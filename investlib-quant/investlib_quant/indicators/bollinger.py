"""
Bollinger Bands Indicator (T063)

Bollinger Bands - volatility bands around a moving average.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Literal
import logging


logger = logging.getLogger(__name__)


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
    price_col: str = 'close'
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands.

    Args:
        df: DataFrame with price data
        period: Moving average period (default 20)
        std_dev: Standard deviation multiplier (default 2.0)
        price_col: Price column name (default 'close')

    Returns:
        Tuple of (upper_band, middle_band, lower_band)

    Formula:
        Middle Band = SMA(period)
        Upper Band = Middle Band + (std_dev * std)
        Lower Band = Middle Band - (std_dev * std)

    Example:
        >>> upper, middle, lower = calculate_bollinger_bands(df, period=20, std_dev=2)
    """
    if price_col not in df.columns:
        raise ValueError(f"Column '{price_col}' not found")

    prices = df[price_col]

    # Calculate middle band (SMA)
    middle_band = prices.rolling(window=period).mean()

    # Calculate standard deviation
    rolling_std = prices.rolling(window=period).std()

    # Calculate upper and lower bands
    upper_band = middle_band + (rolling_std * std_dev)
    lower_band = middle_band - (rolling_std * std_dev)

    logger.debug(f"Calculated Bollinger Bands (period={period}, std={std_dev})")

    return upper_band, middle_band, lower_band


def detect_bollinger_signal(
    price: float,
    upper_band: float,
    lower_band: float,
    middle_band: float
) -> Optional[Literal['overbought', 'oversold', 'squeeze']]:
    """Detect Bollinger Band signals.

    Args:
        price: Current price
        upper_band: Upper band value
        lower_band: Lower band value
        middle_band: Middle band value

    Returns:
        'overbought' | 'oversold' | 'squeeze' | None

    Signals:
        - oversold: Price touches/breaks below lower band (buy signal)
        - overbought: Price touches/breaks above upper band (sell signal)
        - squeeze: Price near middle band (consolidation)

    Example:
        >>> signal = detect_bollinger_signal(1850, 1900, 1800, 1850)
    """
    if any(pd.isna([price, upper_band, lower_band, middle_band])):
        return None

    band_width = upper_band - lower_band
    threshold = band_width * 0.05  # 5% of band width

    # Oversold: price at or below lower band
    if price <= lower_band + threshold:
        logger.info(f"Bollinger oversold: Price={price:.2f}, Lower={lower_band:.2f}")
        return 'oversold'

    # Overbought: price at or above upper band
    elif price >= upper_band - threshold:
        logger.info(f"Bollinger overbought: Price={price:.2f}, Upper={upper_band:.2f}")
        return 'overbought'

    # Squeeze: price near middle band
    elif abs(price - middle_band) < threshold:
        return 'squeeze'

    return None


def calculate_bandwidth(
    upper_band: pd.Series,
    lower_band: pd.Series,
    middle_band: pd.Series
) -> pd.Series:
    """Calculate Bollinger Band width (volatility indicator).

    Args:
        upper_band: Upper band series
        lower_band: Lower band series
        middle_band: Middle band series

    Returns:
        Band width percentage

    Example:
        >>> bw = calculate_bandwidth(upper, lower, middle)
        >>> # Low BW indicates low volatility (potential breakout)
    """
    bandwidth = ((upper_band - lower_band) / middle_band) * 100
    return bandwidth


# Example usage
if __name__ == '__main__':
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    close = 1900 + 50 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 15, 100)

    df = pd.DataFrame({'timestamp': dates, 'close': close})

    upper, middle, lower = calculate_bollinger_bands(df, period=20, std_dev=2)

    print("Bollinger Bands (最近5天):")
    bb_df = pd.DataFrame({
        'Date': df['timestamp'].tail(5),
        'Close': df['close'].tail(5),
        'Upper': upper.tail(5),
        'Middle': middle.tail(5),
        'Lower': lower.tail(5)
    })
    print(bb_df.to_string(index=False))

    signal = detect_bollinger_signal(
        df['close'].iloc[-1],
        upper.iloc[-1],
        lower.iloc[-1],
        middle.iloc[-1]
    )
    print(f"\n信号: {signal if signal else '无'}")
