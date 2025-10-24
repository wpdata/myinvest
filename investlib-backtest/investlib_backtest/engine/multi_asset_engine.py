"""
Multi-Asset Backtest Engine (T037)

支持股票、期货、期权的统一回测引擎。
根据策略类型自动路由到对应的引擎。
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, timedelta
from investlib_backtest.engine.portfolio import Portfolio


class MultiAssetBacktestEngine:
    """多资产回测引擎 (T037).

    功能：
    - 自动检测策略类型（Stock/Futures/Options）
    - 路由到对应的专用引擎
    - 统一的结果格式
    - 支持混合策略组合
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001
    ):
        """初始化多资产回测引擎。

        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage_rate: 滑点率
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.logger = logging.getLogger(__name__)

        # Initialize specialized engines
        self.stock_engine = StockBacktestEngine(
            initial_capital, commission_rate, slippage_rate
        )
        self.futures_engine = FuturesBacktestEngine(
            initial_capital, commission_rate, slippage_rate
        )
        self.options_engine = OptionsBacktestEngine(
            initial_capital, commission_rate, slippage_rate
        )

    def detect_strategy_type(self, strategy) -> Literal['stock', 'futures', 'option']:
        """检测策略类型（使用 isinstance 检查）。

        Args:
            strategy: 策略实例

        Returns:
            'stock' | 'futures' | 'option'
        """
        # Import strategy classes
        from investlib_quant.strategies.base import (
            StockStrategy, FuturesStrategy, OptionsStrategy
        )

        if isinstance(strategy, FuturesStrategy):
            return 'futures'
        elif isinstance(strategy, OptionsStrategy):
            return 'option'
        elif isinstance(strategy, StockStrategy):
            return 'stock'
        else:
            # Fallback: check asset_type attribute
            asset_type = getattr(strategy, 'asset_type', 'stock')
            return asset_type

    def run(
        self,
        strategy,
        symbol: str,
        start_date: str,
        end_date: str,
        capital: Optional[float] = None
    ) -> Dict[str, Any]:
        """运行多资产回测。

        Args:
            strategy: 策略实例
            symbol: 交易标的
            start_date: 开始日期
            end_date: 结束日期
            capital: 初始资金

        Returns:
            回测结果字典
        """
        capital = capital or self.initial_capital

        # Detect strategy type
        strategy_type = self.detect_strategy_type(strategy)
        self.logger.info(f"[MultiAssetEngine] Detected strategy type: {strategy_type}")

        # Route to appropriate engine
        if strategy_type == 'stock':
            return self.stock_engine.run(strategy, symbol, start_date, end_date, capital)
        elif strategy_type == 'futures':
            return self.futures_engine.run(strategy, symbol, start_date, end_date, capital)
        elif strategy_type == 'option':
            return self.options_engine.run(strategy, symbol, start_date, end_date, capital)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")


class StockBacktestEngine:
    """股票回测引擎 (T037).

    特点：
    - T+1交易规则
    - 全额资金购买
    - 仅做多
    """

    def __init__(
        self,
        initial_capital: float,
        commission_rate: float,
        slippage_rate: float
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        strategy,
        symbol: str,
        start_date: str,
        end_date: str,
        capital: float
    ) -> Dict[str, Any]:
        """运行股票回测。"""
        self.logger.info(f"[StockEngine] Running stock backtest for {symbol}")

        # Fetch market data
        from investlib_data.market_api import MarketDataFetcher
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_with_fallback(symbol, start_date, end_date, prefer_cache=True)
        market_data = result['data']

        # Initialize portfolio
        portfolio = Portfolio(capital, self.commission_rate, self.slippage_rate)

        # T+1 tracking
        pending_buy_orders = []  # Orders executed today, available tomorrow

        trades = []
        equity_curve = []

        for i in range(len(market_data)):
            current_date = market_data.iloc[i]['timestamp']
            current_price = market_data.iloc[i]['close']

            # Process pending buy orders (T+1: available next day)
            pending_buy_orders = [
                order for order in pending_buy_orders
                if order['date'] < current_date
            ]

            # Get historical data up to current date
            historical_data = market_data.iloc[:i+1]

            # Generate signal
            signal = strategy.generate_signal(historical_data)

            if signal and signal.get('action') == 'BUY':
                # Execute buy order
                position_size_pct = signal.get('position_size_pct', 1.0)
                allocated_capital = capital * position_size_pct
                quantity = int(allocated_capital / current_price)
                quantity = (quantity // 100) * 100  # Round to 100 shares

                if quantity > 0:
                    cost = quantity * current_price * (1 + self.commission_rate + self.slippage_rate)
                    if cost <= capital:
                        capital -= cost
                        pending_buy_orders.append({
                            'date': current_date,
                            'symbol': symbol,
                            'quantity': quantity,
                            'price': current_price
                        })
                        trades.append({
                            'date': current_date,
                            'action': 'BUY',
                            'price': current_price,
                            'quantity': quantity,
                            'cost': cost
                        })

            # Track equity
            position_value = sum(order['quantity'] * current_price for order in pending_buy_orders)
            total_equity = capital + position_value
            equity_curve.append({
                'date': current_date,
                'equity': total_equity,
                'cash': capital,
                'position_value': position_value
            })

        return {
            'strategy_type': 'stock',
            'symbol': symbol,
            'trades': trades,
            'equity_curve': equity_curve,
            'final_equity': equity_curve[-1]['equity'] if equity_curve else capital,
            'return_pct': ((equity_curve[-1]['equity'] - self.initial_capital) / self.initial_capital * 100) if equity_curve else 0
        }


class FuturesBacktestEngine:
    """期货回测引擎 (T037).

    特点：
    - T+0交易规则
    - 保证金交易
    - 双向交易
    - 强制平仓检测
    """

    def __init__(
        self,
        initial_capital: float,
        commission_rate: float,
        slippage_rate: float
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        strategy,
        symbol: str,
        start_date: str,
        end_date: str,
        capital: float
    ) -> Dict[str, Any]:
        """运行期货回测（支持做多/做空 + 强制平仓）。"""
        self.logger.info(f"[FuturesEngine] Running futures backtest for {symbol}")

        # Fetch market data
        from investlib_data.market_api import MarketDataFetcher
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_with_fallback(symbol, start_date, end_date, prefer_cache=True)
        market_data = result['data']

        # Futures position tracking
        position = None  # {direction, contracts, entry_price, liquidation_price}
        trades = []
        equity_curve = []
        liquidation_events = []

        for i in range(len(market_data)):
            current_date = market_data.iloc[i]['timestamp']
            current_price = market_data.iloc[i]['close']

            # Check forced liquidation
            if position:
                is_liquidated = self._check_forced_liquidation(
                    position, current_price
                )

                if is_liquidated:
                    # Forced liquidation
                    self.logger.warning(f"⚠️ Forced liquidation triggered at {current_price}")
                    pnl = self._calculate_futures_pnl(position, current_price, strategy)
                    capital += pnl

                    liquidation_events.append({
                        'date': current_date,
                        'price': current_price,
                        'direction': position['direction'],
                        'pnl': pnl
                    })

                    trades.append({
                        'date': current_date,
                        'action': 'FORCED_LIQUIDATION',
                        'price': current_price,
                        'pnl': pnl
                    })

                    position = None

            # Get historical data
            historical_data = market_data.iloc[:i+1]

            # Generate signal
            signal = strategy.generate_signal(historical_data)

            if signal:
                action = signal.get('action')
                direction = signal.get('direction', 'long')

                # Close existing position if direction changes
                if position and position['direction'] != direction:
                    pnl = self._calculate_futures_pnl(position, current_price, strategy)
                    capital += pnl
                    trades.append({
                        'date': current_date,
                        'action': 'CLOSE',
                        'price': current_price,
                        'pnl': pnl
                    })
                    position = None

                # Open new position
                if not position and action in ['BUY', 'SELL']:
                    contracts = strategy.calculate_position_size(
                        capital=capital,
                        entry_price=current_price,
                        position_size_pct=signal.get('position_size_pct', 0.5),
                        direction=direction
                    )

                    if contracts > 0:
                        liquidation_price = signal.get('liquidation_price') or strategy.calculate_liquidation_price(
                            entry_price=current_price,
                            direction=direction,
                            force_close_margin_rate=0.10
                        )

                        position = {
                            'direction': direction,
                            'contracts': contracts,
                            'entry_price': current_price,
                            'liquidation_price': liquidation_price
                        }

                        trades.append({
                            'date': current_date,
                            'action': 'OPEN',
                            'direction': direction,
                            'price': current_price,
                            'contracts': contracts
                        })

            # Track equity
            position_pnl = 0
            if position:
                position_pnl = self._calculate_futures_pnl(position, current_price, strategy)

            total_equity = capital + position_pnl
            equity_curve.append({
                'date': current_date,
                'equity': total_equity,
                'cash': capital,
                'unrealized_pnl': position_pnl
            })

        return {
            'strategy_type': 'futures',
            'symbol': symbol,
            'trades': trades,
            'equity_curve': equity_curve,
            'liquidation_events': liquidation_events,
            'final_equity': equity_curve[-1]['equity'] if equity_curve else capital,
            'return_pct': ((equity_curve[-1]['equity'] - self.initial_capital) / self.initial_capital * 100) if equity_curve else 0
        }

    def _check_forced_liquidation(self, position: Dict, current_price: float) -> bool:
        """检查是否触发强制平仓。"""
        liquidation_price = position['liquidation_price']
        direction = position['direction']

        if direction == 'long':
            return current_price <= liquidation_price
        else:  # short
            return current_price >= liquidation_price

    def _calculate_futures_pnl(self, position: Dict, current_price: float, strategy) -> float:
        """计算期货盈亏。"""
        entry_price = position['entry_price']
        contracts = position['contracts']
        direction = position['direction']
        multiplier = strategy.multiplier

        price_change = current_price - entry_price

        if direction == 'short':
            price_change = -price_change

        pnl = price_change * contracts * multiplier

        return pnl


class OptionsBacktestEngine:
    """期权回测引擎 (T037).

    特点：
    - Greeks跟踪
    - 到期日处理
    - 时间价值衰减
    """

    def __init__(
        self,
        initial_capital: float,
        commission_rate: float,
        slippage_rate: float
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        strategy,
        symbol: str,
        start_date: str,
        end_date: str,
        capital: float
    ) -> Dict[str, Any]:
        """运行期权回测。"""
        self.logger.info(f"[OptionsEngine] Running options backtest for {symbol}")

        # Fetch market data
        from investlib_data.market_api import MarketDataFetcher
        fetcher = MarketDataFetcher()

        result = fetcher.fetch_with_fallback(symbol, start_date, end_date, prefer_cache=True)
        market_data = result['data']

        # Options position tracking
        positions = []  # List of option positions
        trades = []
        equity_curve = []
        expiry_events = []

        for i in range(len(market_data)):
            current_date = market_data.iloc[i]['timestamp']
            current_price = market_data.iloc[i]['close']

            # Check option expiry
            positions, expired = self._check_option_expiry(
                positions, current_date, current_price, strategy
            )

            if expired:
                expiry_events.extend(expired)
                for event in expired:
                    capital += event['pnl']
                    trades.append({
                        'date': current_date,
                        'action': 'EXPIRY',
                        'expiry_type': event['action'],
                        'pnl': event['pnl']
                    })

            # Get historical data
            historical_data = market_data.iloc[:i+1]

            # Generate signal
            signal = strategy.generate_signal(historical_data)

            if signal and signal.get('action') == 'COVERED_CALL_SETUP':
                # Execute covered call (multi-leg)
                legs = signal.get('legs', [])

                for leg in legs:
                    if leg['leg_type'] == 'stock':
                        # Buy stock
                        cost = leg['quantity'] * leg['entry_price']
                        if cost <= capital:
                            capital -= cost
                            trades.append({
                                'date': current_date,
                                'action': 'BUY_STOCK',
                                'quantity': leg['quantity'],
                                'price': leg['entry_price']
                            })

                    elif leg['leg_type'] == 'call_option':
                        # Sell call option
                        premium = leg['entry_price'] * 10000  # Multiplier
                        capital += premium

                        positions.append({
                            'type': 'call',
                            'direction': leg['direction'],
                            'strike': leg['strike_price'],
                            'entry_date': current_date,
                            'expiry_days': leg['expiry_days'],
                            'entry_premium': leg['entry_price'],
                            'greeks': leg.get('greeks', {})
                        })

                        trades.append({
                            'date': current_date,
                            'action': 'SELL_CALL',
                            'strike': leg['strike_price'],
                            'premium': premium
                        })

            # Track equity
            options_value = sum(self._estimate_option_value(pos, current_price) for pos in positions)
            total_equity = capital + options_value

            equity_curve.append({
                'date': current_date,
                'equity': total_equity,
                'cash': capital,
                'options_value': options_value
            })

        return {
            'strategy_type': 'option',
            'symbol': symbol,
            'trades': trades,
            'equity_curve': equity_curve,
            'expiry_events': expiry_events,
            'final_equity': equity_curve[-1]['equity'] if equity_curve else capital,
            'return_pct': ((equity_curve[-1]['equity'] - self.initial_capital) / self.initial_capital * 100) if equity_curve else 0
        }

    def _check_option_expiry(self, positions, current_date, current_price, strategy):
        """检查期权到期。"""
        active_positions = []
        expired_events = []

        for position in positions:
            # Simplified expiry check (days remaining)
            # In production, would use actual expiry date
            days_held = (pd.to_datetime(current_date) - pd.to_datetime(position['entry_date'])).days

            if days_held >= position['expiry_days']:
                # Option expired
                expiry_result = strategy.handle_expiry(
                    option_position=position,
                    underlying_price=current_price,
                    strike_price=position['strike']
                )

                expired_events.append(expiry_result)
            else:
                active_positions.append(position)

        return active_positions, expired_events

    def _estimate_option_value(self, position, current_price):
        """估算期权价值（简化版）。"""
        # Simplified: intrinsic value only
        strike = position['strike']
        direction = position['direction']

        if position['type'] == 'call':
            intrinsic = max(0, current_price - strike)
        else:
            intrinsic = max(0, strike - current_price)

        # For short positions, value is negative
        if direction == 'short':
            intrinsic = -intrinsic

        return intrinsic * 10000  # Multiplier
