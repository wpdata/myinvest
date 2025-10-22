"""Risk Calculator for position sizing and risk management.

Implements risk calculation formulas for:
- Position sizing based on capital and risk percentage
- Max loss calculation
- Position limit validation (single position ≤20%, total ≤100%)
"""

from typing import Dict, Any, Optional


class RiskCalculator:
    """Calculate position sizes and risk metrics for trading."""

    def __init__(
        self,
        max_single_position_pct: float = 20.0,
        max_total_allocation_pct: float = 100.0
    ):
        """Initialize risk calculator with position limits.

        Args:
            max_single_position_pct: Maximum single position as % of capital (default 20%)
            max_total_allocation_pct: Maximum total allocation as % of capital (default 100%)
        """
        self.max_single_position_pct = max_single_position_pct
        self.max_total_allocation_pct = max_total_allocation_pct

    def calculate_position_size(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate position size based on risk parameters.

        Formula: position_size = (capital * risk_pct) / abs(entry - stop_loss)

        Args:
            capital: Total available capital
            risk_pct: Risk percentage per trade (e.g., 2.0 for 2%)
            entry_price: Entry price per share/contract
            stop_loss: Stop-loss price

        Returns:
            Position size as percentage of capital (0-100)

        Raises:
            ValueError: If inputs are invalid
        """
        # Validation
        if capital <= 0:
            raise ValueError("Capital must be positive")
        if risk_pct <= 0 or risk_pct > 100:
            raise ValueError("Risk percentage must be between 0 and 100")
        if entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if stop_loss <= 0:
            raise ValueError("Stop-loss must be positive")

        # Calculate risk per share
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            raise ValueError("Entry price and stop-loss cannot be equal")

        # Calculate position size
        risk_amount = capital * (risk_pct / 100.0)
        position_value = risk_amount / (price_risk / entry_price)
        position_size_pct = (position_value / capital) * 100

        # Cap at maximum single position limit
        position_size_pct = min(position_size_pct, self.max_single_position_pct)

        return round(position_size_pct, 2)

    def calculate_max_loss(
        self,
        capital: float,
        position_size_pct: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate maximum loss amount for a position.

        Formula: max_loss = (capital * position_size_pct / 100) * abs(entry - stop_loss) / entry

        Args:
            capital: Total available capital
            position_size_pct: Position size as percentage of capital
            entry_price: Entry price per share/contract
            stop_loss: Stop-loss price

        Returns:
            Maximum loss amount in base currency

        Raises:
            ValueError: If inputs are invalid
        """
        # Validation
        if capital <= 0:
            raise ValueError("Capital must be positive")
        if position_size_pct < 0 or position_size_pct > 100:
            raise ValueError("Position size must be between 0 and 100")
        if entry_price <= 0:
            raise ValueError("Entry price must be positive")
        if stop_loss <= 0:
            raise ValueError("Stop-loss must be positive")

        # Calculate position value
        position_value = capital * (position_size_pct / 100.0)

        # Calculate max loss
        price_risk_pct = abs(entry_price - stop_loss) / entry_price
        max_loss = position_value * price_risk_pct

        return round(max_loss, 2)

    def validate_position_limits(
        self,
        position_size_pct: float,
        current_allocation_pct: float = 0.0
    ) -> Dict[str, Any]:
        """Validate position sizing against risk limits.

        Checks:
        1. Single position ≤ max_single_position_pct (default 20%)
        2. Total allocation (current + new) ≤ max_total_allocation_pct (default 100%)

        Args:
            position_size_pct: Proposed position size as % of capital
            current_allocation_pct: Current total allocation as % of capital

        Returns:
            Validation result dictionary:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "max_allowed_position": float
            }
        """
        errors = []
        warnings = []
        valid = True

        # Check single position limit
        if position_size_pct > self.max_single_position_pct:
            errors.append(
                f"Position size {position_size_pct:.1f}% exceeds single position limit "
                f"{self.max_single_position_pct:.1f}%"
            )
            valid = False

        # Check total allocation limit
        total_allocation = current_allocation_pct + position_size_pct
        if total_allocation > self.max_total_allocation_pct:
            errors.append(
                f"Total allocation {total_allocation:.1f}% would exceed limit "
                f"{self.max_total_allocation_pct:.1f}% (current: {current_allocation_pct:.1f}%, "
                f"new: {position_size_pct:.1f}%)"
            )
            valid = False

        # Calculate max allowed position given current allocation
        max_allowed = self.max_total_allocation_pct - current_allocation_pct
        max_allowed = min(max_allowed, self.max_single_position_pct)

        # Warning for high allocation
        if position_size_pct > 15.0 and valid:
            warnings.append(
                f"Position size {position_size_pct:.1f}% is high (>15% of capital)"
            )

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "max_allowed_position": round(max_allowed, 2)
        }

    def calculate_risk_metrics(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size_pct: Optional[float] = None,
        risk_pct: float = 2.0,
        current_allocation_pct: float = 0.0
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics for a trade.

        Args:
            capital: Total available capital
            entry_price: Entry price per share/contract
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            position_size_pct: Position size (if None, calculate from risk_pct)
            risk_pct: Risk percentage per trade (default 2%)
            current_allocation_pct: Current total allocation

        Returns:
            Complete risk metrics dictionary
        """
        # Calculate position size if not provided
        if position_size_pct is None:
            position_size_pct = self.calculate_position_size(
                capital, risk_pct, entry_price, stop_loss
            )

        # Calculate max loss
        max_loss = self.calculate_max_loss(
            capital, position_size_pct, entry_price, stop_loss
        )

        # Calculate max gain (if take-profit reached)
        position_value = capital * (position_size_pct / 100.0)
        gain_pct = abs(take_profit - entry_price) / entry_price
        max_gain = position_value * gain_pct

        # Calculate risk-reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0

        # Validate position limits
        validation = self.validate_position_limits(
            position_size_pct, current_allocation_pct
        )

        return {
            "position_size_pct": round(position_size_pct, 2),
            "position_value": round(position_value, 2),
            "max_loss": round(max_loss, 2),
            "max_gain": round(max_gain, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "validation": validation
        }
