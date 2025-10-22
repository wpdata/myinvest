"""Moving Average calculations (T029)."""

import pandas as pd
from typing import Union, List


def calculate_ma(
    data: Union[pd.DataFrame, pd.Series],
    period: int = 60,
    periods: List[int] = None
) -> Union[pd.Series, pd.DataFrame]:
    """Calculate moving average(s).

    Args:
        data: DataFrame with 'close' column or Series of close prices
        period: Single MA period (default 60)
        periods: List of periods for multiple MAs (overrides period param)

    Returns:
        pandas Series (single period) or DataFrame (multiple periods) with MA values

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

    # Calculate single or multiple periods
    if periods is None:
        periods = [period]
        return_series = True
    else:
        return_series = False

    # Validate minimum rows
    max_period = max(periods)
    if len(close) < max_period:
        raise ValueError(f"Insufficient data: need at least {max_period} rows, got {len(close)}")

    # Calculate MAs
    if return_series:
        return close.rolling(window=periods[0]).mean()
    else:
        result = pd.DataFrame()
        for p in periods:
            result[f'ma_{p}'] = close.rolling(window=p).mean()
        return result
