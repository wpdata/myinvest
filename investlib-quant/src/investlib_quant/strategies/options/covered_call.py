"""
Covered Call Options Strategy (T036)

备兑开仓策略：持有标的股票的同时卖出认购期权，获取权利金收入。
"""

from typing import Optional, Dict
import pandas as pd
import numpy as np
from ..base import OptionsStrategy


class CoveredCallStrategy(OptionsStrategy):
    """备兑开仓策略 (T036).

    策略逻辑：
    - 持有标的股票（100股为1手）
    - 卖出平值或虚值认购期权，收取权利金
    - 如果期权未被行权，赚取权利金收入
    - 如果期权被行权，按行权价卖出股票
    - 适合对标的温和看涨或中性的投资者

    收益特征：
    - 最大收益：权利金 + (行权价 - 股票成本)
    - 最大损失：股票下跌至0（但有权利金缓冲）
    - 盈亏平衡点：股票成本 - 权利金

    参数：
    - moneyness_target: 目标价值度（1.0=平值，1.05=5%虚值）
    - expiry_days_target: 目标到期天数（默认30天）
    - risk_free_rate: 无风险利率（默认3%）
    """

    def __init__(
        self,
        name: str = "备兑开仓",
        moneyness_target: float = 1.05,  # 5% out-of-the-money
        expiry_days_target: int = 30,
        risk_free_rate: float = 0.03
    ):
        """初始化备兑开仓策略。

        Args:
            name: 策略名称
            moneyness_target: 目标价值度（行权价/标的价格）
            expiry_days_target: 目标到期天数
            risk_free_rate: 无风险利率
        """
        super().__init__(name, option_type='call')
        self.moneyness_target = moneyness_target
        self.expiry_days_target = expiry_days_target
        self.risk_free_rate = risk_free_rate

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """生成备兑开仓信号。

        Args:
            market_data: 标的股票市场数据

        Returns:
            信号字典或 None（包含股票持仓 + 期权卖出）
        """
        # Validate data
        if not self.validate_data(market_data, required_rows=20):
            return None

        # Get latest price
        df = market_data.copy()
        latest = df.iloc[-1]
        current_price = latest['close']

        # Calculate historical volatility (20-day)
        log_returns = np.log(df['close'] / df['close'].shift(1))
        hist_volatility = log_returns.tail(20).std() * np.sqrt(252)

        # Determine strike price (5% out-of-the-money)
        strike_price = current_price * self.moneyness_target

        # Calculate time to expiry (in years)
        time_to_expiry = self.expiry_days_target / 365.0

        # Calculate option Greeks
        greeks = self.calculate_greeks(
            underlying_price=current_price,
            strike_price=strike_price,
            time_to_expiry=time_to_expiry,
            risk_free_rate=self.risk_free_rate,
            volatility=hist_volatility
        )

        # Estimate option premium using Black-Scholes intrinsic value + time value
        # For simplicity, use approximation: premium ≈ 2-3% of underlying price for ATM
        # For OTM, reduce by moneyness difference
        moneyness = strike_price / current_price
        premium_estimate = current_price * 0.025 * (2 - moneyness)  # Rough estimate

        # Generate covered call setup signal
        return {
            "action": "COVERED_CALL_SETUP",
            "legs": [
                {
                    "leg_type": "stock",
                    "action": "BUY",
                    "symbol": "UNDERLYING",  # Placeholder
                    "quantity": 100,  # 1 lot = 100 shares
                    "entry_price": float(current_price),
                    "direction": "long"
                },
                {
                    "leg_type": "call_option",
                    "action": "SELL",  # Short call
                    "strike_price": float(strike_price),
                    "expiry_days": self.expiry_days_target,
                    "quantity": 1,  # 1 contract
                    "entry_price": float(premium_estimate),
                    "direction": "short",
                    "greeks": greeks
                }
            ],
            "position_size_pct": 0.3,  # Use 30% of capital
            "confidence": "MEDIUM",
            "reasoning": {
                "strategy": "备兑开仓 (Covered Call)",
                "underlying_price": float(current_price),
                "strike_price": float(strike_price),
                "moneyness": f"{(moneyness - 1) * 100:.1f}% 虚值",
                "premium_estimate": float(premium_estimate),
                "hist_volatility": f"{hist_volatility * 100:.2f}%",
                "max_profit": float(premium_estimate * 10000 + (strike_price - current_price) * 100),
                "breakeven": float(current_price - premium_estimate),
                "greeks": {
                    "delta": f"{greeks['delta']:.4f}",
                    "gamma": f"{greeks['gamma']:.4f}",
                    "vega": f"{greeks['vega']:.4f}",
                    "theta": f"{greeks['theta']:.4f} (每日时间衰减)"
                },
                "适用场景": "对标的温和看涨或中性，希望通过卖出期权赚取额外收入"
            }
        }

    def calculate_max_profit(
        self,
        stock_entry_price: float,
        strike_price: float,
        premium_received: float,
        quantity: int = 100
    ) -> Dict[str, float]:
        """计算备兑开仓的最大收益。

        Args:
            stock_entry_price: 股票买入价
            strike_price: 期权行权价
            premium_received: 收到的权利金
            quantity: 股票数量（默认100股）

        Returns:
            收益详情字典
        """
        # Max profit = premium + (strike - stock_cost)
        stock_profit_if_called = (strike_price - stock_entry_price) * quantity
        option_premium_income = premium_received * 10000  # Multiplier for options

        max_profit = stock_profit_if_called + option_premium_income
        max_profit_pct = max_profit / (stock_entry_price * quantity) * 100

        return {
            "max_profit": float(max_profit),
            "max_profit_pct": float(max_profit_pct),
            "stock_profit_if_called": float(stock_profit_if_called),
            "option_premium_income": float(option_premium_income),
            "breakeven_price": float(stock_entry_price - premium_received)
        }

    def calculate_max_loss(
        self,
        stock_entry_price: float,
        premium_received: float,
        quantity: int = 100
    ) -> Dict[str, float]:
        """计算备兑开仓的最大损失。

        Args:
            stock_entry_price: 股票买入价
            premium_received: 收到的权利金
            quantity: 股票数量

        Returns:
            损失详情字典
        """
        # Max loss = stock drops to 0 (minus premium received as cushion)
        max_loss = stock_entry_price * quantity - (premium_received * 10000)

        # Practical max loss (20% drop scenario)
        practical_loss_20pct = stock_entry_price * quantity * 0.20 - (premium_received * 10000)

        return {
            "theoretical_max_loss": float(max_loss),
            "practical_loss_20pct_drop": float(practical_loss_20pct),
            "premium_cushion": float(premium_received * 10000),
            "cushion_pct": float((premium_received * 10000) / (stock_entry_price * quantity) * 100)
        }

    def should_roll_option(
        self,
        current_price: float,
        strike_price: float,
        days_to_expiry: int,
        premium_remaining: float
    ) -> Dict[str, any]:
        """判断是否应该展期期权（Roll forward）。

        Args:
            current_price: 当前标的价格
            strike_price: 当前期权行权价
            days_to_expiry: 到期天数
            premium_remaining: 剩余权利金价值

        Returns:
            展期建议字典
        """
        # Roll criteria:
        # 1. Option is deep in-the-money (ITM) → likely to be exercised
        # 2. Near expiry (< 7 days) → time value decaying fast
        # 3. Low remaining premium → not worth holding

        is_deep_itm = current_price > strike_price * 1.05
        near_expiry = days_to_expiry <= 7
        low_premium = premium_remaining < strike_price * 0.01

        should_roll = is_deep_itm or (near_expiry and not low_premium)

        return {
            "should_roll": should_roll,
            "reason": [],
            "is_deep_itm": is_deep_itm,
            "near_expiry": near_expiry,
            "low_premium": low_premium,
            "recommendation": (
                "建议展期：买回当前期权，卖出更远月份期权" if should_roll
                else "持有至到期"
            )
        }


# Example usage and testing
if __name__ == '__main__':
    # Create sample stock data
    dates = pd.date_range(start='2025-01-01', periods=60, freq='D')
    np.random.seed(42)

    # Generate moderately bullish stock price
    trend = np.linspace(50, 53, 60)
    noise = np.random.normal(0, 0.5, 60)
    close_prices = trend + noise

    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.normal(0, 0.2, 60),
        'high': close_prices + np.abs(np.random.normal(0.5, 0.2, 60)),
        'low': close_prices - np.abs(np.random.normal(0.5, 0.2, 60)),
        'close': close_prices,
        'volume': np.random.randint(100000, 500000, 60)
    })

    # Test strategy
    strategy = CoveredCallStrategy(
        name="50ETF备兑开仓",
        moneyness_target=1.05,  # 5% OTM
        expiry_days_target=30
    )

    print("=" * 60)
    print(f"策略测试: {strategy.name}")
    print(f"资产类型: {strategy.asset_type}")
    print(f"期权类型: {strategy.option_type}")
    print(f"目标行权价: 标的价格 × {strategy.moneyness_target}")
    print(f"目标到期天数: {strategy.expiry_days_target} 天")
    print("=" * 60)

    # Generate signal
    signal = strategy.generate_signal(sample_data)

    if signal:
        print("\n✅ 备兑开仓信号:")
        print(f"  策略: {signal['action']}")
        print(f"  仓位: {signal['position_size_pct'] * 100}%")
        print(f"  信心: {signal['confidence']}")

        print(f"\n📊 交易腿:")
        for i, leg in enumerate(signal['legs'], 1):
            print(f"\n  Leg {i}: {leg['leg_type']}")
            print(f"    动作: {leg['action']}")
            print(f"    方向: {leg['direction']}")
            if leg['leg_type'] == 'stock':
                print(f"    数量: {leg['quantity']} 股")
                print(f"    价格: ¥{leg['entry_price']:.2f}")
            else:
                print(f"    行权价: ¥{leg['strike_price']:.2f}")
                print(f"    权利金: ¥{leg['entry_price']:.4f}")
                print(f"    到期: {leg['expiry_days']} 天")
                print(f"    Greeks:")
                for greek, value in leg['greeks'].items():
                    print(f"      {greek}: {value}")

        print(f"\n💡 策略推理:")
        for key, value in signal['reasoning'].items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        # Calculate profit/loss scenarios
        stock_price = signal['legs'][0]['entry_price']
        strike_price = signal['legs'][1]['strike_price']
        premium = signal['legs'][1]['entry_price']

        profit_scenario = strategy.calculate_max_profit(
            stock_entry_price=stock_price,
            strike_price=strike_price,
            premium_received=premium
        )

        loss_scenario = strategy.calculate_max_loss(
            stock_entry_price=stock_price,
            premium_received=premium
        )

        print(f"\n📈 收益分析:")
        print(f"  最大收益: ¥{profit_scenario['max_profit']:,.2f} ({profit_scenario['max_profit_pct']:.2f}%)")
        print(f"    - 股票盈利（如被行权）: ¥{profit_scenario['stock_profit_if_called']:,.2f}")
        print(f"    - 权利金收入: ¥{profit_scenario['option_premium_income']:,.2f}")
        print(f"  盈亏平衡点: ¥{profit_scenario['breakeven_price']:.2f}")

        print(f"\n📉 风险分析:")
        print(f"  理论最大损失: ¥{loss_scenario['theoretical_max_loss']:,.2f}")
        print(f"  实际损失（20%下跌）: ¥{loss_scenario['practical_loss_20pct_drop']:,.2f}")
        print(f"  权利金缓冲: ¥{loss_scenario['premium_cushion']:,.2f} ({loss_scenario['cushion_pct']:.2f}%)")

    else:
        print("\n⏸️  无交易信号")

    print("\n" + "=" * 60)
