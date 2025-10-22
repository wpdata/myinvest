"""Signal Generator integrating strategy analysis and risk management.

Combines:
- LivermoreStrategy for market signal detection
- RiskCalculator for position sizing and risk metrics
- Validates all signals include mandatory safety fields
"""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from investlib_quant.livermore_strategy import LivermoreStrategy
from investlib_quant.risk_calculator import RiskCalculator


class SignalGenerator:
    """Generate trading signals with complete risk management."""

    def __init__(
        self,
        strategy: Optional[LivermoreStrategy] = None,
        risk_calculator: Optional[RiskCalculator] = None
    ):
        """Initialize signal generator with strategy and risk calculator.

        Args:
            strategy: LivermoreStrategy instance (creates default if None)
            risk_calculator: RiskCalculator instance (creates default if None)
        """
        self.strategy = strategy or LivermoreStrategy()
        self.risk_calculator = risk_calculator or RiskCalculator()

    def generate_trading_signal(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        capital: float = 100000.0,
        current_allocation_pct: float = 0.0
    ) -> Dict[str, Any]:
        """Generate complete trading signal with risk management.

        This is the main entry point that:
        1. Analyzes market data using Livermore strategy
        2. Calculates ATR-based stop-loss and take-profit
        3. Sizes position using risk calculator
        4. Validates all safety requirements
        5. Returns structured signal with metadata

        Args:
            symbol: Stock/futures symbol (e.g., "600519.SH")
            market_data: DataFrame with OHLCV data
            capital: Total available capital
            current_allocation_pct: Current portfolio allocation %

        Returns:
            Complete trading signal dictionary

        Raises:
            ValueError: If signal validation fails (e.g., missing stop-loss)
        """
        # 1. Analyze market data with strategy
        strategy_signal = self.strategy.analyze(market_data, capital)

        # 2. Validate strategy signal has mandatory fields
        self._validate_strategy_signal(strategy_signal)

        # 3. Calculate comprehensive risk metrics
        risk_metrics = self.risk_calculator.calculate_risk_metrics(
            capital=capital,
            entry_price=strategy_signal['entry_price'],
            stop_loss=strategy_signal['stop_loss'],
            take_profit=strategy_signal['take_profit'],
            position_size_pct=strategy_signal['position_size_pct'],
            current_allocation_pct=current_allocation_pct
        )

        # 4. Build complete signal
        complete_signal = {
            # Core signal fields
            "symbol": symbol,
            "action": strategy_signal['action'],
            "confidence": strategy_signal['confidence'],

            # Price levels
            "entry_price": strategy_signal['entry_price'],
            "stop_loss": strategy_signal['stop_loss'],
            "take_profit": strategy_signal['take_profit'],

            # Position sizing
            "position_size_pct": risk_metrics['position_size_pct'],
            "position_value": risk_metrics['position_value'],

            # Risk metrics
            "max_loss": risk_metrics['max_loss'],
            "max_gain": risk_metrics['max_gain'],
            "risk_reward_ratio": risk_metrics['risk_reward_ratio'],

            # Validation
            "validation": risk_metrics['validation'],

            # Explainability
            "key_factors": strategy_signal['key_factors'],
            "strategy_name": "Livermore Trend Following",

            # Metadata
            "generated_at": datetime.utcnow().isoformat(),
            "market_data_points": len(market_data),
            "atr": strategy_signal.get('atr', 0)
        }

        # 5. Final validation
        if not complete_signal['validation']['valid']:
            # Signal is technically valid but position limits exceeded
            # Return signal with validation errors for user decision
            pass

        return complete_signal

    def _validate_strategy_signal(self, signal: Dict[str, Any]) -> None:
        """Validate strategy signal has all mandatory fields.

        Per Constitution Principle VIII (Investment Safety):
        - Stop-loss is MANDATORY and must be present
        - Entry, take-profit, position size must be present

        Args:
            signal: Strategy signal dictionary

        Raises:
            ValueError: If any mandatory field is missing or invalid
        """
        # Check mandatory fields
        required_fields = [
            'action', 'entry_price', 'stop_loss', 'take_profit',
            'position_size_pct', 'confidence', 'key_factors'
        ]

        for field in required_fields:
            if field not in signal:
                raise ValueError(f"Strategy signal missing mandatory field: {field}")
            if signal[field] is None:
                raise ValueError(f"Strategy signal field '{field}' cannot be None")

        # Special validation: stop-loss must be present (Constitution requirement)
        if signal['stop_loss'] <= 0:
            raise ValueError(
                "Invalid stop-loss: must be positive (Constitution Principle VIII)"
            )

        # Validate stop-loss logic
        action = signal['action']
        entry = signal['entry_price']
        stop = signal['stop_loss']

        if action in ['BUY', 'STRONG_BUY']:
            if stop >= entry:
                raise ValueError(
                    f"Invalid stop-loss for BUY: {stop} must be below entry {entry}"
                )
        elif action in ['SELL', 'STRONG_SELL']:
            if stop <= entry:
                raise ValueError(
                    f"Invalid stop-loss for SELL: {stop} must be above entry {entry}"
                )

    def generate_signals_batch(
        self,
        symbols: list,
        market_data_dict: Dict[str, pd.DataFrame],
        capital: float = 100000.0,
        current_allocation_pct: float = 0.0
    ) -> Dict[str, Dict[str, Any]]:
        """Generate signals for multiple symbols.

        Args:
            symbols: List of symbols to analyze
            market_data_dict: Dictionary mapping symbol to market data DataFrame
            capital: Total available capital
            current_allocation_pct: Current portfolio allocation %

        Returns:
            Dictionary mapping symbol to signal (or error message)
        """
        signals = {}

        for symbol in symbols:
            try:
                if symbol not in market_data_dict:
                    signals[symbol] = {
                        "error": f"No market data available for {symbol}"
                    }
                    continue

                signal = self.generate_trading_signal(
                    symbol=symbol,
                    market_data=market_data_dict[symbol],
                    capital=capital,
                    current_allocation_pct=current_allocation_pct
                )
                signals[symbol] = signal

            except Exception as e:
                signals[symbol] = {
                    "error": str(e),
                    "symbol": symbol
                }

        return signals
