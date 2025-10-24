"""
Futures Trend Following Strategy (T035)

基于均线系统的期货趋势跟踪策略，支持双向交易（做多/做空）。
"""

from typing import Optional, Dict, Literal
import pandas as pd
import numpy as np
from ..base import FuturesStrategy


class FuturesTrendFollowing(FuturesStrategy):
    """期货趋势跟踪策略 (T035).

    策略逻辑：
    - 使用双均线系统（快线/慢线）识别趋势
    - 做多信号：快线上穿慢线且价格在慢线之上
    - 做空信号：快线下穿慢线且价格在慢线之下
    - 支持合约自动展期
    - 包含强平风险管理

    参数：
    - fast_period: 快速均线周期（默认20）
    - slow_period: 慢速均线周期（默认60）
    - margin_rate: 保证金率（默认15%）
    - multiplier: 合约乘数（IF: 300, IC: 200）
    - stop_loss_pct: 止损百分比（默认3%）
    - take_profit_pct: 止盈百分比（默认6%）
    """

    def __init__(
        self,
        name: str = "期货趋势跟踪",
        fast_period: int = 20,
        slow_period: int = 60,
        margin_rate: float = 0.15,
        multiplier: int = 300,
        stop_loss_pct: float = 0.03,
        take_profit_pct: float = 0.06
    ):
        """初始化期货趋势跟踪策略。

        Args:
            name: 策略名称
            fast_period: 快速均线周期
            slow_period: 慢速均线周期
            margin_rate: 保证金率
            multiplier: 合约乘数
            stop_loss_pct: 止损百分比
            take_profit_pct: 止盈百分比
        """
        super().__init__(name, margin_rate, multiplier)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """生成交易信号（支持做多和做空）。

        Args:
            market_data: 市场数据 DataFrame

        Returns:
            信号字典或 None
        """
        # Validate data
        if not self.validate_data(market_data, required_rows=self.slow_period):
            return None

        # Calculate moving averages
        df = market_data.copy()
        df['MA_fast'] = df['close'].rolling(window=self.fast_period).mean()
        df['MA_slow'] = df['close'].rolling(window=self.slow_period).mean()

        # Check if we have enough data
        if df['MA_slow'].isna().iloc[-1]:
            return None

        # Get latest values
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        current_price = latest['close']
        ma_fast_current = latest['MA_fast']
        ma_slow_current = latest['MA_slow']
        ma_fast_previous = previous['MA_fast']
        ma_slow_previous = previous['MA_slow']

        # Detect crossovers
        bullish_crossover = (
            ma_fast_current > ma_slow_current and
            ma_fast_previous <= ma_slow_previous
        )

        bearish_crossover = (
            ma_fast_current < ma_slow_current and
            ma_fast_previous >= ma_slow_previous
        )

        # Trend confirmation: price position relative to slow MA
        price_above_slow_ma = current_price > ma_slow_current
        price_below_slow_ma = current_price < ma_slow_current

        # Generate signals
        signal = None
        direction = None
        confidence = "MEDIUM"

        if bullish_crossover and price_above_slow_ma:
            # BUY (做多) signal
            signal = "BUY"
            direction = "long"
            confidence = "HIGH"
            reasoning = {
                "crossover": "快线上穿慢线",
                "trend": "价格在慢线之上",
                "ma_fast": float(ma_fast_current),
                "ma_slow": float(ma_slow_current),
                "price": float(current_price),
                "signal_type": "做多 (Long)"
            }

        elif bearish_crossover and price_below_slow_ma:
            # SELL (做空) signal
            signal = "SELL"
            direction = "short"
            confidence = "HIGH"
            reasoning = {
                "crossover": "快线下穿慢线",
                "trend": "价格在慢线之下",
                "ma_fast": float(ma_fast_current),
                "ma_slow": float(ma_slow_current),
                "price": float(current_price),
                "signal_type": "做空 (Short)"
            }

        else:
            # No signal
            return None

        # Calculate stop loss and take profit
        if direction == "long":
            stop_loss = current_price * (1 - self.stop_loss_pct)
            take_profit = current_price * (1 + self.take_profit_pct)
        else:  # short
            stop_loss = current_price * (1 + self.stop_loss_pct)
            take_profit = current_price * (1 - self.take_profit_pct)

        # Calculate liquidation price
        liquidation_price = self.calculate_liquidation_price(
            entry_price=current_price,
            direction=direction,
            force_close_margin_rate=0.10
        )

        return {
            "action": signal,
            "direction": direction,
            "entry_price": float(current_price),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "liquidation_price": float(liquidation_price),
            "position_size_pct": 0.5,  # Use 50% of capital for margin
            "confidence": confidence,
            "reasoning": reasoning
        }

    def check_rollover_needed(
        self,
        current_contract: str,
        current_date: pd.Timestamp
    ) -> Optional[str]:
        """检查是否需要合约展期。

        Args:
            current_contract: 当前合约代码
            current_date: 当前日期

        Returns:
            新合约代码或None
        """
        return self.handle_rollover(current_contract, current_date)

    def calculate_position_size_with_margin(
        self,
        capital: float,
        entry_price: float,
        position_size_pct: float = 0.5,
        direction: Literal['long', 'short'] = 'long'
    ) -> Dict[str, any]:
        """计算期货持仓（包含保证金占用详情）。

        Args:
            capital: 可用资金
            entry_price: 入场价格
            position_size_pct: 仓位百分比
            direction: 交易方向

        Returns:
            持仓详情字典
        """
        contracts = self.calculate_position_size(
            capital=capital,
            entry_price=entry_price,
            position_size_pct=position_size_pct,
            direction=direction
        )

        margin_used = contracts * entry_price * self.multiplier * self.margin_rate
        notional_value = contracts * entry_price * self.multiplier
        leverage = notional_value / margin_used if margin_used > 0 else 0

        return {
            "contracts": contracts,
            "margin_used": float(margin_used),
            "notional_value": float(notional_value),
            "leverage": float(leverage),
            "margin_rate": self.margin_rate,
            "multiplier": self.multiplier,
            "direction": direction
        }


# Example usage and testing
if __name__ == '__main__':
    # Create sample futures data
    dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
    np.random.seed(42)

    # Generate trending price data
    trend = np.linspace(4800, 5200, 100)
    noise = np.random.normal(0, 50, 100)
    close_prices = trend + noise

    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.normal(0, 10, 100),
        'high': close_prices + np.abs(np.random.normal(20, 10, 100)),
        'low': close_prices - np.abs(np.random.normal(20, 10, 100)),
        'close': close_prices,
        'volume': np.random.randint(10000, 50000, 100)
    })

    # Test strategy
    strategy = FuturesTrendFollowing(
        name="IF期货趋势跟踪",
        fast_period=20,
        slow_period=60,
        margin_rate=0.15,
        multiplier=300
    )

    print("=" * 60)
    print(f"策略测试: {strategy.name}")
    print(f"资产类型: {strategy.asset_type}")
    print(f"交易规则: {strategy.trading_rule}")
    print(f"支持方向: {strategy.direction_supported}")
    print(f"保证金率: {strategy.margin_rate * 100}%")
    print(f"合约乘数: {strategy.multiplier}")
    print("=" * 60)

    # Generate signal
    signal = strategy.generate_signal(sample_data)

    if signal:
        print("\n✅ 交易信号:")
        print(f"  动作: {signal['action']}")
        print(f"  方向: {signal['direction']}")
        print(f"  入场价: {signal['entry_price']:.2f}")
        print(f"  止损价: {signal['stop_loss']:.2f}")
        print(f"  止盈价: {signal['take_profit']:.2f}")
        print(f"  强平价: {signal['liquidation_price']:.2f}")
        print(f"  仓位: {signal['position_size_pct'] * 100}%")
        print(f"  信心: {signal['confidence']}")
        print(f"\n  推理:")
        for key, value in signal['reasoning'].items():
            print(f"    {key}: {value}")

        # Calculate position details
        capital = 100000  # 10万资金
        position_details = strategy.calculate_position_size_with_margin(
            capital=capital,
            entry_price=signal['entry_price'],
            position_size_pct=signal['position_size_pct'],
            direction=signal['direction']
        )

        print(f"\n📊 持仓详情 (可用资金: ¥{capital:,.0f}):")
        print(f"  合约数量: {position_details['contracts']} 手")
        print(f"  保证金占用: ¥{position_details['margin_used']:,.2f}")
        print(f"  名义价值: ¥{position_details['notional_value']:,.2f}")
        print(f"  杠杆倍数: {position_details['leverage']:.2f}x")

    else:
        print("\n⏸️  无交易信号 (HOLD)")

    # Test rollover
    print("\n" + "=" * 60)
    print("合约展期测试:")
    test_contract = "IF2506.CFFEX"
    test_date = pd.Timestamp('2025-06-10')
    next_contract = strategy.check_rollover_needed(test_contract, test_date)

    if next_contract:
        print(f"  ⚠️  需要展期: {test_contract} → {next_contract}")
    else:
        print(f"  ✓ 无需展期: {test_contract}")

    print("=" * 60)
