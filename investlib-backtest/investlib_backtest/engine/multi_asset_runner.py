"""Multi-Asset Backtest Runner (T037, T038).

Extends BacktestRunner with:
- Futures and options support
- Automatic forced liquidation checking
- Margin management
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from investlib_backtest.engine.multi_asset_portfolio import MultiAssetPortfolio


class MultiAssetBacktestRunner:
    """Backtest runner for stocks, futures, and options."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001,
        force_close_margin_rate: float = 0.03
    ):
        """Initialize multi-asset backtest runner.

        Args:
            initial_capital: Starting capital
            commission_rate: Commission as decimal (default 0.03%)
            slippage_rate: Slippage as decimal (default 0.1%)
            force_close_margin_rate: Margin rate for forced liquidation (default 3%)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.force_close_margin_rate = force_close_margin_rate
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        strategy,
        symbols: List[str],
        start_date: str,
        end_date: str,
        capital: Optional[float] = None,
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run multi-asset backtest.

        Args:
            strategy: Strategy instance
            symbols: List of symbols (stocks, futures, options)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            capital: Initial capital
            strategy_params: Strategy parameters

        Returns:
            Backtest results dictionary
        """
        capital = capital or self.initial_capital
        strategy_params = strategy_params or {}

        self.logger.info(
            f"[MultiAssetBacktest] Starting: {strategy.__class__.__name__} "
            f"on {symbols} from {start_date} to {end_date}"
        )

        # Initialize multi-asset portfolio
        portfolio = MultiAssetPortfolio(
            initial_capital=capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate,
            force_close_margin_rate=self.force_close_margin_rate
        )

        # Fetch historical data for all symbols
        from investlib_data.market_api import MarketDataFetcher
        from investlib_data.cache_manager import CacheManager
        from investlib_data.database import SessionLocal
        from investlib_data.multi_asset_api import detect_asset_type

        session = None
        try:
            session = SessionLocal()
            cache_manager = CacheManager(session=session)
        except Exception as e:
            self.logger.warning(f"Cache not available: {e}")
            cache_manager = None

        fetcher = MarketDataFetcher(cache_manager=cache_manager)

        try:
            # Fetch and categorize data by asset type
            all_data: Dict[str, pd.DataFrame] = {}
            asset_types: Dict[str, str] = {}
            data_sources: Dict[str, str] = {}

            for symbol in symbols:
                self.logger.info(f"Fetching {symbol}...")
                try:
                    # Detect asset type
                    asset_type = detect_asset_type(symbol)
                    asset_types[symbol] = asset_type

                    # Fetch data
                    result = fetcher.fetch_with_fallback(
                        symbol,
                        start_date,
                        end_date,
                        prefer_cache=True
                    )
                    market_data = result['data']
                    data_sources[symbol] = result['metadata']['api_source']

                    self.logger.info(
                        f"✓ Loaded {len(market_data)} days for {symbol} ({asset_type}) "
                        f"from {data_sources[symbol]}"
                    )

                    all_data[symbol] = market_data

                except Exception as e:
                    self.logger.error(f"Failed to fetch {symbol}: {e}")
                    raise

            # Get all unique trading dates
            all_dates = sorted(set(
                date for df in all_data.values()
                for date in df['timestamp'].unique()
            ))

            self.logger.info(f"Backtesting across {len(all_dates)} trading days...")

            # Main backtest loop
            trades_executed = 0
            signals_generated = 0
            forced_liquidations = 0

            for i, current_date in enumerate(all_dates):
                # Get current prices
                current_prices = {}
                for symbol, df in all_data.items():
                    day_data = df[df['timestamp'] == current_date]
                    if not day_data.empty:
                        current_prices[symbol] = day_data.iloc[0]['close']

                # CRITICAL: Check forced liquidations BEFORE generating signals (T038)
                liquidated_count = portfolio.check_forced_liquidation(
                    current_prices=current_prices,
                    timestamp=current_date,
                    data_source='forced_liquidation'
                )
                forced_liquidations += liquidated_count

                # Check option expiry (T039)
                expired_count = portfolio.check_option_expiry(
                    current_date=current_date,
                    current_prices=current_prices,
                    data_source='option_expiry'
                )
                if expired_count > 0:
                    self.logger.info(
                        f"[MultiAssetBacktest] {expired_count} options expired on {current_date}"
                    )

                # Generate signals for each symbol
                for symbol in symbols:
                    if symbol not in current_prices:
                        continue

                    # Get historical data up to current date
                    historical_data = all_data[symbol][
                        all_data[symbol]['timestamp'] <= current_date
                    ]

                    # Need enough data for indicators
                    if len(historical_data) < 120:
                        continue

                    try:
                        # Generate signal
                        signal = self._generate_signal_from_data(
                            strategy, symbol, historical_data, capital
                        )
                        signals_generated += 1

                        if not signal:
                            continue

                        action = signal.get('action')
                        asset_type = asset_types[symbol]

                        if action in ['BUY', 'STRONG_BUY']:
                            # Calculate position size
                            position_size_pct = signal.get('position_size_pct', 10)
                            position_value = capital * (position_size_pct / 100)
                            price = current_prices[symbol]

                            # Asset-specific buy logic
                            if asset_type == 'stock':
                                quantity = int(position_value / price)
                                if quantity > 0:
                                    success = portfolio.buy(
                                        symbol=symbol,
                                        price=price,
                                        quantity=quantity,
                                        timestamp=current_date,
                                        asset_type='stock',
                                        data_source=data_sources[symbol]
                                    )
                                    if success:
                                        trades_executed += 1

                            elif asset_type == 'futures':
                                # Futures: calculate based on margin
                                margin_rate = 0.15  # 15% margin
                                multiplier = 300 if symbol.startswith('IF') or symbol.startswith('IC') else 100
                                # How many contracts can we afford?
                                margin_per_contract = price * multiplier * margin_rate
                                max_contracts = int(position_value / margin_per_contract)
                                quantity = max(1, max_contracts)

                                success = portfolio.buy(
                                    symbol=symbol,
                                    price=price,
                                    quantity=quantity,
                                    timestamp=current_date,
                                    asset_type='futures',
                                    data_source=data_sources[symbol],
                                    margin_rate=margin_rate
                                )
                                if success:
                                    trades_executed += 1

                            elif asset_type == 'option':
                                # Options: calculate Greeks if available
                                greeks = signal.get('greeks', {})
                                multiplier = 10000
                                # How many contracts?
                                premium_per_contract = price * multiplier
                                max_contracts = int(position_value / premium_per_contract)
                                quantity = max(1, max_contracts)

                                # Get option details from signal
                                expiry_date = signal.get('expiry_date')
                                strike_price = signal.get('strike_price', price)
                                option_type = signal.get('option_type', 'call')

                                success = portfolio.buy(
                                    symbol=symbol,
                                    price=price,
                                    quantity=quantity,
                                    timestamp=current_date,
                                    asset_type='option',
                                    data_source=data_sources[symbol],
                                    greeks=greeks,
                                    expiry_date=expiry_date,
                                    strike_price=strike_price,
                                    option_type=option_type
                                )
                                if success:
                                    trades_executed += 1

                        elif action in ['SELL', 'STRONG_SELL']:
                            # Sell entire position if we have one
                            if symbol in portfolio.positions:
                                position = portfolio.positions[symbol]
                                quantity = position['quantity']
                                price = current_prices[symbol]

                                success = portfolio.sell(
                                    symbol=symbol,
                                    price=price,
                                    quantity=quantity,
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
                        f"Progress: {progress:.1f}% ({i+1}/{len(all_dates)}) | "
                        f"Trades: {trades_executed} | Forced liquidations: {forced_liquidations}"
                    )

            # Get final prices
            final_prices = {}
            for symbol, df in all_data.items():
                final_prices[symbol] = df.iloc[-1]['close']

            # Get portfolio summary
            summary = portfolio.get_summary(final_prices)

            self.logger.info(
                f"[MultiAssetBacktest] Complete: "
                f"Final value: {summary['final_value']:.2f} | "
                f"Return: {summary['total_return']*100:.2f}% | "
                f"Trades: {trades_executed} | "
                f"Forced liquidations: {forced_liquidations}"
            )

            # Return results
            return {
                'strategy_name': strategy.__class__.__name__,
                'symbols': symbols,
                'asset_types': asset_types,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': capital,
                'final_capital': summary['final_value'],
                'total_return': summary['total_return'],
                'total_trades': trades_executed,
                'signals_generated': signals_generated,
                'forced_liquidations': forced_liquidations,
                'trade_log': portfolio.get_trade_log(),
                'equity_curve': portfolio.get_equity_curve(),
                'data_sources': data_sources,
                'margin_stats': {
                    'margin_used': summary['margin_used'],
                    'margin_available': summary['margin_available']
                },
                'backtest_completed_at': datetime.now().isoformat()
            }

        finally:
            if session:
                session.close()
                self.logger.debug("Database session closed")

    def _generate_signal_from_data(
        self,
        strategy,
        symbol: str,
        historical_data: pd.DataFrame,
        capital: float
    ) -> Optional[Dict[str, Any]]:
        """Generate signal from historical data."""
        metadata = {
            'api_source': 'Backtest (pre-fetched)',
            'retrieval_timestamp': datetime.now(),
            'data_freshness': 'historical'
        }

        # Use analyze_data() method
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

        # Fallback
        try:
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
