"""Backtest engine for strategy validation (T066, T014).

V0.3 Enhancement (T014): Added run_single_stock() for parallel execution.

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
        # Check minimum rows (reduced from 250 to 150 to support shorter backtest periods)
        # Note: Strategy still needs 120 days for indicators, so 150 gives 30 days of actual backtesting
        if len(data) < 150:  # ~6 months minimum
            return False, f"数据不足: {len(data)} 天（至少需要 150 天，建议 250+ 天以获得更准确结果）"

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
                self.logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}...")
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

                    # Log actual data received
                    self.logger.info(
                        f"📊 Retrieved {len(market_data)} rows for {symbol} "
                        f"(requested: {start_date} to {end_date})"
                    )
                    if len(market_data) > 0 and 'timestamp' in market_data.columns:
                        actual_start = market_data['timestamp'].min()
                        actual_end = market_data['timestamp'].max()
                        self.logger.info(f"   Actual date range: {actual_start} to {actual_end}")

                    # Validate data
                    is_valid, error_msg = self.validate_data(market_data, symbol)
                    if not is_valid:
                        # Enhanced error message with date range info
                        raise ValueError(
                            f"Data validation failed for {symbol}: {error_msg}\n"
                            f"  Requested: {start_date} to {end_date}\n"
                            f"  Received: {len(market_data)} rows\n"
                            f"  Source: {data_sources[symbol]}"
                        )

                    # Check if strategy needs multi-timeframe data
                    strategy_class_name = strategy.__class__.__name__
                    if strategy_class_name == 'MultiTimeframeStrategy':
                        # Add weekly data for multi-timeframe strategies
                        self.logger.info(f"📊 Preparing multi-timeframe data for {symbol}...")
                        from investlib_data.resample import resample_to_weekly, align_timeframes

                        weekly_data = resample_to_weekly(market_data)
                        market_data = align_timeframes(market_data, weekly_data)
                        self.logger.info(f"✓ Added weekly indicators to daily data")

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
                            # Check if we already have a position (avoid stacking positions)
                            current_position = portfolio.positions.get(symbol, 0)
                            if current_position > 0:
                                # Skip BUY signal if already holding position
                                self.logger.debug(
                                    f"[BacktestRunner] Skipping BUY signal for {symbol} "
                                    f"(already holding {current_position} shares)"
                                )
                                continue

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

            # Close any open positions at the end of backtest
            # This ensures all trades are paired (BUY has corresponding SELL)
            open_positions = list(portfolio.positions.keys())
            if open_positions:
                final_date = all_dates[-1]
                self.logger.info(
                    f"[BacktestRunner] Closing {len(open_positions)} open position(s) at backtest end"
                )
                for symbol in open_positions:
                    quantity = portfolio.positions[symbol]
                    if quantity > 0:
                        price = final_prices.get(symbol, 0)
                        if price > 0:
                            portfolio.sell(
                                symbol=symbol,
                                quantity=quantity,
                                price=price,
                                timestamp=final_date,
                                data_source='backtest_close'
                            )
                            trades_executed += 1
                            self.logger.info(
                                f"[BacktestRunner] Closed {quantity} {symbol} @ {price:.2f}"
                            )

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

    def run_single_stock(
        self,
        symbol: str,
        data: pd.DataFrame,
        start_date: str,
        end_date: str,
        strategy,
        capital: Optional[float] = None,
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run backtest for a single stock with pre-fetched data (T014).

        This method is designed for parallel execution - it accepts pre-fetched
        market data instead of fetching it internally. No shared state, no API calls.

        Args:
            symbol: Stock symbol
            data: Pre-fetched market data DataFrame (OHLCV + timestamp)
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            strategy: Strategy instance
            capital: Initial capital (default: use self.initial_capital)
            strategy_params: Optional strategy parameters (unused - strategy already initialized)

        Returns:
            Backtest results dictionary for this symbol

        Raises:
            ValueError: If data validation fails
        """
        capital = capital or self.initial_capital

        self.logger.info(
            f"[BacktestRunner] Single-stock backtest: {strategy.__class__.__name__} "
            f"on {symbol} ({len(data)} days)"
        )

        # Validate data
        is_valid, error_msg = self.validate_data(data, symbol)
        if not is_valid:
            raise ValueError(f"Data validation failed for {symbol}: {error_msg}")

        # Initialize portfolio
        portfolio = Portfolio(
            initial_capital=capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate
        )

        # Filter data by date range
        data = data[
            (data['timestamp'] >= start_date) &
            (data['timestamp'] <= end_date)
        ].copy()

        if data.empty:
            raise ValueError(
                f"No data for {symbol} in date range {start_date} to {end_date}"
            )

        # Get all trading dates
        all_dates = sorted(data['timestamp'].unique())

        self.logger.debug(
            f"[BacktestRunner] Single-stock: {symbol} - {len(all_dates)} trading days"
        )

        # Main backtest loop
        trades_executed = 0
        signals_generated = 0

        for i, current_date in enumerate(all_dates):
            # Get current price
            day_data = data[data['timestamp'] == current_date]
            if day_data.empty:
                continue

            current_price = day_data.iloc[0]['close']

            # Get historical data up to current date
            historical_data = data[data['timestamp'] <= current_date]

            # Strategy needs enough data for indicators (e.g., MA120)
            if len(historical_data) < 120:
                continue

            try:
                # Generate signal
                signal = self._generate_signal_from_data(
                    strategy, symbol, historical_data, capital
                )
                signals_generated += 1

                if signal and signal.get('action') in ['BUY', 'STRONG_BUY']:
                    # Calculate position size
                    position_size_pct = signal.get('position_size_pct', 10)
                    position_value = capital * (position_size_pct / 100)
                    quantity = int(position_value / current_price)

                    if quantity > 0:
                        success = portfolio.buy(
                            symbol=symbol,
                            price=current_price,
                            quantity=quantity,
                            timestamp=current_date,
                            data_source='SharedMemory'
                        )
                        if success:
                            trades_executed += 1

                elif signal and signal.get('action') in ['SELL', 'STRONG_SELL']:
                    # Sell entire position if we have one
                    current_position = portfolio.positions.get(symbol, 0)
                    if current_position > 0:
                        success = portfolio.sell(
                            symbol=symbol,
                            price=current_price,
                            quantity=current_position,
                            timestamp=current_date,
                            data_source='SharedMemory'
                        )
                        if success:
                            trades_executed += 1

            except Exception as e:
                self.logger.warning(
                    f"Signal generation failed for {symbol} on {current_date}: {e}"
                )

            # Record daily portfolio value
            portfolio.record_daily_value(current_date, {symbol: current_price})

        # Get final price
        final_price = data.iloc[-1]['close']

        # Get portfolio summary
        summary = portfolio.get_summary({symbol: final_price})

        self.logger.info(
            f"[BacktestRunner] Single-stock complete ({symbol}): "
            f"Final value: {summary['final_value']:.2f} | "
            f"Return: {summary['total_return']*100:.2f}% | "
            f"Trades: {trades_executed}"
        )

        # Return results
        return {
            'strategy_name': strategy.__class__.__name__,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': capital,
            'final_capital': summary['final_value'],
            'total_return': summary['total_return'],
            'total_trades': trades_executed,
            'signals_generated': signals_generated,
            'trade_log': portfolio.get_trade_log(),
            'equity_curve': portfolio.get_equity_curve(),
            'data_source': 'SharedMemory',
            'backtest_completed_at': datetime.now().isoformat()
        }

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
