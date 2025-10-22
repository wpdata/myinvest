"""Backtest engine for strategy validation (T066).

Runs strategies on historical market data (3+ years) to validate performance.
Uses real Tushare/AKShare data with transaction cost simulation.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from investlib_backtest.engine.portfolio import Portfolio


class BacktestRunner:
    """Main backtest execution engine."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001
    ):
        """Initialize backtest runner.

        Args:
            initial_capital: Starting capital
            commission_rate: Commission as decimal (default 0.03%)
            slippage_rate: Slippage as decimal (default 0.1%)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.logger = logging.getLogger(__name__)

    def validate_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        max_gap_days: int = 15
    ) -> tuple[bool, Optional[str]]:
        """Validate data quality before backtest (FR-140).

        Args:
            data: Market data DataFrame
            symbol: Stock symbol
            max_gap_days: Maximum allowed gap in trading days (default 15 for Chinese holidays)

        Returns:
            (is_valid, error_message)
        """
        # Check minimum rows
        if len(data) < 250:  # ~1 year minimum
            return False, f"数据不足: {len(data)} 天（至少需要 250 天）"

        # Check required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            return False, f"缺少列: {missing_cols}"

        # Check for gaps in trading days
        if 'timestamp' in data.columns:
            data = data.sort_values('timestamp')
            dates = pd.to_datetime(data['timestamp'])
            gaps = dates.diff().dt.days

            # Find gaps > max_gap_days (accounting for weekends and holidays)
            large_gaps = gaps[gaps > max_gap_days]
            if len(large_gaps) > 0:
                gap_dates = dates[gaps > max_gap_days].tolist()
                # Log warning but don't fail (Chinese market has long holidays)
                self.logger.warning(
                    f"⚠️ {symbol} 数据缺口检测: {len(large_gaps)} 个缺口 > {max_gap_days} 天. "
                    f"首个缺口在: {gap_dates[0]}. 可能是停牌或长假期。"
                )
                # Only fail if there are extreme gaps (> 30 days, likely data issue)
                extreme_gaps = gaps[gaps > 30]
                if len(extreme_gaps) > 5:
                    return False, (
                        f"严重数据缺口: {len(extreme_gaps)} 个缺口 > 30 天，可能数据有问题"
                    )

        self.logger.info(f"✓ {symbol} 数据验证通过: {len(data)} 个交易日")
        return True, None

    def run(
        self,
        strategy,
        symbols: List[str],
        start_date: str,
        end_date: str,
        capital: Optional[float] = None,
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run backtest for a strategy on historical data (FR-116 to FR-120).

        Args:
            strategy: Strategy instance (Livermore/Kroll/Fusion)
            symbols: List of stock symbols to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            capital: Initial capital (default: use self.initial_capital)
            strategy_params: Optional strategy parameters

        Returns:
            Backtest results dictionary

        Raises:
            ValueError: If data validation fails
        """
        capital = capital or self.initial_capital
        strategy_params = strategy_params or {}

        self.logger.info(
            f"[BacktestRunner] Starting backtest: {strategy.__class__.__name__} "
            f"on {symbols} from {start_date} to {end_date}"
        )

        # Initialize portfolio
        portfolio = Portfolio(
            initial_capital=capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate
        )

        # Fetch and validate historical data for all symbols
        from investlib_data.market_api import MarketDataFetcher
        from investlib_data.cache_manager import CacheManager
        from investlib_data.database import SessionLocal

        session = None
        try:
            session = SessionLocal()
            cache_manager = CacheManager(session=session)
        except Exception as e:
            self.logger.warning(f"Cache not available: {e}")
            cache_manager = None

        fetcher = MarketDataFetcher(cache_manager=cache_manager)

        try:
            # Store data for all symbols
            all_data: Dict[str, pd.DataFrame] = {}
            data_sources: Dict[str, str] = {}

            for symbol in symbols:
                self.logger.info(f"Fetching historical data for {symbol}...")
                try:
                    # CRITICAL: Use prefer_cache=True to avoid API rate limits during backtesting
                    # This will try cache first, only calling APIs if cache misses
                    result = fetcher.fetch_with_fallback(
                        symbol,
                        start_date,
                        end_date,
                        prefer_cache=True  # Backtest mode: cache-first strategy
                    )
                    market_data = result['data']
                    data_sources[symbol] = result['metadata']['api_source']

                    # Validate data
                    is_valid, error_msg = self.validate_data(market_data, symbol)
                    if not is_valid:
                        raise ValueError(f"Data validation failed for {symbol}: {error_msg}")

                    all_data[symbol] = market_data
                    self.logger.info(
                        f"✓ Loaded {len(market_data)} days of data for {symbol} "
                        f"from {data_sources[symbol]}"
                    )

                except Exception as e:
                    self.logger.error(f"Failed to fetch data for {symbol}: {e}")
                    raise

            # Get all unique trading dates (union of all symbols)
            all_dates = sorted(set(
                date for df in all_data.values()
                for date in df['timestamp'].unique()
            ))

            self.logger.info(f"Backtesting across {len(all_dates)} trading days...")

            # Main backtest loop
            trades_executed = 0
            signals_generated = 0

            for i, current_date in enumerate(all_dates):
                # Get current prices for all symbols on this date
                current_prices = {}
                for symbol, df in all_data.items():
                    day_data = df[df['timestamp'] == current_date]
                    if not day_data.empty:
                        current_prices[symbol] = day_data.iloc[0]['close']

                # For each symbol, generate signal and execute trades
                for symbol in symbols:
                    if symbol not in current_prices:
                        continue  # No data for this symbol on this date

                    # Get historical data up to current date for strategy analysis
                    historical_data = all_data[symbol][
                        all_data[symbol]['timestamp'] <= current_date
                    ]

                    # Strategy needs enough data for indicators (e.g., MA120)
                    if len(historical_data) < 120:
                        continue

                    try:
                        # Generate signal using strategy
                        # Note: We pass historical data directly for efficiency
                        # Strategy should analyze this data and return signal
                        signal = self._generate_signal_from_data(
                            strategy, symbol, historical_data, capital
                        )
                        signals_generated += 1

                        if signal and signal.get('action') in ['BUY', 'STRONG_BUY']:
                            # Calculate position size
                            position_size_pct = signal.get('position_size_pct', 10)
                            position_value = capital * (position_size_pct / 100)
                            price = current_prices[symbol]
                            quantity = int(position_value / price)

                            if quantity > 0:
                                success = portfolio.buy(
                                    symbol=symbol,
                                    price=price,
                                    quantity=quantity,
                                    timestamp=current_date,
                                    data_source=data_sources[symbol]
                                )
                                if success:
                                    trades_executed += 1

                        elif signal and signal.get('action') in ['SELL', 'STRONG_SELL']:
                            # Sell entire position if we have one
                            current_position = portfolio.positions.get(symbol, 0)
                            if current_position > 0:
                                price = current_prices[symbol]
                                success = portfolio.sell(
                                    symbol=symbol,
                                    price=price,
                                    quantity=current_position,
                                    timestamp=current_date,
                                    data_source=data_sources[symbol]
                                )
                                if success:
                                    trades_executed += 1

                    except Exception as e:
                        self.logger.warning(
                            f"Signal generation failed for {symbol} on {current_date}: {e}"
                        )

                # Record daily portfolio value
                portfolio.record_daily_value(current_date, current_prices)

                # Progress logging
                if (i + 1) % 50 == 0:
                    progress = (i + 1) / len(all_dates) * 100
                    self.logger.info(
                        f"Progress: {progress:.1f}% ({i+1}/{len(all_dates)} days) | "
                        f"Trades: {trades_executed} | Signals: {signals_generated}"
                    )

            # Get final prices for portfolio valuation
            final_prices = {}
            for symbol, df in all_data.items():
                final_prices[symbol] = df.iloc[-1]['close']

            # Get portfolio summary
            summary = portfolio.get_summary(final_prices)

            self.logger.info(
                f"[BacktestRunner] Backtest complete: "
                f"Final value: {summary['final_value']:.2f} | "
                f"Return: {summary['total_return']*100:.2f}% | "
                f"Trades: {trades_executed}"
            )

            # Return complete results
            return {
                'strategy_name': strategy.__class__.__name__,
                'symbols': symbols,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': capital,
                'final_capital': summary['final_value'],
                'total_return': summary['total_return'],
                'total_trades': trades_executed,
                'signals_generated': signals_generated,
                'trade_log': portfolio.get_trade_log(),
                'equity_curve': portfolio.get_equity_curve(),
                'data_sources': data_sources,
                'backtest_completed_at': datetime.now().isoformat()
            }
        finally:
            # CRITICAL: Close database session to prevent connection leaks
            if session:
                session.close()
                self.logger.debug("[BacktestRunner] Database session closed")

    def _generate_signal_from_data(
        self,
        strategy,
        symbol: str,
        historical_data: pd.DataFrame,
        capital: float
    ) -> Optional[Dict[str, Any]]:
        """Generate signal from historical data snapshot.

        This method uses strategy.analyze_data() to avoid re-fetching data.
        This is critical for backtest performance - without it, we'd make
        hundreds or thousands of redundant API calls.
        """
        # Create metadata for data provenance
        metadata = {
            'api_source': 'Backtest (pre-fetched)',
            'retrieval_timestamp': datetime.now(),
            'data_freshness': 'historical'
        }

        # Use analyze_data() method (all strategies should have this now)
        if hasattr(strategy, 'analyze_data'):
            try:
                return strategy.analyze_data(
                    market_data=historical_data,
                    symbol=symbol,
                    capital=capital,
                    metadata=metadata
                )
            except Exception as e:
                self.logger.debug(f"Signal generation error for {symbol}: {e}")
                return None

        # Fallback: This should not happen with refactored strategies
        # Log a warning if we hit this path
        self.logger.warning(
            f"Strategy {strategy.__class__.__name__} missing analyze_data() method. "
            f"This will cause redundant API calls. Please refactor strategy to add analyze_data()."
        )

        try:
            # This will cause API re-fetch - performance will be poor
            return strategy.analyze(
                symbol=symbol,
                start_date=None,
                end_date=None,
                capital=capital,
                use_cache=True
            )
        except Exception as e:
            self.logger.debug(f"Signal generation error: {e}")
            return None
