"""Combination Strategy Data Models.

Multi-leg strategy structures for spreads and combinations.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Literal, Optional
from enum import Enum
import json


class CombinationType(Enum):
    """Pre-defined combination strategy types."""
    COVERED_CALL = "covered_call"
    BUTTERFLY_SPREAD = "butterfly_spread"
    CALENDAR_SPREAD = "calendar_spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    IRON_CONDOR = "iron_condor"
    VERTICAL_SPREAD = "vertical_spread"


@dataclass
class Leg:
    """Single leg of a multi-leg strategy.

    Attributes:
        contract: Contract symbol (e.g., '10005102.SH')
        direction: 'long' or 'short'
        quantity: Number of contracts
        asset_type: 'stock', 'futures', or 'option'
        strike_price: Option strike price (if option)
        expiry_date: Option expiry date (if option)
        greeks: Option Greeks dict (optional)
    """
    contract: str
    direction: Literal['long', 'short']
    quantity: int
    asset_type: Literal['stock', 'futures', 'option'] = 'option'
    strike_price: Optional[float] = None
    expiry_date: Optional[str] = None
    greeks: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Leg':
        """Create Leg from dictionary."""
        return cls(**data)


@dataclass
class CombinationStrategy:
    """Multi-leg combination strategy.

    Attributes:
        name: Strategy name
        strategy_type: Type from CombinationType enum
        legs: List of Leg objects
        status: 'active' or 'closed'
        strategy_id: Optional ID from database
    """
    name: str
    strategy_type: str
    legs: List[Leg]
    status: str = 'active'
    strategy_id: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'strategy_type': self.strategy_type,
            'legs': [leg.to_dict() for leg in self.legs],
            'status': self.status,
            'strategy_id': self.strategy_id
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> 'CombinationStrategy':
        """Create CombinationStrategy from dictionary."""
        legs = [Leg.from_dict(leg_data) for leg_data in data['legs']]
        return cls(
            name=data['name'],
            strategy_type=data['strategy_type'],
            legs=legs,
            status=data.get('status', 'active'),
            strategy_id=data.get('strategy_id')
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'CombinationStrategy':
        """Create CombinationStrategy from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Pre-defined strategy templates

def create_covered_call(
    stock_symbol: str,
    stock_quantity: int,
    call_symbol: str,
    call_strike: float,
    call_expiry: str
) -> CombinationStrategy:
    """Create covered call strategy template.

    Args:
        stock_symbol: Underlying stock symbol
        stock_quantity: Number of shares (should be 100 * num_contracts)
        call_symbol: Call option symbol
        call_strike: Call strike price
        call_expiry: Call expiry date (YYYY-MM-DD)

    Returns:
        CombinationStrategy with 2 legs (long stock + short call)
    """
    legs = [
        Leg(
            contract=stock_symbol,
            direction='long',
            quantity=stock_quantity,
            asset_type='stock'
        ),
        Leg(
            contract=call_symbol,
            direction='short',
            quantity=stock_quantity // 100,  # 1 contract per 100 shares
            asset_type='option',
            strike_price=call_strike,
            expiry_date=call_expiry
        )
    ]

    return CombinationStrategy(
        name=f"Covered Call - {stock_symbol}",
        strategy_type=CombinationType.COVERED_CALL.value,
        legs=legs
    )


def create_butterfly_spread(
    underlying: str,
    lower_strike: float,
    middle_strike: float,
    upper_strike: float,
    expiry: str,
    quantity: int = 1
) -> CombinationStrategy:
    """Create butterfly spread template.

    Args:
        underlying: Underlying symbol
        lower_strike: Lower strike price
        middle_strike: Middle strike (ATM)
        upper_strike: Upper strike price
        expiry: Expiry date (YYYY-MM-DD)
        quantity: Number of spreads

    Returns:
        CombinationStrategy with 3 legs
    """
    legs = [
        # Buy 1 lower strike call
        Leg(
            contract=f"{underlying}_C_{lower_strike}_{expiry}",
            direction='long',
            quantity=quantity,
            asset_type='option',
            strike_price=lower_strike,
            expiry_date=expiry
        ),
        # Sell 2 middle strike calls
        Leg(
            contract=f"{underlying}_C_{middle_strike}_{expiry}",
            direction='short',
            quantity=quantity * 2,
            asset_type='option',
            strike_price=middle_strike,
            expiry_date=expiry
        ),
        # Buy 1 upper strike call
        Leg(
            contract=f"{underlying}_C_{upper_strike}_{expiry}",
            direction='long',
            quantity=quantity,
            asset_type='option',
            strike_price=upper_strike,
            expiry_date=expiry
        )
    ]

    return CombinationStrategy(
        name=f"Butterfly Spread - {underlying}",
        strategy_type=CombinationType.BUTTERFLY_SPREAD.value,
        legs=legs
    )


def create_calendar_spread(
    underlying: str,
    strike: float,
    near_expiry: str,
    far_expiry: str,
    quantity: int = 1
) -> CombinationStrategy:
    """Create calendar spread template.

    Args:
        underlying: Underlying symbol
        strike: Strike price (same for both)
        near_expiry: Near-term expiry (YYYY-MM-DD)
        far_expiry: Far-term expiry (YYYY-MM-DD)
        quantity: Number of spreads

    Returns:
        CombinationStrategy with 2 legs
    """
    legs = [
        # Sell near-term call
        Leg(
            contract=f"{underlying}_C_{strike}_{near_expiry}",
            direction='short',
            quantity=quantity,
            asset_type='option',
            strike_price=strike,
            expiry_date=near_expiry
        ),
        # Buy far-term call
        Leg(
            contract=f"{underlying}_C_{strike}_{far_expiry}",
            direction='long',
            quantity=quantity,
            asset_type='option',
            strike_price=strike,
            expiry_date=far_expiry
        )
    ]

    return CombinationStrategy(
        name=f"Calendar Spread - {underlying}",
        strategy_type=CombinationType.CALENDAR_SPREAD.value,
        legs=legs
    )


def create_straddle(
    underlying: str,
    strike: float,
    expiry: str,
    quantity: int = 1,
    direction: Literal['long', 'short'] = 'long'
) -> CombinationStrategy:
    """Create straddle template.

    Args:
        underlying: Underlying symbol
        strike: Strike price (ATM)
        expiry: Expiry date (YYYY-MM-DD)
        quantity: Number of straddles
        direction: 'long' for long straddle, 'short' for short straddle

    Returns:
        CombinationStrategy with 2 legs (call + put)
    """
    legs = [
        # Call
        Leg(
            contract=f"{underlying}_C_{strike}_{expiry}",
            direction=direction,
            quantity=quantity,
            asset_type='option',
            strike_price=strike,
            expiry_date=expiry
        ),
        # Put
        Leg(
            contract=f"{underlying}_P_{strike}_{expiry}",
            direction=direction,
            quantity=quantity,
            asset_type='option',
            strike_price=strike,
            expiry_date=expiry
        )
    ]

    strategy_name = "Long Straddle" if direction == 'long' else "Short Straddle"

    return CombinationStrategy(
        name=f"{strategy_name} - {underlying}",
        strategy_type=CombinationType.STRADDLE.value,
        legs=legs
    )
