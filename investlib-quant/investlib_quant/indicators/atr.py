"""ATR (Average True Range) calculation (T028)."""

import pandas as pd
import numpy as np
from typing import Union


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR indicator.

    Args:
        data: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)

    Returns:
        pandas Series with ATR values

    Raises:
        ValueError: If missing required columns or insufficient data
    """
    # Validate columns
    required_cols = ['high', 'low', 'close']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"DataFrame must have '{col}' column")

    # Validate minimum rows
    if len(data) < period + 1:
        raise ValueError(f"Insufficient data: need at least {period + 1} rows, got {len(data)}")

    # Use pandas_ta if available
    try:
        import pandas_ta as ta
        atr = ta.atr(data['high'], data['low'], data['close'], length=period)
    except ImportError:
        # Manual ATR calculation
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

    return atr
