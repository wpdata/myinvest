"""
MyInvest V0.3 - Margin Calculator (T031)
Calculate margin requirements and forced liquidation prices for futures/options.
"""

import logging
from typing import Literal


logger = logging.getLogger(__name__)


class MarginCalculator:
    """Margin calculation for futures and options trading.

    Features:
    - Margin requirement calculation
    - Liquidation price calculation
    - Forced liquidation detection
    """

    def calculate_margin(
        self,
        contract_type: Literal['futures', 'option'],
        quantity: int,
        price: float,
        multiplier: int = 1,
        margin_rate: float = 0.15
    ) -> float:
        """Calculate margin requirement.

        Args:
            contract_type: 'futures' or 'option'
            quantity: Number of contracts
            price: Contract price
            multiplier: Contract multiplier (e.g., IF futures = 300)
            margin_rate: Margin rate (e.g., 0.15 = 15%)

        Returns:
            Required margin amount

        Example:
            >>> calc = MarginCalculator()
            >>> # IF2506 @ 5000, 1 contract, multiplier 300, margin 15%
            >>> margin = calc.calculate_margin('futures', 1, 5000, 300, 0.15)
            >>> # margin = 1 * 5000 * 300 * 0.15 = 225,000
        """
        contract_value = abs(quantity) * price * multiplier
        margin = contract_value * margin_rate

        logger.debug(
            f"[Margin] {contract_type}: qty={quantity}, price={price}, "
            f"multiplier={multiplier}, rate={margin_rate*100:.1f}% → margin=¥{margin:,.2f}"
        )

        return margin

    def calculate_liquidation_price(
        self,
        entry_price: float,
        direction: Literal['long', 'short'],
        margin_rate: float = 0.15,
        force_close_margin_rate: float = 0.10
    ) -> float:
        """Calculate forced liquidation price.

        When margin falls below force_close_margin_rate, position is liquidated.

        Args:
            entry_price: Position entry price
            direction: 'long' or 'short'
            margin_rate: Initial margin rate (e.g., 0.15)
            force_close_margin_rate: Forced liquidation threshold (e.g., 0.10)

        Returns:
            Liquidation price

        Formula:
            Long: liquidation_price = entry_price * (1 - (margin_rate - force_close_margin_rate))
            Short: liquidation_price = entry_price * (1 + (margin_rate - force_close_margin_rate))

        Example:
            >>> calc = MarginCalculator()
            >>> # Long @ 5000, margin 15%, force close 10%
            >>> liq_price = calc.calculate_liquidation_price(5000, 'long', 0.15, 0.10)
            >>> # liq_price = 5000 * (1 - 0.05) = 4750
        """
        margin_buffer = margin_rate - force_close_margin_rate

        if direction == 'long':
            liquidation_price = entry_price * (1 - margin_buffer)
        else:  # short
            liquidation_price = entry_price * (1 + margin_buffer)

        logger.debug(
            f"[Liquidation] {direction} @ {entry_price}: "
            f"margin={margin_rate*100:.1f}%, force_close={force_close_margin_rate*100:.1f}% "
            f"→ liquidation @ {liquidation_price:.2f}"
        )

        return liquidation_price

    def is_forced_liquidation(
        self,
        current_price: float,
        liquidation_price: float,
        direction: Literal['long', 'short']
    ) -> bool:
        """Check if position should be force-liquidated.

        Args:
            current_price: Current market price
            liquidation_price: Calculated liquidation price
            direction: 'long' or 'short'

        Returns:
            True if force liquidation triggered

        Logic:
            Long: liquidate if current_price <= liquidation_price
            Short: liquidate if current_price >= liquidation_price
        """
        if direction == 'long':
            triggered = current_price <= liquidation_price
        else:  # short
            triggered = current_price >= liquidation_price

        if triggered:
            logger.warning(
                f"[ForcedLiquidation] {direction} position liquidated: "
                f"current={current_price:.2f}, threshold={liquidation_price:.2f}"
            )

        return triggered

    def calculate_margin_ratio(
        self,
        account_equity: float,
        margin_used: float
    ) -> float:
        """Calculate current margin ratio.

        Args:
            account_equity: Current account equity (including unrealized P&L)
            margin_used: Total margin used

        Returns:
            Margin ratio (0-1), where 1 = 100% margin usage

        Example:
            >>> calc = MarginCalculator()
            >>> ratio = calc.calculate_margin_ratio(100000, 50000)
            >>> # ratio = 0.5 (50%)
        """
        if margin_used == 0:
            return 0.0

        ratio = margin_used / account_equity if account_equity > 0 else float('inf')

        return min(ratio, 1.0)  # Cap at 100%
