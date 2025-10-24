"""
Combination Strategy Data Models (T050)

Multi-leg option and futures combination strategies.
"""

from typing import List, Dict, Literal, Optional
from dataclasses import dataclass, field
from enum import Enum


class CombinationType(str, Enum):
    """Pre-defined combination strategy types."""
    COVERED_CALL = "covered_call"  # 备兑开仓
    BUTTERFLY_SPREAD = "butterfly_spread"  # 蝶式价差
    CALENDAR_SPREAD = "calendar_spread"  # 日历价差
    STRADDLE = "straddle"  # 跨式组合
    STRANGLE = "strangle"  # 宽跨式组合
    IRON_CONDOR = "iron_condor"  # 铁鹰式组合
    BULL_CALL_SPREAD = "bull_call_spread"  # 牛市看涨价差
    BEAR_PUT_SPREAD = "bear_put_spread"  # 熊市看跌价差
    CUSTOM = "custom"  # 自定义组合


@dataclass
class Leg:
    """Single leg in a multi-leg strategy.

    Attributes:
        leg_id: Unique identifier for this leg
        asset_type: 'stock' | 'futures' | 'call' | 'put'
        action: 'BUY' | 'SELL'
        symbol: Underlying symbol
        quantity: Number of contracts/shares
        strike_price: Strike price (for options)
        expiry_date: Expiry date (for options/futures)
        entry_price: Entry price
        multiplier: Contract multiplier
        greeks: Option Greeks (if applicable)
    """
    leg_id: str
    asset_type: Literal['stock', 'futures', 'call', 'put']
    action: Literal['BUY', 'SELL']
    symbol: str
    quantity: int
    entry_price: float
    strike_price: Optional[float] = None
    expiry_date: Optional[str] = None
    multiplier: int = 1
    greeks: Dict[str, float] = field(default_factory=dict)

    @property
    def direction(self) -> str:
        """Get position direction."""
        return 'long' if self.action == 'BUY' else 'short'

    @property
    def cost(self) -> float:
        """Calculate leg cost (positive = debit, negative = credit)."""
        sign = 1 if self.action == 'BUY' else -1
        return sign * self.entry_price * self.quantity * self.multiplier


@dataclass
class CombinationStrategy:
    """Multi-leg combination strategy.

    Attributes:
        strategy_id: Unique identifier
        strategy_name: Human-readable name
        strategy_type: Type from CombinationType enum
        legs: List of strategy legs
        status: 'active' | 'closed' | 'expired'
        created_at: Creation timestamp
        notes: Additional notes
    """
    strategy_id: str
    strategy_name: str
    strategy_type: CombinationType
    legs: List[Leg]
    status: Literal['active', 'closed', 'expired'] = 'active'
    created_at: Optional[str] = None
    notes: Optional[str] = None

    @property
    def net_cost(self) -> float:
        """Calculate net cost/credit of the combination."""
        return sum(leg.cost for leg in self.legs)

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit spread (net outflow)."""
        return self.net_cost > 0

    @property
    def is_credit(self) -> bool:
        """Check if this is a credit spread (net inflow)."""
        return self.net_cost < 0

    def get_legs_by_type(self, asset_type: str) -> List[Leg]:
        """Get all legs of a specific type."""
        return [leg for leg in self.legs if leg.asset_type == asset_type]

    def get_long_legs(self) -> List[Leg]:
        """Get all long legs."""
        return [leg for leg in self.legs if leg.action == 'BUY']

    def get_short_legs(self) -> List[Leg]:
        """Get all short legs."""
        return [leg for leg in self.legs if leg.action == 'SELL']


# Pre-defined strategy templates
class StrategyTemplates:
    """Factory for creating common combination strategies."""

    @staticmethod
    def covered_call(
        stock_symbol: str,
        stock_price: float,
        strike_price: float,
        call_premium: float,
        expiry_date: str,
        quantity: int = 100
    ) -> CombinationStrategy:
        """Create covered call strategy (备兑开仓).

        Args:
            stock_symbol: Stock symbol
            stock_price: Current stock price
            strike_price: Call option strike
            call_premium: Premium received
            expiry_date: Option expiry date
            quantity: Stock quantity (default 100 shares = 1 lot)

        Returns:
            CombinationStrategy with 2 legs
        """
        legs = [
            Leg(
                leg_id="leg1_stock",
                asset_type="stock",
                action="BUY",
                symbol=stock_symbol,
                quantity=quantity,
                entry_price=stock_price,
                multiplier=1
            ),
            Leg(
                leg_id="leg2_call",
                asset_type="call",
                action="SELL",
                symbol=stock_symbol,
                quantity=1,  # 1 contract
                entry_price=call_premium,
                strike_price=strike_price,
                expiry_date=expiry_date,
                multiplier=quantity  # 1 contract = 100 shares
            )
        ]

        return CombinationStrategy(
            strategy_id=f"covered_call_{stock_symbol}_{expiry_date}",
            strategy_name=f"备兑开仓 - {stock_symbol}",
            strategy_type=CombinationType.COVERED_CALL,
            legs=legs,
            notes=f"持有{quantity}股{stock_symbol}，卖出{strike_price}行权价认购期权"
        )

    @staticmethod
    def butterfly_spread(
        symbol: str,
        lower_strike: float,
        middle_strike: float,
        upper_strike: float,
        premium_lower: float,
        premium_middle: float,
        premium_upper: float,
        expiry_date: str,
        option_type: Literal['call', 'put'] = 'call'
    ) -> CombinationStrategy:
        """Create butterfly spread strategy (蝶式价差).

        Args:
            symbol: Underlying symbol
            lower_strike: Lower strike price
            middle_strike: Middle strike (ATM)
            upper_strike: Upper strike price
            premium_lower: Premium for lower strike
            premium_middle: Premium for middle strike
            premium_upper: Premium for upper strike
            expiry_date: Expiry date
            option_type: 'call' or 'put'

        Returns:
            CombinationStrategy with 3 legs (4 options)
        """
        legs = [
            # Buy 1 lower strike
            Leg(
                leg_id="leg1_lower",
                asset_type=option_type,
                action="BUY",
                symbol=symbol,
                quantity=1,
                entry_price=premium_lower,
                strike_price=lower_strike,
                expiry_date=expiry_date,
                multiplier=10000
            ),
            # Sell 2 middle strike
            Leg(
                leg_id="leg2_middle",
                asset_type=option_type,
                action="SELL",
                symbol=symbol,
                quantity=2,
                entry_price=premium_middle,
                strike_price=middle_strike,
                expiry_date=expiry_date,
                multiplier=10000
            ),
            # Buy 1 upper strike
            Leg(
                leg_id="leg3_upper",
                asset_type=option_type,
                action="BUY",
                symbol=symbol,
                quantity=1,
                entry_price=premium_upper,
                strike_price=upper_strike,
                expiry_date=expiry_date,
                multiplier=10000
            )
        ]

        return CombinationStrategy(
            strategy_id=f"butterfly_{symbol}_{expiry_date}",
            strategy_name=f"蝶式价差 - {symbol}",
            strategy_type=CombinationType.BUTTERFLY_SPREAD,
            legs=legs,
            notes=f"买入{lower_strike}/{upper_strike}，卖出2份{middle_strike}"
        )

    @staticmethod
    def straddle(
        symbol: str,
        strike_price: float,
        call_premium: float,
        put_premium: float,
        expiry_date: str,
        action: Literal['BUY', 'SELL'] = 'BUY'
    ) -> CombinationStrategy:
        """Create straddle strategy (跨式组合).

        Args:
            symbol: Underlying symbol
            strike_price: Strike (usually ATM)
            call_premium: Call option premium
            put_premium: Put option premium
            expiry_date: Expiry date
            action: 'BUY' (long straddle) or 'SELL' (short straddle)

        Returns:
            CombinationStrategy with 2 legs
        """
        legs = [
            Leg(
                leg_id="leg1_call",
                asset_type="call",
                action=action,
                symbol=symbol,
                quantity=1,
                entry_price=call_premium,
                strike_price=strike_price,
                expiry_date=expiry_date,
                multiplier=10000
            ),
            Leg(
                leg_id="leg2_put",
                asset_type="put",
                action=action,
                symbol=symbol,
                quantity=1,
                entry_price=put_premium,
                strike_price=strike_price,
                expiry_date=expiry_date,
                multiplier=10000
            )
        ]

        strategy_name = "买入跨式" if action == "BUY" else "卖出跨式"

        return CombinationStrategy(
            strategy_id=f"straddle_{symbol}_{expiry_date}",
            strategy_name=f"{strategy_name} - {symbol}",
            strategy_type=CombinationType.STRADDLE,
            legs=legs,
            notes=f"{strategy_name}，行权价{strike_price}"
        )


# Example usage
if __name__ == '__main__':
    # Test covered call
    covered_call = StrategyTemplates.covered_call(
        stock_symbol="600519.SH",
        stock_price=1800,
        strike_price=1900,
        call_premium=50,
        expiry_date="2025-03-21",
        quantity=100
    )

    print(f"策略: {covered_call.strategy_name}")
    print(f"类型: {covered_call.strategy_type.value}")
    print(f"腿数: {len(covered_call.legs)}")
    print(f"净成本: ¥{covered_call.net_cost:,.2f}")
    print(f"借方/贷方: {'借方' if covered_call.is_debit else '贷方'}")

    for leg in covered_call.legs:
        print(f"\n  腿 {leg.leg_id}:")
        print(f"    类型: {leg.asset_type}")
        print(f"    动作: {leg.action} ({leg.direction})")
        print(f"    数量: {leg.quantity}")
        print(f"    成本: ¥{leg.cost:,.2f}")
