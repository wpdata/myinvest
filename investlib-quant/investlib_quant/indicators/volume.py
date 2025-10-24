"""
Volume Pattern Analysis (T064)

Volume-based technical indicators and pattern recognition.
"""

import pandas as pd
import numpy as np
from typing import Optional
import logging


logger = logging.getLogger(__name__)


def calculate_volume_ma(
    df: pd.DataFrame,
    period: int = 20,
    volume_col: str = 'volume'
) -> pd.Series:
    """Calculate volume moving average.

    Args:
        df: DataFrame with volume data
        period: MA period (default 20)
        volume_col: Volume column name

    Returns:
        Volume MA series
    """
    return df[volume_col].rolling(window=period).mean()


def detect_volume_spike(
    current_volume: float,
    volume_ma: float,
    threshold: float = 1.5
) -> bool:
    """Detect volume spike.

    Args:
        current_volume: Current volume
        volume_ma: Volume moving average
        threshold: Spike threshold multiplier (default 1.5)

    Returns:
        True if volume spike detected
    """
    if pd.isna(volume_ma) or volume_ma == 0:
        return False

    ratio = current_volume / volume_ma

    if ratio >= threshold:
        logger.info(f"Volume spike: {ratio:.2f}x average")
        return True

    return False


def detect_volume_divergence(
    price_series: pd.Series,
    volume_series: pd.Series,
    lookback: int = 20
) -> bool:
    """Detect price-volume divergence.

    Args:
        price_series: Price series
        volume_series: Volume series
        lookback: Periods to analyze

    Returns:
        True if divergence detected
    """
    if len(price_series) < lookback or len(volume_series) < lookback:
        return False

    recent_price = price_series.tail(lookback)
    recent_volume = volume_series.tail(lookback)

    # Price trend
    price_trend = (recent_price.iloc[-1] - recent_price.iloc[0]) / recent_price.iloc[0]

    # Volume trend
    vol_ma_early = recent_volume[:10].mean()
    vol_ma_late = recent_volume[-10:].mean()
    volume_trend = (vol_ma_late - vol_ma_early) / vol_ma_early if vol_ma_early > 0 else 0

    # Divergence: price up but volume down (bearish)
    # or price down but volume down (bullish)
    if price_trend > 0.05 and volume_trend < -0.2:
        logger.info("Bearish divergence: Price up, volume down")
        return True
    elif price_trend < -0.05 and volume_trend < -0.2:
        logger.info("Bullish divergence: Price down, volume down")
        return True

    return False


# Example
if __name__ == '__main__':
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'close': 1900 + np.random.normal(0, 20, 100),
        'volume': np.random.randint(100000, 500000, 100)
    })

    vol_ma = calculate_volume_ma(df, period=20)
    spike = detect_volume_spike(df['volume'].iloc[-1], vol_ma.iloc[-1], threshold=1.5)
    print(f"成交量放大: {spike}")
