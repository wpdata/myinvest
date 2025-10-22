"""Livermore Trend-Following Strategy Implementation.

Implements Jesse Livermore's trend-following strategy with the following rules:
- BUY signal: Price breaks above 120-day MA + volume spike + MACD golden cross
- Stop-loss: 2x ATR below entry (for BUY) or above entry (for SELL)
- Position sizing: Risk 2% of capital per trade
- Take-profit: 3x risk (1:3 risk-reward ratio minimum)

V0.2 Update: Now uses real market data via MarketDataFetcher (US5 - T013)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from investlib_data.market_api import MarketDataFetcher, NoDataAvailableError


class LivermoreStrategy:
    """Livermore trend-following strategy analyzer with real data integration."""

    def __init__(
        self,
        ma_period: int = 120,
        volume_period: int = 20,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        atr_period: int = 14,
        risk_pct: float = 2.0,
        stop_loss_atr_multiple: float = 2.0,
        risk_reward_ratio: float = 3.0
    ):
        """Initialize strategy parameters.

        Args:
            ma_period: Moving average period (default 120 days)
            volume_period: Volume average period (default 20 days)
            macd_fast: MACD fast period (default 12)
            macd_slow: MACD slow period (default 26)
            macd_signal: MACD signal period (default 9)
            atr_period: ATR period for stop-loss (default 14)
            risk_pct: Risk percentage per trade (default 2%)
            stop_loss_atr_multiple: ATR multiple for stop-loss (default 2.0)
            risk_reward_ratio: Minimum risk-reward ratio (default 3.0)
        """
        self.ma_period = ma_period
        self.volume_period = volume_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.atr_period = atr_period
        self.risk_pct = risk_pct
        self.stop_loss_atr_multiple = stop_loss_atr_multiple
        self.risk_reward_ratio = risk_reward_ratio
        self.logger = logging.getLogger(__name__)

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators.

        Args:
            data: DataFrame with columns: timestamp, open, high, low, close, volume

        Returns:
            DataFrame with added indicator columns
        """
        df = data.copy()

        # 120-day moving average
        df['ma_120'] = df['close'].rolling(window=self.ma_period).mean()

        # Volume moving average
        df['volume_ma'] = df['volume'].rolling(window=self.volume_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # MACD
        ema_fast = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=self.macd_signal, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()

        return df

    def detect_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect trading signal from indicators.

        Args:
            df: DataFrame with calculated indicators

        Returns:
            Signal dictionary with action, confidence, and key factors
        """
        # Use latest data point
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest

        # Initialize signal
        action = 'HOLD'
        confidence = 'LOW'
        key_factors = []

        # Check for bullish breakout
        bullish_breakout = False
        if latest['close'] > latest['ma_120']:
            key_factors.append(f"Price ({latest['close']:.2f}) above 120-day MA ({latest['ma_120']:.2f})")
            bullish_breakout = True

        # Check for volume spike (>30% above average)
        volume_spike = False
        if latest['volume_ratio'] > 1.3:
            key_factors.append(f"Volume spike: {latest['volume_ratio']:.1f}x average")
            volume_spike = True

        # Check for MACD golden cross
        macd_golden_cross = False
        if latest['macd'] > latest['macd_signal'] and previous['macd'] <= previous['macd_signal']:
            key_factors.append("MACD golden cross detected")
            macd_golden_cross = True

        # Check for MACD momentum (positive or increasing)
        macd_positive = latest['macd'] > 0
        macd_increasing = latest['macd'] > previous['macd']

        # Determine action
        if bullish_breakout and volume_spike and macd_golden_cross:
            action = 'BUY'
            confidence = 'HIGH'
        elif bullish_breakout and volume_spike:
            action = 'BUY'
            confidence = 'MEDIUM'
            key_factors.append("Bullish breakout with volume confirmation")
        elif bullish_breakout and macd_positive:
            action = 'BUY'
            confidence = 'MEDIUM'
            key_factors.append("Bullish breakout with MACD support")
        elif latest['close'] < latest['ma_120'] and volume_spike:
            action = 'SELL'
            confidence = 'MEDIUM'
            key_factors.append(f"Price below 120-day MA, bearish signal")
        elif latest['close'] < latest['ma_120'] and latest['macd'] < 0:
            action = 'SELL'
            confidence = 'LOW'
            key_factors.append("Bearish trend detected")
        else:
            action = 'HOLD'
            confidence = 'LOW'
            key_factors.append("No strong trend detected, holding position")

        return {
            'action': action,
            'confidence': confidence,
            'key_factors': key_factors,
            'latest_price': latest['close'],
            'atr': latest['atr']
        }

    def calculate_risk_metrics(
        self,
        signal_data: Dict[str, Any],
        capital: float = 100000.0
    ) -> Dict[str, Any]:
        """Calculate risk metrics (stop-loss, take-profit, position size).

        Args:
            signal_data: Signal dictionary from detect_signal()
            capital: Total capital available (default 100,000)

        Returns:
            Risk metrics dictionary
        """
        action = signal_data['action']
        entry_price = signal_data['latest_price']
        atr = signal_data['atr']

        # Calculate stop-loss based on ATR
        if action in ['BUY', 'STRONG_BUY']:
            stop_loss = entry_price - (self.stop_loss_atr_multiple * atr)
            take_profit = entry_price + (self.risk_reward_ratio * (entry_price - stop_loss))
        elif action in ['SELL', 'STRONG_SELL']:
            stop_loss = entry_price + (self.stop_loss_atr_multiple * atr)
            take_profit = entry_price - (self.risk_reward_ratio * (stop_loss - entry_price))
        else:
            # HOLD: no position
            stop_loss = entry_price
            take_profit = entry_price

        # Calculate position size (risk 2% of capital)
        risk_per_trade = capital * (self.risk_pct / 100.0)
        price_risk = abs(entry_price - stop_loss)
        position_value = risk_per_trade / (price_risk / entry_price) if price_risk > 0 else 0
        position_size_pct = min((position_value / capital) * 100, 20.0)  # Cap at 20%

        # Calculate max loss
        max_loss_amount = (capital * position_size_pct / 100) * (price_risk / entry_price)

        return {
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'position_size_pct': round(position_size_pct, 2),
            'max_loss_amount': round(max_loss_amount, 2),
            'atr': round(atr, 2)
        }

    def analyze_data(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        capital: float = 100000.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze provided market data without fetching from API.

        This method is used by backtesting to avoid redundant API calls.

        Args:
            market_data: DataFrame with OHLCV data
            symbol: Stock symbol (for logging/output)
            capital: Total capital available (default: 100000)
            metadata: Optional metadata dict (for data provenance tracking)

        Returns:
            Complete signal dictionary with action, risk metrics, and data metadata

        Raises:
            ValueError: If insufficient data or missing required columns
        """
        # Use default metadata if not provided
        if metadata is None:
            metadata = {
                'api_source': 'Direct Data',
                'retrieval_timestamp': datetime.now(),
                'data_freshness': 'unknown'
            }

        # Validate input data
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in market_data.columns:
                raise ValueError(f"Missing required column: {col}")

        # Require minimum data points for indicators
        if len(market_data) < self.ma_period:
            raise ValueError(
                f"Insufficient data for {symbol}: need at least {self.ma_period} days, "
                f"got {len(market_data)} days."
            )

        # Calculate indicators
        df = self.calculate_indicators(market_data)

        # Detect signal
        signal_data = self.detect_signal(df)

        # Calculate risk metrics
        risk_metrics = self.calculate_risk_metrics(signal_data, capital)

        # Combine into complete signal with data metadata
        complete_signal = {
            'symbol': symbol,
            'action': signal_data['action'],
            'confidence': signal_data['confidence'],
            'key_factors': signal_data['key_factors'],
            **risk_metrics,
            # Data metadata
            'data_source': metadata.get('api_source', 'Unknown'),
            'data_timestamp': metadata['retrieval_timestamp'].isoformat() if isinstance(metadata.get('retrieval_timestamp'), datetime) else str(metadata.get('retrieval_timestamp', 'Unknown')),
            'data_freshness': metadata.get('data_freshness', 'unknown'),
            'data_points': len(market_data),
            'analysis_timestamp': datetime.now().isoformat()
        }

        return complete_signal

    def analyze(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        capital: float = 100000.0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Analyze market data and generate trading signal using real market data.

        V0.2 Update (T013): Now accepts symbol and fetches real data via MarketDataFetcher.

        Args:
            symbol: Stock symbol (e.g., '600519.SH' or '600519')
            start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            capital: Total capital available (default: 100000)
            use_cache: Whether to use cached data (default: True). Set False for --no-cache

        Returns:
            Complete signal dictionary with action, risk metrics, data metadata, and explainability

        Raises:
            ValueError: If insufficient data for analysis
            NoDataAvailableError: If all data sources fail
        """
        # Set default date range
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            # Need at least ma_period trading days + buffer for weekends/holidays
            # Request ~1.5x calendar days to ensure enough trading days
            days_needed = int(self.ma_period * 1.5 + 30)  # 120 * 1.5 + 30 = 210 days
            start_date = (datetime.now() - timedelta(days=days_needed)).strftime('%Y-%m-%d')

        # Fetch real data using MarketDataFetcher
        from investlib_data.cache_manager import CacheManager
        from investlib_data.database import SessionLocal

        cache_manager = None
        session = None
        if use_cache:
            try:
                session = SessionLocal()
                cache_manager = CacheManager(session=session)
            except Exception as e:
                self.logger.warning(f"Cache not available: {e}")

        fetcher = MarketDataFetcher(cache_manager=cache_manager)

        self.logger.info(f"[LivermoreStrategy] Fetching data for {symbol} from {start_date} to {end_date}")

        try:
            try:
                result = fetcher.fetch_with_fallback(symbol, start_date, end_date)
            except NoDataAvailableError as e:
                self.logger.error(f"[LivermoreStrategy] Failed to fetch data for {symbol}: {e}")
                raise

            market_data = result['data']
            metadata = result['metadata']

            # Log data provenance
            self.logger.info(
                f"[LivermoreStrategy] Analyzing {symbol} with data from {metadata['api_source']}, "
                f"retrieved at {metadata['retrieval_timestamp']}, freshness={metadata['data_freshness']}"
            )

            # Validate input data
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in market_data.columns:
                    raise ValueError(f"Missing required column: {col}")

            # Require minimum data points for indicators
            if len(market_data) < self.ma_period:
                raise ValueError(
                    f"Insufficient data for {symbol}: need at least {self.ma_period} days, "
                    f"got {len(market_data)} days. Try extending date range."
                )

            # Calculate indicators
            df = self.calculate_indicators(market_data)

            # Detect signal
            signal_data = self.detect_signal(df)

            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(signal_data, capital)

            # Combine into complete signal with data metadata (US5 - T013)
            complete_signal = {
                'symbol': symbol,
                'action': signal_data['action'],
                'confidence': signal_data['confidence'],
                'key_factors': signal_data['key_factors'],
                **risk_metrics,
                # Data metadata (NEW in V0.2)
                'data_source': metadata['api_source'],
                'data_timestamp': metadata['retrieval_timestamp'].isoformat() if isinstance(metadata['retrieval_timestamp'], datetime) else str(metadata['retrieval_timestamp']),
                'data_freshness': metadata['data_freshness'],
                'data_points': len(market_data),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return complete_signal
        finally:
            # CRITICAL: Close database session to prevent connection leaks
            if session:
                session.close()
                self.logger.debug("[LivermoreStrategy] Database session closed")
