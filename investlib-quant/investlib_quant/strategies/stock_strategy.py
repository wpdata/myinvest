"""Stock-specific strategy base class (T034).

Extends BaseStrategy with stock-specific features:
- Full payment trading (no margin)
- Traditional position sizing
- Stop-loss and take-profit levels
"""

from abc import abstractmethod
from typing import Dict, Optional
import pandas as pd
import logging

from investlib_quant.strategies.base import BaseStrategy


class StockStrategy(BaseStrategy):
    """Stock strategy base class.

    Features:
    - Full payment required for positions
    - Position sizing based on capital percentage
    - Stop-loss and take-profit management
    - No margin or leverage
    """

    def __init__(
        self,
        name: str,
        max_position_size_pct: float = 20.0,  # Max 20% per position
        default_stop_loss_pct: float = 5.0,   # Default 5% stop-loss
        default_take_profit_pct: float = 15.0  # Default 15% take-profit
    ):
        """Initialize stock strategy.

        Args:
            name: Strategy name
            max_position_size_pct: Maximum position size as % of capital
            default_stop_loss_pct: Default stop-loss percentage
            default_take_profit_pct: Default take-profit percentage
        """
        super().__init__(name)
        self.max_position_size_pct = max_position_size_pct
        self.default_stop_loss_pct = default_stop_loss_pct
        self.default_take_profit_pct = default_take_profit_pct
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """Generate trading signal (must be implemented by subclass).

        Args:
            market_data: Market data DataFrame with OHLCV columns

        Returns:
            Signal dictionary with:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "entry_price": float,
                "stop_loss": float,
                "take_profit": float,
                "position_size_pct": float,  # 0-max_position_size_pct
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "reasoning": dict
            }
        """
        pass

    def calculate_position_size(
        self,
        capital: float,
        price: float,
        risk_pct: float = None
    ) -> int:
        """Calculate position size for stock purchase.

        Args:
            capital: Available capital
            price: Stock price
            risk_pct: Risk percentage (default: use max_position_size_pct)

        Returns:
            Number of shares to buy
        """
        risk_pct = risk_pct or self.max_position_size_pct
        position_value = capital * (risk_pct / 100)
        shares = int(position_value / price)

        # Round down to nearest 100 (standard lot size in Chinese market)
        shares = (shares // 100) * 100

        return max(100, shares)  # Minimum 100 shares (1 lot)

    def calculate_stop_loss(
        self,
        entry_price: float,
        stop_loss_pct: float = None
    ) -> float:
        """Calculate stop-loss price.

        Args:
            entry_price: Entry price
            stop_loss_pct: Stop-loss percentage (default: use default_stop_loss_pct)

        Returns:
            Stop-loss price
        """
        stop_loss_pct = stop_loss_pct or self.default_stop_loss_pct
        return entry_price * (1 - stop_loss_pct / 100)

    def calculate_take_profit(
        self,
        entry_price: float,
        take_profit_pct: float = None
    ) -> float:
        """Calculate take-profit price.

        Args:
            entry_price: Entry price
            take_profit_pct: Take-profit percentage (default: use default_take_profit_pct)

        Returns:
            Take-profit price
        """
        take_profit_pct = take_profit_pct or self.default_take_profit_pct
        return entry_price * (1 + take_profit_pct / 100)

    def validate_signal(self, signal: Dict) -> bool:
        """Validate signal structure.

        Args:
            signal: Signal dictionary

        Returns:
            True if valid
        """
        required_keys = ['action', 'entry_price']

        if not signal:
            return False

        for key in required_keys:
            if key not in signal:
                self.logger.warning(f"Signal missing required key: {key}")
                return False

        # Validate action
        if signal['action'] not in ['BUY', 'SELL', 'HOLD']:
            self.logger.warning(f"Invalid action: {signal['action']}")
            return False

        # Validate position size
        if 'position_size_pct' in signal:
            if signal['position_size_pct'] > self.max_position_size_pct:
                self.logger.warning(
                    f"Position size {signal['position_size_pct']}% exceeds max "
                    f"{self.max_position_size_pct}%"
                )
                signal['position_size_pct'] = self.max_position_size_pct

        return True

    def analyze_data(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        capital: float,
        metadata: Dict
    ) -> Optional[Dict]:
        """Analyze market data and generate trading signal.

        This method extends BaseStrategy.analyze_data() with stock-specific validation.

        Args:
            market_data: Market data DataFrame
            symbol: Stock symbol
            capital: Available capital
            metadata: Data metadata

        Returns:
            Signal dictionary or None
        """
        # Validate data
        if not self.validate_data(market_data, required_rows=20):
            self.logger.warning(f"Insufficient data for {symbol}")
            return None

        # Generate signal using strategy logic
        signal = self.generate_signal(market_data)

        # Validate signal
        if signal and not self.validate_signal(signal):
            return None

        # Skip HOLD signals
        if not signal or signal.get('action') == 'HOLD':
            return None

        # Add default stop-loss/take-profit if not provided
        if signal.get('action') == 'BUY':
            if 'stop_loss' not in signal:
                signal['stop_loss'] = self.calculate_stop_loss(signal['entry_price'])
            if 'take_profit' not in signal:
                signal['take_profit'] = self.calculate_take_profit(signal['entry_price'])

        return signal


class SimpleStockStrategy(StockStrategy):
    """Example: Simple moving average crossover stock strategy.

    BUY when MA20 crosses above MA60
    SELL when MA20 crosses below MA60
    """

    def __init__(self):
        super().__init__(
            name="SimpleMA",
            max_position_size_pct=15.0,
            default_stop_loss_pct=7.0,
            default_take_profit_pct=20.0
        )

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """Generate signal based on MA crossover."""
        if len(market_data) < 60:
            return None

        # Calculate moving averages
        ma20 = market_data['close'].rolling(20).mean()
        ma60 = market_data['close'].rolling(60).mean()

        # Get latest values
        current_ma20 = ma20.iloc[-1]
        current_ma60 = ma60.iloc[-1]
        prev_ma20 = ma20.iloc[-2]
        prev_ma60 = ma60.iloc[-2]

        current_price = market_data['close'].iloc[-1]

        # Bullish crossover
        if prev_ma20 <= prev_ma60 and current_ma20 > current_ma60:
            return {
                "action": "BUY",
                "entry_price": current_price,
                "position_size_pct": 15.0,
                "confidence": "MEDIUM",
                "reasoning": {
                    "signal_type": "MA_CROSSOVER_BULLISH",
                    "ma20": current_ma20,
                    "ma60": current_ma60
                }
            }

        # Bearish crossover
        if prev_ma20 >= prev_ma60 and current_ma20 < current_ma60:
            return {
                "action": "SELL",
                "entry_price": current_price,
                "confidence": "MEDIUM",
                "reasoning": {
                    "signal_type": "MA_CROSSOVER_BEARISH",
                    "ma20": current_ma20,
                    "ma60": current_ma60
                }
            }

        return {"action": "HOLD"}
