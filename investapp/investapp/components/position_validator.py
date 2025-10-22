"""Position Validator for risk limit enforcement."""

from typing import Dict, Any, List


class ValidationResult:
    """Validation result container."""

    def __init__(self, valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []


class PositionValidator:
    """Validate position sizing against risk limits."""

    def __init__(
        self,
        max_single_position_pct: float = 20.0,
        max_total_allocation_pct: float = 100.0
    ):
        self.max_single_position_pct = max_single_position_pct
        self.max_total_allocation_pct = max_total_allocation_pct

    def validate_position(
        self,
        recommendation: Dict[str, Any],
        current_holdings: Dict[str, Any],
        total_capital: float
    ) -> ValidationResult:
        """Validate position against limits.

        Args:
            recommendation: Recommendation with position_size_pct
            current_holdings: Dict mapping symbol to value
            total_capital: Total capital

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        position_pct = recommendation.get('position_size_pct', 0)

        # Check single position limit
        if position_pct > self.max_single_position_pct:
            errors.append(
                f"单笔仓位{position_pct:.1f}%超过限制{self.max_single_position_pct:.1f}%"
            )

        # Calculate current allocation
        current_value = sum(current_holdings.values()) if current_holdings else 0
        current_pct = (current_value / total_capital * 100) if total_capital > 0 else 0

        # Check total allocation
        total_pct = current_pct + position_pct
        if total_pct > self.max_total_allocation_pct:
            errors.append(
                f"总仓位{total_pct:.1f}%将超过限制{self.max_total_allocation_pct:.1f}% "
                f"(当前{current_pct:.1f}% + 新增{position_pct:.1f}%)"
            )

        # Warnings
        if position_pct > 15.0 and not errors:
            warnings.append(f"仓位{position_pct:.1f}%较高，建议谨慎")

        valid = len(errors) == 0

        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
