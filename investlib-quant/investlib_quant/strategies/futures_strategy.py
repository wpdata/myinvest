"""Futures-specific strategy base class (T035).

Extends BaseStrategy with futures-specific features:
- Margin-based trading
- Leverage management
- Forced liquidation awareness
- Contract rollover handling
"""

from abc import abstractmethod
from typing import Dict, Optional
import pandas as pd
import logging

from investlib_quant.strategies.base import BaseStrategy


class FuturesStrategy(BaseStrategy):
    """Futures strategy base class.

    Features:
    - Margin-based position sizing
    - Leverage control
    - Forced liquidation risk management
    - Contract expiry awareness
    """

    def __init__(
        self,
        name: str,
        max_leverage: float = 3.0,           # Max 3x leverage
        margin_rate: float = 0.15,           # 15% margin requirement
        default_stop_loss_pct: float = 8.0,  # 8% stop-loss (tighter for futures)
        max_positions: int = 2               # Max 2 contracts simultaneously
    ):
        """Initialize futures strategy.

        Args:
            name: Strategy name
            max_leverage: Maximum leverage allowed
            margin_rate: Margin requirement (e.g., 0.15 = 15%)
            default_stop_loss_pct: Default stop-loss percentage
            max_positions: Maximum number of contracts to hold
        """
        super().__init__(name)
        self.max_leverage = max_leverage
        self.margin_rate = margin_rate
        self.default_stop_loss_pct = default_stop_loss_pct
        self.max_positions = max_positions
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
                "leverage": float,  # 1.0 to max_leverage
                "contracts": int,   # Number of contracts
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "reasoning": dict
            }
        """
        pass

    def calculate_margin_required(
        self,
        price: float,
        contracts: int,
        multiplier: int = 300
    ) -> float:
        """Calculate margin required for position.

        Args:
            price: Futures price
            contracts: Number of contracts
            multiplier: Contract multiplier (e.g., 300 for CSI 300 futures)

        Returns:
            Margin required (CNY)
        """
        from investlib_margin.calculator import MarginCalculator

        calc = MarginCalculator()
        return calc.calculate_margin(
            contract_type='futures',
            quantity=contracts,
            price=price,
            multiplier=multiplier,
            margin_rate=self.margin_rate
        )

    def calculate_liquidation_price(
        self,
        entry_price: float,
        direction: str = 'long',
        force_close_margin_rate: float = 0.03
    ) -> float:
        """Calculate forced liquidation price.

        Args:
            entry_price: Entry price
            direction: 'long' or 'short'
            force_close_margin_rate: Forced liquidation margin rate (default 3%)

        Returns:
            Liquidation price
        """
        from investlib_margin.calculator import MarginCalculator

        calc = MarginCalculator()
        return calc.calculate_liquidation_price(
            entry_price=entry_price,
            direction=direction,
            margin_rate=self.margin_rate,
            force_close_margin_rate=force_close_margin_rate
        )

    def calculate_position_size(
        self,
        capital: float,
        price: float,
        leverage: float = None,
        multiplier: int = 300
    ) -> int:
        """Calculate number of contracts to trade.

        Args:
            capital: Available capital
            price: Futures price
            leverage: Desired leverage (default: max_leverage)
            multiplier: Contract multiplier

        Returns:
            Number of contracts
        """
        leverage = min(leverage or self.max_leverage, self.max_leverage)

        # Total exposure = capital × leverage
        total_exposure = capital * leverage

        # Margin per contract
        margin_per_contract = price * multiplier * self.margin_rate

        # Number of contracts
        contracts = int(total_exposure / (price * multiplier))

        # Limit by max_positions
        contracts = min(contracts, self.max_positions)

        return max(1, contracts)  # Minimum 1 contract

    def validate_signal(self, signal: Dict) -> bool:
        """Validate futures signal structure.

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

        # Validate leverage
        if 'leverage' in signal:
            if signal['leverage'] > self.max_leverage:
                self.logger.warning(
                    f"Leverage {signal['leverage']}x exceeds max {self.max_leverage}x"
                )
                signal['leverage'] = self.max_leverage

        # Validate contracts
        if 'contracts' in signal:
            if signal['contracts'] > self.max_positions:
                self.logger.warning(
                    f"Contracts {signal['contracts']} exceeds max {self.max_positions}"
                )
                signal['contracts'] = self.max_positions

        return True

    def check_rollover_needed(
        self,
        symbol: str,
        current_date: pd.Timestamp
    ) -> bool:
        """Check if contract rollover is needed.

        Args:
            symbol: Futures symbol (e.g., 'IF2506.CFFEX')
            current_date: Current date

        Returns:
            True if rollover needed (within 5 days of expiry)
        """
        # Parse expiry from symbol (e.g., IF2506 = 2025-06)
        import re
        from datetime import datetime

        match = re.match(r'^([A-Z]+)(\d{4})', symbol.split('.')[0])
        if not match:
            return False

        date_str = match.group(2)  # e.g., "2506"
        year = 2000 + int(date_str[:2])  # 25 -> 2025
        month = int(date_str[2:])         # 06 -> 6

        # Expiry is third Friday of the month
        expiry_date = self._get_third_friday(year, month)

        # Check if within 5 days
        days_to_expiry = (expiry_date - current_date).days
        return 0 < days_to_expiry <= 5

    def _get_third_friday(self, year: int, month: int) -> pd.Timestamp:
        """Get third Friday of the month."""
        import calendar
        from datetime import datetime

        # Find first Friday
        first_day = datetime(year, month, 1)
        first_friday_offset = (4 - first_day.weekday()) % 7
        first_friday = 1 + first_friday_offset

        # Third Friday is 14 days later
        third_friday = first_friday + 14

        return pd.Timestamp(datetime(year, month, third_friday))

    def analyze_data(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        capital: float,
        metadata: Dict
    ) -> Optional[Dict]:
        """Analyze market data and generate trading signal.

        Extends BaseStrategy.analyze_data() with futures-specific features:
        - Margin calculation
        - Liquidation price calculation
        - Rollover check

        Args:
            market_data: Market data DataFrame
            symbol: Futures symbol
            capital: Available capital
            metadata: Data metadata

        Returns:
            Signal dictionary or None
        """
        # Validate data
        if not self.validate_data(market_data, required_rows=30):
            self.logger.warning(f"Insufficient data for {symbol}")
            return None

        # Check rollover
        current_date = pd.to_datetime(market_data['timestamp'].iloc[-1])
        if self.check_rollover_needed(symbol, current_date):
            self.logger.warning(
                f"Contract {symbol} near expiry - consider rolling over"
            )

        # Generate signal
        signal = self.generate_signal(market_data)

        # Validate signal
        if signal and not self.validate_signal(signal):
            return None

        # Skip HOLD signals
        if not signal or signal.get('action') == 'HOLD':
            return None

        # Add margin and liquidation info for BUY signals
        if signal.get('action') == 'BUY':
            entry_price = signal['entry_price']

            # Add stop-loss if not provided
            if 'stop_loss' not in signal:
                signal['stop_loss'] = self.calculate_stop_loss(entry_price)

            # Add liquidation price
            signal['liquidation_price'] = self.calculate_liquidation_price(
                entry_price=entry_price,
                direction='long'
            )

            # Add margin info
            multiplier = self._get_multiplier(symbol)
            contracts = signal.get('contracts', 1)
            signal['margin_required'] = self.calculate_margin_required(
                price=entry_price,
                contracts=contracts,
                multiplier=multiplier
            )

        return signal

    def calculate_stop_loss(self, entry_price: float) -> float:
        """Calculate stop-loss price for futures."""
        return entry_price * (1 - self.default_stop_loss_pct / 100)

    def _get_multiplier(self, symbol: str) -> int:
        """Get contract multiplier from symbol."""
        if symbol.startswith('IF') or symbol.startswith('IC') or symbol.startswith('IH'):
            return 300  # Stock index futures
        else:
            return 100  # Commodity futures (default)


class SimpleTrendFuturesStrategy(FuturesStrategy):
    """Example: Simple trend-following futures strategy.

    BUY when price > MA20 and MA20 > MA60
    SELL when price < MA20 or MA20 < MA60
    """

    def __init__(self):
        super().__init__(
            name="SimpleTrendFutures",
            max_leverage=2.0,
            margin_rate=0.15,
            default_stop_loss_pct=10.0,
            max_positions=1
        )

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """Generate signal based on trend."""
        if len(market_data) < 60:
            return None

        # Calculate moving averages
        ma20 = market_data['close'].rolling(20).mean()
        ma60 = market_data['close'].rolling(60).mean()

        current_price = market_data['close'].iloc[-1]
        current_ma20 = ma20.iloc[-1]
        current_ma60 = ma60.iloc[-1]

        # Strong uptrend: price > MA20 > MA60
        if current_price > current_ma20 > current_ma60:
            return {
                "action": "BUY",
                "entry_price": current_price,
                "leverage": 2.0,
                "contracts": 1,
                "confidence": "HIGH",
                "reasoning": {
                    "signal_type": "TREND_BULLISH",
                    "ma20": current_ma20,
                    "ma60": current_ma60
                }
            }

        # Trend broken or bearish
        if current_price < current_ma20 or current_ma20 < current_ma60:
            return {
                "action": "SELL",
                "entry_price": current_price,
                "confidence": "MEDIUM",
                "reasoning": {
                    "signal_type": "TREND_BROKEN",
                    "ma20": current_ma20,
                    "ma60": current_ma60
                }
            }

        return {"action": "HOLD"}
