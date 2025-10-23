"""Options-specific strategy base class (T036).

Extends BaseStrategy with options-specific features:
- Greeks-based analysis (Delta, Gamma, Vega, Theta)
- Strike selection
- Expiry management
- Implied volatility analysis
"""

from abc import abstractmethod
from typing import Dict, Optional, Literal
import pandas as pd
import logging
from datetime import datetime, timedelta

from investlib_quant.strategies.base import BaseStrategy


class OptionsStrategy(BaseStrategy):
    """Options strategy base class.

    Features:
    - Greeks calculation and monitoring
    - Strike price selection
    - Expiry date management
    - Volatility-based trading
    """

    def __init__(
        self,
        name: str,
        target_delta: float = 0.5,           # Target delta for options
        max_theta_decay: float = -0.10,      # Max acceptable theta decay
        min_days_to_expiry: int = 15,        # Min days before expiry
        max_position_contracts: int = 10     # Max contracts per position
    ):
        """Initialize options strategy.

        Args:
            name: Strategy name
            target_delta: Target delta for option selection
            max_theta_decay: Maximum acceptable daily theta decay
            min_days_to_expiry: Minimum days to expiry (avoid near-expiry)
            max_position_contracts: Maximum contracts per position
        """
        super().__init__(name)
        self.target_delta = target_delta
        self.max_theta_decay = max_theta_decay
        self.min_days_to_expiry = min_days_to_expiry
        self.max_position_contracts = max_position_contracts
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """Generate trading signal (must be implemented by subclass).

        Args:
            market_data: Underlying asset market data

        Returns:
            Signal dictionary with:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "option_type": "call" | "put",
                "strike_price": float,
                "expiry_date": str,  # YYYY-MM-DD
                "contracts": int,
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "reasoning": dict,
                "greeks": {
                    "delta": float,
                    "gamma": float,
                    "vega": float,
                    "theta": float
                }
            }
        """
        pass

    def calculate_greeks(
        self,
        spot_price: float,
        strike_price: float,
        days_to_expiry: int,
        volatility: float = 0.20,
        option_type: Literal['call', 'put'] = 'call',
        risk_free_rate: float = 0.03
    ) -> Dict[str, float]:
        """Calculate option Greeks.

        Args:
            spot_price: Current underlying price
            strike_price: Option strike price
            days_to_expiry: Days until expiry
            volatility: Implied volatility (default 20%)
            option_type: 'call' or 'put'
            risk_free_rate: Risk-free rate (default 3%)

        Returns:
            Dictionary with delta, gamma, vega, theta, rho
        """
        try:
            from investlib_greeks.calculator import OptionsGreeksCalculator

            calc = OptionsGreeksCalculator()
            T = days_to_expiry / 365.0  # Convert to years

            greeks = calc.calculate_greeks(
                S=spot_price,
                K=strike_price,
                T=T,
                r=risk_free_rate,
                sigma=volatility,
                option_type=option_type
            )

            return greeks

        except ImportError:
            self.logger.warning("investlib-greeks not available, using simplified Greeks")
            # Simplified Greeks
            return {
                'delta': 0.5 if option_type == 'call' else -0.5,
                'gamma': 0.0,
                'vega': 0.0,
                'theta': 0.0,
                'rho': 0.0
            }

    def select_strike_price(
        self,
        spot_price: float,
        option_type: Literal['call', 'put'],
        target_delta: float = None
    ) -> float:
        """Select optimal strike price based on target delta.

        Args:
            spot_price: Current underlying price
            option_type: 'call' or 'put'
            target_delta: Target delta (default: use self.target_delta)

        Returns:
            Recommended strike price
        """
        target_delta = target_delta or self.target_delta

        # ATM (at-the-money) has delta ~0.5 for calls, ~-0.5 for puts
        # OTM (out-of-the-money) has lower absolute delta
        # ITM (in-the-money) has higher absolute delta

        if option_type == 'call':
            if abs(target_delta) < 0.3:
                # OTM call: strike above spot
                return spot_price * 1.05  # 5% OTM
            elif abs(target_delta) > 0.7:
                # ITM call: strike below spot
                return spot_price * 0.95  # 5% ITM
            else:
                # ATM call
                return spot_price
        else:  # put
            if abs(target_delta) < 0.3:
                # OTM put: strike below spot
                return spot_price * 0.95  # 5% OTM
            elif abs(target_delta) > 0.7:
                # ITM put: strike above spot
                return spot_price * 1.05  # 5% ITM
            else:
                # ATM put
                return spot_price

    def select_expiry_date(
        self,
        current_date: datetime,
        min_days: int = None,
        preferred_tenor_days: int = 30
    ) -> str:
        """Select option expiry date.

        Args:
            current_date: Current date
            min_days: Minimum days to expiry (default: use self.min_days_to_expiry)
            preferred_tenor_days: Preferred tenor in days (default: 30)

        Returns:
            Expiry date as YYYY-MM-DD string
        """
        min_days = min_days or self.min_days_to_expiry

        # Calculate target expiry
        target_expiry = current_date + timedelta(days=preferred_tenor_days)

        # Find third Friday of target month (standard expiry)
        year = target_expiry.year
        month = target_expiry.month

        # Find first Friday
        first_day = datetime(year, month, 1)
        first_friday_offset = (4 - first_day.weekday()) % 7
        first_friday = 1 + first_friday_offset

        # Third Friday
        third_friday = first_friday + 14
        expiry_date = datetime(year, month, third_friday)

        # Ensure minimum days
        if (expiry_date - current_date).days < min_days:
            # Move to next month
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

            first_day = datetime(year, month, 1)
            first_friday_offset = (4 - first_day.weekday()) % 7
            first_friday = 1 + first_friday_offset
            third_friday = first_friday + 14
            expiry_date = datetime(year, month, third_friday)

        return expiry_date.strftime('%Y-%m-%d')

    def check_expiry_warning(
        self,
        expiry_date: str,
        current_date: datetime
    ) -> bool:
        """Check if option is near expiry.

        Args:
            expiry_date: Option expiry date (YYYY-MM-DD)
            current_date: Current date

        Returns:
            True if within warning threshold (near expiry)
        """
        expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
        days_to_expiry = (expiry_dt - current_date).days

        return days_to_expiry <= self.min_days_to_expiry

    def validate_signal(self, signal: Dict) -> bool:
        """Validate options signal structure.

        Args:
            signal: Signal dictionary

        Returns:
            True if valid
        """
        required_keys = ['action']

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

        # For BUY signals, validate option-specific fields
        if signal['action'] == 'BUY':
            if 'option_type' not in signal:
                self.logger.warning("BUY signal missing option_type")
                return False

            if signal['option_type'] not in ['call', 'put']:
                self.logger.warning(f"Invalid option_type: {signal['option_type']}")
                return False

            # Validate contracts
            if 'contracts' in signal:
                if signal['contracts'] > self.max_position_contracts:
                    self.logger.warning(
                        f"Contracts {signal['contracts']} exceeds max {self.max_position_contracts}"
                    )
                    signal['contracts'] = self.max_position_contracts

            # Validate theta
            if 'greeks' in signal and 'theta' in signal['greeks']:
                if signal['greeks']['theta'] < self.max_theta_decay:
                    self.logger.warning(
                        f"Theta {signal['greeks']['theta']:.3f} exceeds max decay "
                        f"{self.max_theta_decay:.3f}"
                    )

        return True

    def analyze_data(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        capital: float,
        metadata: Dict
    ) -> Optional[Dict]:
        """Analyze market data and generate trading signal.

        Extends BaseStrategy.analyze_data() with options-specific features.

        Args:
            market_data: Underlying asset market data
            symbol: Underlying symbol
            capital: Available capital
            metadata: Data metadata

        Returns:
            Signal dictionary or None
        """
        # Validate data
        if not self.validate_data(market_data, required_rows=20):
            self.logger.warning(f"Insufficient data for {symbol}")
            return None

        # Generate signal
        signal = self.generate_signal(market_data)

        # Validate signal
        if signal and not self.validate_signal(signal):
            return None

        # Skip HOLD signals
        if not signal or signal.get('action') == 'HOLD':
            return None

        # Add Greeks if not provided
        if signal.get('action') == 'BUY' and 'greeks' not in signal:
            current_price = market_data['close'].iloc[-1]
            strike_price = signal.get('strike_price', current_price)
            option_type = signal.get('option_type', 'call')

            # Get expiry
            if 'expiry_date' in signal:
                expiry_dt = datetime.strptime(signal['expiry_date'], '%Y-%m-%d')
                current_dt = datetime.strptime(
                    str(market_data['timestamp'].iloc[-1])[:10],
                    '%Y-%m-%d'
                )
                days_to_expiry = (expiry_dt - current_dt).days
            else:
                days_to_expiry = 30  # Default

            # Calculate Greeks
            signal['greeks'] = self.calculate_greeks(
                spot_price=current_price,
                strike_price=strike_price,
                days_to_expiry=days_to_expiry,
                option_type=option_type
            )

        return signal


class SimpleVolatilityOptionsStrategy(OptionsStrategy):
    """Example: Simple volatility-based options strategy.

    BUY calls when volatility is low and price trending up
    BUY puts when volatility is low and price trending down
    """

    def __init__(self):
        super().__init__(
            name="SimpleVolOptions",
            target_delta=0.5,
            max_theta_decay=-0.15,
            min_days_to_expiry=20,
            max_position_contracts=5
        )

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """Generate signal based on volatility and trend."""
        if len(market_data) < 30:
            return None

        # Calculate historical volatility
        returns = market_data['close'].pct_change()
        vol_20 = returns.rolling(20).std() * (252 ** 0.5)  # Annualized

        current_price = market_data['close'].iloc[-1]
        current_vol = vol_20.iloc[-1]

        # Calculate trend
        ma10 = market_data['close'].rolling(10).mean()
        ma20 = market_data['close'].rolling(20).mean()

        current_ma10 = ma10.iloc[-1]
        current_ma20 = ma20.iloc[-1]

        # Current date
        current_date = datetime.strptime(
            str(market_data['timestamp'].iloc[-1])[:10],
            '%Y-%m-%d'
        )

        # Low volatility + uptrend = BUY call
        if current_vol < 0.25 and current_ma10 > current_ma20:
            strike = self.select_strike_price(current_price, 'call', target_delta=0.5)
            expiry = self.select_expiry_date(current_date, preferred_tenor_days=30)

            return {
                "action": "BUY",
                "option_type": "call",
                "strike_price": strike,
                "expiry_date": expiry,
                "contracts": 2,
                "confidence": "MEDIUM",
                "reasoning": {
                    "signal_type": "VOL_CALL",
                    "volatility": current_vol,
                    "trend": "BULLISH"
                }
            }

        # Low volatility + downtrend = BUY put
        if current_vol < 0.25 and current_ma10 < current_ma20:
            strike = self.select_strike_price(current_price, 'put', target_delta=-0.5)
            expiry = self.select_expiry_date(current_date, preferred_tenor_days=30)

            return {
                "action": "BUY",
                "option_type": "put",
                "strike_price": strike,
                "expiry_date": expiry,
                "contracts": 2,
                "confidence": "MEDIUM",
                "reasoning": {
                    "signal_type": "VOL_PUT",
                    "volatility": current_vol,
                    "trend": "BEARISH"
                }
            }

        return {"action": "HOLD"}
