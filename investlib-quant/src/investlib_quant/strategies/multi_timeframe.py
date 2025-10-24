"""
Multi-Timeframe Strategy (T059)

Combine weekly trend analysis with daily entry signals.
Only trade when weekly trend aligns with daily signal.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
from .base import StockStrategy
import logging


logger = logging.getLogger(__name__)


class MultiTimeframeStrategy(StockStrategy):
    """多时间框架策略 - 周线趋势 + 日线入场.

    Strategy Logic:
        1. Check weekly trend (up/down/sideways)
        2. Generate daily entry signal
        3. Only execute trade when both align:
           - BUY: Weekly uptrend + Daily bullish signal
           - SELL: Weekly downtrend + Daily bearish signal
           - HOLD: Misaligned signals

    Parameters:
        - weekly_ma_short: Weekly short MA period (default 10 weeks)
        - weekly_ma_long: Weekly long MA period (default 20 weeks)
        - daily_ma_fast: Daily fast MA period (default 5 days)
        - daily_ma_slow: Daily slow MA period (default 20 days)
        - stop_loss_pct: Stop loss percentage (default 5%)
        - take_profit_pct: Take profit percentage (default 10%)
    """

    def __init__(
        self,
        name: str = "多时间框架策略",
        weekly_ma_short: int = 10,
        weekly_ma_long: int = 20,
        daily_ma_fast: int = 5,
        daily_ma_slow: int = 20,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10
    ):
        """Initialize multi-timeframe strategy.

        Args:
            name: Strategy name
            weekly_ma_short: Weekly short MA period
            weekly_ma_long: Weekly long MA period
            daily_ma_fast: Daily fast MA period
            daily_ma_slow: Daily slow MA period
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
        """
        super().__init__(name)
        self.weekly_ma_short = weekly_ma_short
        self.weekly_ma_long = weekly_ma_long
        self.daily_ma_fast = daily_ma_fast
        self.daily_ma_slow = daily_ma_slow
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """Generate trading signal using multi-timeframe analysis.

        Args:
            market_data: Daily market data with 'weekly_*' columns added

        Returns:
            Signal dict or None

        Note:
            market_data should have weekly indicators already aligned.
            Use align_timeframes() from resample.py to prepare data.
        """
        # Validate data
        required_daily_rows = max(self.daily_ma_slow, 20)
        if not self.validate_data(market_data, required_rows=required_daily_rows):
            return None

        # Check if weekly data is present
        if 'weekly_close' not in market_data.columns:
            logger.warning(
                "Weekly data not found in market_data. "
                "Use align_timeframes() to add weekly indicators."
            )
            # Fall back to daily-only analysis
            return self._generate_daily_signal(market_data)

        # Step 1: Check weekly trend
        weekly_trend = self._check_weekly_trend(market_data)

        # Step 2: Generate daily signal
        daily_signal = self._generate_daily_signal(market_data)

        # Step 3: Combine signals
        final_signal = self._combine_signals(weekly_trend, daily_signal)

        return final_signal

    def _check_weekly_trend(self, market_data: pd.DataFrame) -> str:
        """Check weekly trend from aligned weekly data.

        Args:
            market_data: Daily data with 'weekly_close' column

        Returns:
            'up' | 'down' | 'sideways'
        """
        # Extract unique weekly closes (remove duplicates from daily alignment)
        weekly_data = market_data[['timestamp', 'weekly_close']].drop_duplicates(
            subset=['weekly_close']
        ).copy()

        if len(weekly_data) < self.weekly_ma_long:
            logger.warning(
                f"Insufficient weekly data: {len(weekly_data)} < {self.weekly_ma_long}"
            )
            return 'sideways'

        # Calculate weekly MAs
        weekly_data['ma_short'] = weekly_data['weekly_close'].rolling(
            window=self.weekly_ma_short
        ).mean()
        weekly_data['ma_long'] = weekly_data['weekly_close'].rolling(
            window=self.weekly_ma_long
        ).mean()

        # Get latest values
        latest = weekly_data.iloc[-1]
        price = latest['weekly_close']
        ma_short = latest['ma_short']
        ma_long = latest['ma_long']

        # Check for NaN
        if pd.isna(ma_short) or pd.isna(ma_long):
            return 'sideways'

        # Determine trend
        if ma_short > ma_long and price > ma_short:
            trend = 'up'
        elif ma_short < ma_long and price < ma_short:
            trend = 'down'
        else:
            trend = 'sideways'

        logger.debug(
            f"Weekly trend: {trend.upper()} "
            f"(Price={price:.2f}, MA{self.weekly_ma_short}={ma_short:.2f}, "
            f"MA{self.weekly_ma_long}={ma_long:.2f})"
        )

        return trend

    def _generate_daily_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """Generate daily entry signal using moving average crossover.

        Args:
            market_data: Daily market data

        Returns:
            Dict with 'action', 'direction', etc. or None
        """
        df = market_data.copy()

        # Calculate daily MAs
        df['ma_fast'] = df['close'].rolling(window=self.daily_ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(window=self.daily_ma_slow).mean()

        # Check if we have enough data
        if df['ma_slow'].isna().iloc[-1]:
            return None

        # Get latest and previous values
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        current_price = latest['close']
        ma_fast_current = latest['ma_fast']
        ma_slow_current = latest['ma_slow']
        ma_fast_previous = previous['ma_fast']
        ma_slow_previous = previous['ma_slow']

        # Detect crossovers
        bullish_crossover = (
            ma_fast_current > ma_slow_current and
            ma_fast_previous <= ma_slow_previous
        )

        bearish_crossover = (
            ma_fast_current < ma_slow_current and
            ma_fast_previous >= ma_slow_previous
        )

        if bullish_crossover:
            return {
                'action': 'BUY',
                'direction': 'bullish',
                'entry_price': current_price,
                'reasoning': {
                    'daily_signal': '快线上穿慢线',
                    'ma_fast': float(ma_fast_current),
                    'ma_slow': float(ma_slow_current)
                }
            }
        elif bearish_crossover:
            return {
                'action': 'SELL',
                'direction': 'bearish',
                'entry_price': current_price,
                'reasoning': {
                    'daily_signal': '快线下穿慢线',
                    'ma_fast': float(ma_fast_current),
                    'ma_slow': float(ma_slow_current)
                }
            }
        else:
            return None

    def _combine_signals(
        self,
        weekly_trend: str,
        daily_signal: Optional[Dict]
    ) -> Optional[Dict]:
        """Combine weekly trend and daily signal.

        Only trade when both align.

        Args:
            weekly_trend: 'up' | 'down' | 'sideways'
            daily_signal: Daily signal dict or None

        Returns:
            Final signal or None
        """
        # No daily signal → HOLD
        if daily_signal is None:
            return None

        daily_action = daily_signal.get('action')
        entry_price = daily_signal.get('entry_price', 0)

        # Check alignment
        aligned = False
        final_action = None
        confidence = "LOW"

        if weekly_trend == 'up' and daily_action == 'BUY':
            aligned = True
            final_action = 'BUY'
            confidence = "HIGH"
        elif weekly_trend == 'down' and daily_action == 'SELL':
            aligned = True
            final_action = 'SELL'
            confidence = "HIGH"
        elif weekly_trend == 'sideways':
            # In sideways, use daily signal with lower confidence
            aligned = True
            final_action = daily_action
            confidence = "MEDIUM"

        if not aligned or final_action is None:
            logger.info(
                f"Signals not aligned: Weekly={weekly_trend}, Daily={daily_action} → HOLD"
            )
            return None

        # Calculate stop loss and take profit
        if final_action == 'BUY':
            stop_loss = entry_price * (1 - self.stop_loss_pct)
            take_profit = entry_price * (1 + self.take_profit_pct)
        else:  # SELL
            stop_loss = entry_price * (1 + self.stop_loss_pct)
            take_profit = entry_price * (1 - self.take_profit_pct)

        # Build final signal
        signal = {
            'action': final_action,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size_pct': 0.8 if confidence == "HIGH" else 0.5,
            'confidence': confidence,
            'reasoning': {
                'strategy': '多时间框架策略',
                'weekly_trend': weekly_trend,
                'daily_signal': daily_signal.get('reasoning', {}).get('daily_signal', ''),
                'alignment': f"周线{weekly_trend} + 日线{final_action}",
                'confidence_reason': (
                    "周线与日线方向一致" if confidence == "HIGH"
                    else "周线震荡，仅依据日线信号"
                )
            }
        }

        logger.info(
            f"✅ 多时间框架信号: {final_action} "
            f"(周线={weekly_trend}, 日线={daily_action}, 信心={confidence})"
        )

        return signal


# Example usage
if __name__ == '__main__':
    from investlib_data.resample import resample_to_weekly, align_timeframes

    # Generate sample daily data
    dates = pd.date_range(start='2024-01-01', end='2025-01-31', freq='D')
    np.random.seed(42)

    # Create uptrend
    trend = np.linspace(1800, 2000, len(dates))
    noise = np.random.normal(0, 20, len(dates))
    close_prices = trend + noise

    daily_data = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.normal(0, 5, len(dates)),
        'high': close_prices + np.abs(np.random.normal(10, 5, len(dates))),
        'low': close_prices - np.abs(np.random.normal(10, 5, len(dates))),
        'close': close_prices,
        'volume': np.random.randint(100000, 500000, len(dates))
    })

    # Resample to weekly
    weekly_data = resample_to_weekly(daily_data)

    # Align timeframes
    aligned_data = align_timeframes(weekly_data, daily_data)

    print("=" * 60)
    print("多时间框架策略测试")
    print("=" * 60)

    # Create strategy
    strategy = MultiTimeframeStrategy(
        name="周线+日线组合策略",
        weekly_ma_short=10,
        weekly_ma_long=20,
        daily_ma_fast=5,
        daily_ma_slow=20
    )

    # Test signal generation
    signal = strategy.generate_signal(aligned_data)

    if signal:
        print("\n✅ 交易信号:")
        print(f"  动作: {signal['action']}")
        print(f"  入场价: ¥{signal['entry_price']:.2f}")
        print(f"  止损: ¥{signal['stop_loss']:.2f}")
        print(f"  止盈: ¥{signal['take_profit']:.2f}")
        print(f"  仓位: {signal['position_size_pct']*100:.0f}%")
        print(f"  信心: {signal['confidence']}")
        print(f"\n  推理:")
        for key, value in signal['reasoning'].items():
            print(f"    {key}: {value}")
    else:
        print("\n⏸️ 无交易信号 (HOLD)")
        print("周线与日线信号未对齐，或无日线信号")
