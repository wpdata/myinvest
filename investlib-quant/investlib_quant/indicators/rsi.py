"""RSI (Relative Strength Index) calculation (T027)."""

import pandas as pd
from typing import Union


def calculate_rsi(data: Union[pd.DataFrame, pd.Series], period: int = 14) -> pd.Series:
    """Calculate RSI indicator.

    Args:
        data: DataFrame with 'close' column or Series of close prices
        period: RSI period (default 14)

    Returns:
        pandas Series with RSI values (0-100 range)

    Raises:
        ValueError: If insufficient data or missing columns
    """
    # Extract close prices
    if isinstance(data, pd.DataFrame):
        if 'close' not in data.columns:
            raise ValueError("DataFrame must have 'close' column")
        close = data['close']
    else:
        close = data

    # Validate minimum rows
    if len(close) < period + 1:
        raise ValueError(f"Insufficient data: need at least {period + 1} rows, got {len(close)}")

    # Use pandas_ta if available, otherwise manual calculation
    try:
        import pandas_ta as ta
        rsi = ta.rsi(close, length=period)
    except ImportError:
        # Manual RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

    return rsi
