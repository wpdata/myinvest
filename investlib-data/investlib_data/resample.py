"""
Weekly Data Resampling (T057)

Convert daily OHLCV data to weekly timeframe for multi-timeframe analysis.
"""

import pandas as pd
import numpy as np
from typing import Optional
import logging


logger = logging.getLogger(__name__)


def resample_to_weekly(
    daily_df: pd.DataFrame,
    week_start: str = 'MON'
) -> pd.DataFrame:
    """Resample daily OHLCV data to weekly.

    Args:
        daily_df: Daily DataFrame with columns:
            - timestamp: datetime
            - open, high, low, close: float
            - volume: float
        week_start: Week start day ('MON' or 'SUN')

    Returns:
        Weekly DataFrame with same schema

    Example:
        >>> daily_data = pd.DataFrame({
        ...     'timestamp': pd.date_range('2025-01-01', periods=100, freq='D'),
        ...     'open': np.random.uniform(1800, 1900, 100),
        ...     'high': np.random.uniform(1850, 1950, 100),
        ...     'low': np.random.uniform(1750, 1850, 100),
        ...     'close': np.random.uniform(1800, 1900, 100),
        ...     'volume': np.random.randint(100000, 500000, 100)
        ... })
        >>> weekly_data = resample_to_weekly(daily_data)
        >>> # Returns weekly bars with OHLC aggregation
    """
    if daily_df.empty:
        logger.warning("Empty DataFrame provided")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Ensure timestamp is datetime
    df = daily_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Set timestamp as index
    df = df.set_index('timestamp')

    # Sort by date
    df = df.sort_index()

    # Resample to weekly
    # Week starts on Monday by default (W-MON)
    # Use W-SUN for Sunday start
    freq = 'W-MON' if week_start == 'MON' else 'W-SUN'

    weekly = df.resample(freq).agg({
        'open': 'first',      # First open of the week
        'high': 'max',        # Highest high of the week
        'low': 'min',         # Lowest low of the week
        'close': 'last',      # Last close of the week
        'volume': 'sum'       # Total volume for the week
    })

    # Remove rows with NaN (weeks with no data)
    weekly = weekly.dropna()

    # Reset index to get timestamp back as column
    weekly = weekly.reset_index()

    logger.info(
        f"Resampled {len(df)} daily bars to {len(weekly)} weekly bars "
        f"(week starts on {week_start})"
    )

    return weekly


def resample_to_monthly(
    daily_df: pd.DataFrame
) -> pd.DataFrame:
    """Resample daily OHLCV data to monthly.

    Args:
        daily_df: Daily DataFrame

    Returns:
        Monthly DataFrame

    Example:
        >>> monthly_data = resample_to_monthly(daily_data)
    """
    if daily_df.empty:
        logger.warning("Empty DataFrame provided")
        return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    df = daily_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    df = df.set_index('timestamp').sort_index()

    # Resample to month end (M)
    monthly = df.resample('M').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })

    monthly = monthly.dropna().reset_index()

    logger.info(
        f"Resampled {len(daily_df)} daily bars to {len(monthly)} monthly bars"
    )

    return monthly


def align_timeframes(
    higher_tf_df: pd.DataFrame,
    lower_tf_df: pd.DataFrame
) -> pd.DataFrame:
    """Align higher timeframe data with lower timeframe for analysis.

    Adds higher timeframe values to each lower timeframe row.

    Args:
        higher_tf_df: Higher timeframe data (e.g., weekly)
        lower_tf_df: Lower timeframe data (e.g., daily)

    Returns:
        Lower timeframe DataFrame with higher TF columns added

    Example:
        >>> weekly_data = resample_to_weekly(daily_data)
        >>> aligned = align_timeframes(weekly_data, daily_data)
        >>> # aligned now has 'weekly_close', 'weekly_high', etc. columns
    """
    if higher_tf_df.empty or lower_tf_df.empty:
        logger.warning("One or both DataFrames are empty")
        return lower_tf_df

    # Ensure timestamps are datetime
    higher = higher_tf_df.copy()
    lower = lower_tf_df.copy()

    if not pd.api.types.is_datetime64_any_dtype(higher['timestamp']):
        higher['timestamp'] = pd.to_datetime(higher['timestamp'])
    if not pd.api.types.is_datetime64_any_dtype(lower['timestamp']):
        lower['timestamp'] = pd.to_datetime(lower['timestamp'])

    # Rename higher TF columns to indicate timeframe
    higher_renamed = higher.rename(columns={
        'open': 'weekly_open',
        'high': 'weekly_high',
        'low': 'weekly_low',
        'close': 'weekly_close',
        'volume': 'weekly_volume'
    })

    # Merge using asof (forward fill higher TF values)
    # Sort both by timestamp
    higher_renamed = higher_renamed.sort_values('timestamp')
    lower = lower.sort_values('timestamp')

    # Merge asof: for each lower TF timestamp, find the most recent higher TF timestamp
    aligned = pd.merge_asof(
        lower,
        higher_renamed,
        on='timestamp',
        direction='backward'
    )

    logger.info(
        f"Aligned {len(lower)} lower TF bars with {len(higher_renamed)} higher TF bars"
    )

    return aligned


# Example usage
if __name__ == '__main__':
    # Create sample daily data
    dates = pd.date_range(start='2024-01-01', end='2025-01-31', freq='D')
    np.random.seed(42)

    # Generate trending price data
    trend = np.linspace(1800, 2000, len(dates))
    noise = np.random.normal(0, 30, len(dates))
    close_prices = trend + noise

    daily_data = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.normal(0, 5, len(dates)),
        'high': close_prices + np.abs(np.random.normal(15, 5, len(dates))),
        'low': close_prices - np.abs(np.random.normal(15, 5, len(dates))),
        'close': close_prices,
        'volume': np.random.randint(100000, 500000, len(dates))
    })

    print("=" * 60)
    print("周线重采样测试")
    print("=" * 60)

    print(f"\n原始日线数据: {len(daily_data)} 条")
    print(daily_data.head(3))

    # Resample to weekly
    weekly_data = resample_to_weekly(daily_data, week_start='MON')

    print(f"\n周线数据: {len(weekly_data)} 条")
    print(weekly_data.head(3))

    # Resample to monthly
    monthly_data = resample_to_monthly(daily_data)

    print(f"\n月线数据: {len(monthly_data)} 条")
    print(monthly_data.head(3))

    # Align timeframes
    aligned_data = align_timeframes(weekly_data, daily_data)

    print(f"\n对齐后的日线数据（含周线指标）: {len(aligned_data)} 条")
    print(aligned_data[['timestamp', 'close', 'weekly_close']].head(10))

    # Verify weekly alignment
    print("\n验证周线对齐:")
    sample_week = aligned_data[aligned_data['timestamp'].dt.isocalendar().week == 2]
    if not sample_week.empty:
        print(f"第2周的所有日线数据都对应同一个周线收盘价: {sample_week['weekly_close'].unique()}")
