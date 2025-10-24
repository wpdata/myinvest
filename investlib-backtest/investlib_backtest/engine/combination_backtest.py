"""
Combination Strategy Backtest Engine (T054)

Backtest multi-leg option/futures combinations with proper handling
of all legs together.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class CombinationBacktestEngine:
    """Backtest engine for multi-leg combination strategies.

    Handles:
    - Entry/exit of all legs simultaneously
    - Greeks tracking across all legs
    - Margin requirements with hedge reductions
    - Option expiry for multi-leg positions
    - P&L calculation considering all legs
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003
    ):
        """Initialize combination backtest engine.

        Args:
            initial_capital: Starting capital
            commission_rate: Commission rate per transaction
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        combination_strategy,
        market_data: pd.DataFrame,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Run backtest for a combination strategy.

        Args:
            combination_strategy: CombinationStrategy object with legs
            market_data: Price history DataFrame
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            Dict with backtest results:
                - trades: List of trade events
                - equity_curve: Portfolio value over time
                - greeks_history: Greeks tracking
                - final_pnl: Final profit/loss
                - sharpe_ratio: Risk-adjusted return
                - max_drawdown: Maximum drawdown
                - total_margin: Total margin used
        """
        self.logger.info(
            f"Starting combination backtest: {combination_strategy.strategy_name}"
        )

        # Filter market data by date range
        market_data = market_data[
            (market_data['timestamp'] >= start_date) &
            (market_data['timestamp'] <= end_date)
        ].copy()

        if market_data.empty:
            self.logger.warning("No market data in specified date range")
            return self._empty_result()

        # Initialize tracking
        capital = self.initial_capital
        position = None  # Active combination position
        trades = []
        equity_curve = []
        greeks_history = []

        # Entry signal - enter at first bar
        entry_date = market_data.iloc[0]['timestamp']
        entry_prices = self._get_entry_prices(combination_strategy, market_data.iloc[0])

        # Calculate entry cost and margin
        from investlib_margin.combination_margin import calculate_combination_margin

        legs_with_prices = self._enrich_legs_with_prices(
            combination_strategy.legs,
            entry_prices
        )

        margin_result = calculate_combination_margin(legs_with_prices)
        total_margin = margin_result['total_margin']

        if total_margin > capital:
            self.logger.error(
                f"Insufficient capital: Need ¥{total_margin:,.0f}, "
                f"Have ¥{capital:,.0f}"
            )
            return self._empty_result()

        # Enter position
        capital -= total_margin
        position = {
            'entry_date': entry_date,
            'legs': combination_strategy.legs,
            'entry_prices': entry_prices,
            'margin': total_margin,
            'net_cost': combination_strategy.net_cost
        }

        trades.append({
            'date': entry_date,
            'action': 'ENTER_COMBINATION',
            'strategy': combination_strategy.strategy_name,
            'legs_count': len(combination_strategy.legs),
            'margin': total_margin
        })

        self.logger.info(
            f"Entered combination at {entry_date}: "
            f"{len(combination_strategy.legs)} legs, Margin=¥{total_margin:,.0f}"
        )

        # Iterate through market data
        for i in range(len(market_data)):
            current_row = market_data.iloc[i]
            current_date = current_row['timestamp']

            # Calculate current P&L
            if position:
                pnl = self._calculate_combination_pnl(
                    position,
                    current_row
                )

                # Calculate Greeks if options exist
                greeks = self._calculate_combination_greeks(
                    position,
                    current_row
                )

                greeks_history.append({
                    'date': current_date,
                    **greeks
                })

                # Check expiry for option legs
                expired = self._check_expiry(position, current_date)

                if expired:
                    # Close position due to expiry
                    capital += total_margin + pnl

                    trades.append({
                        'date': current_date,
                        'action': 'EXPIRY_CLOSE',
                        'pnl': pnl
                    })

                    self.logger.info(
                        f"Position expired at {current_date}, P&L=¥{pnl:,.2f}"
                    )

                    position = None

            # Track equity
            if position:
                unrealized_pnl = self._calculate_combination_pnl(position, current_row)
                total_equity = capital + total_margin + unrealized_pnl
            else:
                total_equity = capital

            equity_curve.append({
                'date': current_date,
                'equity': total_equity,
                'cash': capital,
                'unrealized_pnl': unrealized_pnl if position else 0
            })

        # Final metrics
        equity_df = pd.DataFrame(equity_curve)
        final_equity = equity_df.iloc[-1]['equity']
        final_pnl = final_equity - self.initial_capital

        returns = equity_df['equity'].pct_change().dropna()
        sharpe_ratio = self._calculate_sharpe(returns)
        max_drawdown = self._calculate_max_drawdown(equity_df['equity'])

        result = {
            'strategy_type': 'combination',
            'strategy_name': combination_strategy.strategy_name,
            'legs_count': len(combination_strategy.legs),
            'trades': trades,
            'equity_curve': equity_curve,
            'greeks_history': greeks_history,
            'final_equity': final_equity,
            'final_pnl': final_pnl,
            'return_pct': (final_pnl / self.initial_capital) * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_margin': total_margin,
            'margin_utilization_pct': (total_margin / self.initial_capital) * 100
        }

        self.logger.info(
            f"Backtest complete: P&L=¥{final_pnl:,.2f} ({result['return_pct']:.2f}%), "
            f"Sharpe={sharpe_ratio:.2f}, MaxDD={max_drawdown:.2f}%"
        )

        return result

    def _get_entry_prices(self, strategy, market_row) -> Dict[str, float]:
        """Get entry prices for all legs."""
        prices = {}
        for leg in strategy.legs:
            # Use entry_price from leg definition
            prices[leg.leg_id] = leg.entry_price
        return prices

    def _enrich_legs_with_prices(self, legs: List, prices: Dict) -> List[Dict]:
        """Convert Leg objects to dicts with prices."""
        result = []
        for leg in legs:
            result.append({
                'symbol': leg.symbol,
                'asset_type': leg.asset_type,
                'action': leg.action,
                'quantity': leg.quantity,
                'entry_price': prices.get(leg.leg_id, leg.entry_price),
                'multiplier': leg.multiplier,
                'strike_price': leg.strike_price
            })
        return result

    def _calculate_combination_pnl(
        self,
        position: Dict,
        market_row: pd.Series
    ) -> float:
        """Calculate total P&L for combination at current price."""
        from investlib_quant.strategies.pnl_chart import calculate_leg_pnl_at_price

        # Get current underlying price from market data
        underlying_price = market_row.get('close', 0)

        total_pnl = 0.0
        for leg in position['legs']:
            leg_dict = {
                'asset_type': leg.asset_type,
                'action': leg.action,
                'quantity': leg.quantity,
                'entry_price': leg.entry_price,
                'strike_price': leg.strike_price,
                'multiplier': leg.multiplier
            }
            leg_pnl = calculate_leg_pnl_at_price(leg_dict, underlying_price)
            total_pnl += leg_pnl

        return total_pnl

    def _calculate_combination_greeks(
        self,
        position: Dict,
        market_row: pd.Series
    ) -> Dict[str, float]:
        """Calculate aggregate Greeks for combination."""
        try:
            from investlib_greeks.aggregator import aggregate_position_greeks

            # Build option positions for Greeks calculation
            option_positions = []
            for leg in position['legs']:
                if leg.asset_type in ['call', 'put']:
                    option_positions.append({
                        'option_type': leg.asset_type,
                        'direction': leg.direction,
                        'quantity': leg.quantity,
                        'greeks': leg.greeks if hasattr(leg, 'greeks') else {}
                    })

            if option_positions:
                return aggregate_position_greeks(option_positions)
            else:
                return {'total_delta': 0, 'total_gamma': 0, 'total_vega': 0,
                       'total_theta': 0, 'total_rho': 0}
        except Exception as e:
            self.logger.warning(f"Greeks calculation failed: {e}")
            return {'total_delta': 0, 'total_gamma': 0, 'total_vega': 0,
                   'total_theta': 0, 'total_rho': 0}

    def _check_expiry(self, position: Dict, current_date) -> bool:
        """Check if any option leg has expired."""
        for leg in position['legs']:
            if leg.asset_type in ['call', 'put']:
                if leg.expiry_date:
                    expiry = pd.to_datetime(leg.expiry_date)
                    if pd.to_datetime(current_date) >= expiry:
                        return True
        return False

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """Calculate annualized Sharpe ratio."""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        return (returns.mean() / returns.std()) * np.sqrt(252)

    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """Calculate maximum drawdown percentage."""
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100
        return abs(drawdown.min())

    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'strategy_type': 'combination',
            'trades': [],
            'equity_curve': [],
            'greeks_history': [],
            'final_equity': self.initial_capital,
            'final_pnl': 0.0,
            'return_pct': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'total_margin': 0.0
        }


# Example usage
if __name__ == '__main__':
    from investlib_quant.strategies.combination_models import StrategyTemplates

    # Create covered call strategy
    strategy = StrategyTemplates.covered_call(
        stock_symbol="600519.SH",
        stock_price=1800,
        strike_price=1900,
        call_premium=50,
        expiry_date="2025-03-21",
        quantity=100
    )

    # Create sample market data
    dates = pd.date_range(start='2025-01-01', end='2025-03-21', freq='D')
    market_data = pd.DataFrame({
        'timestamp': dates,
        'symbol': '600519.SH',
        'close': np.linspace(1800, 1850, len(dates)) + np.random.normal(0, 20, len(dates))
    })

    # Run backtest
    engine = CombinationBacktestEngine(initial_capital=200000)
    result = engine.run(
        combination_strategy=strategy,
        market_data=market_data,
        start_date='2025-01-01',
        end_date='2025-03-21'
    )

    print("=" * 60)
    print(f"组合策略回测结果: {result['strategy_name']}")
    print("=" * 60)
    print(f"策略腿数: {result['legs_count']}")
    print(f"最终权益: ¥{result['final_equity']:,.2f}")
    print(f"盈亏: ¥{result['final_pnl']:,.2f} ({result['return_pct']:.2f}%)")
    print(f"夏普比率: {result['sharpe_ratio']:.2f}")
    print(f"最大回撤: {result['max_drawdown']:.2f}%")
    print(f"保证金占用: ¥{result['total_margin']:,.2f} ({result['margin_utilization_pct']:.1f}%)")
    print(f"交易次数: {len(result['trades'])}")
