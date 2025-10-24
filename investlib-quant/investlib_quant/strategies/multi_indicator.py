"""
Multi-Indicator Combination Strategy (T065)

Combine MACD, KDJ, Bollinger Bands, and Volume for robust signals.
"""

import pandas as pd
from typing import Optional, Dict
from .stock_strategy import StockStrategy
from ..indicators.macd import calculate_macd, detect_macd_crossover
from ..indicators.kdj import calculate_kdj, detect_kdj_signal
from ..indicators.bollinger import calculate_bollinger_bands, detect_bollinger_signal
from ..indicators.volume import calculate_volume_ma, detect_volume_spike
import logging


logger = logging.getLogger(__name__)


class MultiIndicatorStrategy(StockStrategy):
    """多指标组合策略.

    Combines multiple technical indicators using voting system:
    - MACD: Trend confirmation
    - KDJ: Overbought/oversold timing
    - Bollinger Bands: Volatility extremes
    - Volume: Confirmation of strength

    Voting Logic:
    - BUY: 3+ bullish indicators
    - SELL: 3+ bearish indicators
    - HOLD: Mixed signals
    """

    def __init__(
        self,
        name: str = "多指标组合策略",
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        kdj_period: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        volume_period: int = 20,
        min_votes: int = 3
    ):
        super().__init__(name)
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.kdj_period = kdj_period
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.volume_period = volume_period
        self.min_votes = min_votes

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        if not self.validate_data(market_data, required_rows=30):
            return None

        df = market_data.copy()

        # Calculate indicators
        macd, macd_sig, _ = calculate_macd(df, self.macd_fast, self.macd_slow, self.macd_signal)
        k, d, j = calculate_kdj(df, period=self.kdj_period)
        upper, middle, lower = calculate_bollinger_bands(df, self.bb_period, self.bb_std)
        vol_ma = calculate_volume_ma(df, self.volume_period)

        # Detect signals
        macd_signal = detect_macd_crossover(macd, macd_sig)
        kdj_signal = detect_kdj_signal(k, d, j)
        bb_signal = detect_bollinger_signal(
            df['close'].iloc[-1],
            upper.iloc[-1],
            lower.iloc[-1],
            middle.iloc[-1]
        )
        vol_spike = detect_volume_spike(df['volume'].iloc[-1], vol_ma.iloc[-1])

        # Vote counting
        buy_votes = 0
        sell_votes = 0
        indicators = {}

        if macd_signal == 'bullish':
            buy_votes += 1
            indicators['MACD'] = '买入 (金叉)'
        elif macd_signal == 'bearish':
            sell_votes += 1
            indicators['MACD'] = '卖出 (死叉)'
        else:
            indicators['MACD'] = '中性'

        if kdj_signal == 'buy':
            buy_votes += 1
            indicators['KDJ'] = '买入 (超卖反弹)'
        elif kdj_signal == 'sell':
            sell_votes += 1
            indicators['KDJ'] = '卖出 (超买回落)'
        else:
            indicators['KDJ'] = '中性'

        if bb_signal == 'oversold':
            buy_votes += 1
            indicators['布林带'] = '买入 (触及下轨)'
        elif bb_signal == 'overbought':
            sell_votes += 1
            indicators['布林带'] = '卖出 (触及上轨)'
        else:
            indicators['布林带'] = '中性'

        if vol_spike:
            # Volume spike confirms direction
            if buy_votes > sell_votes:
                buy_votes += 1
                indicators['成交量'] = '放量确认 (买入)'
            elif sell_votes > buy_votes:
                sell_votes += 1
                indicators['成交量'] = '放量确认 (卖出)'
            else:
                indicators['成交量'] = '放量'
        else:
            indicators['成交量'] = '正常'

        # Decision
        current_price = df['close'].iloc[-1]

        if buy_votes >= self.min_votes:
            return {
                'action': 'BUY',
                'entry_price': current_price,
                'stop_loss': current_price * 0.95,
                'take_profit': current_price * 1.10,
                'position_size_pct': 0.7,
                'confidence': 'HIGH' if buy_votes >= 4 else 'MEDIUM',
                'reasoning': {
                    'strategy': '多指标组合',
                    'buy_votes': buy_votes,
                    'sell_votes': sell_votes,
                    'indicators': indicators
                }
            }
        elif sell_votes >= self.min_votes:
            return {
                'action': 'SELL',
                'entry_price': current_price,
                'stop_loss': current_price * 1.05,
                'take_profit': current_price * 0.90,
                'position_size_pct': 0.7,
                'confidence': 'HIGH' if sell_votes >= 4 else 'MEDIUM',
                'reasoning': {
                    'strategy': '多指标组合',
                    'buy_votes': buy_votes,
                    'sell_votes': sell_votes,
                    'indicators': indicators
                }
            }

        return None


# Example
if __name__ == '__main__':
    import numpy as np

    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    close = 1900 + 50 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 15, 100)

    df = pd.DataFrame({
        'timestamp': dates,
        'high': close + 10,
        'low': close - 10,
        'close': close,
        'volume': np.random.randint(100000, 500000, 100)
    })

    strategy = MultiIndicatorStrategy(min_votes=3)
    signal = strategy.generate_signal(df)

    if signal:
        print(f"信号: {signal['action']}, 信心: {signal['confidence']}")
        print(f"指标投票: {signal['reasoning']}")
    else:
        print("无信号")
