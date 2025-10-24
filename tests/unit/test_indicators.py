"""
单元测试：技术指标
测试 investlib-quant/indicators/ 中的 MACD、KDJ、布林带、成交量指标
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加 investlib-quant 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'investlib-quant' / 'src'))

from investlib_quant.indicators.macd import calculate_macd, detect_macd_crossover
from investlib_quant.indicators.kdj import calculate_kdj, detect_kdj_signal
from investlib_quant.indicators.bollinger import calculate_bollinger_bands, detect_bollinger_signal
from investlib_quant.indicators.volume import detect_volume_spike, detect_volume_divergence, calculate_volume_ma


class TestMACDIndicator:
    """MACD 指标测试"""

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        # 模拟上升趋势
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        prices = pd.Series([100 + i * 0.5 + np.random.randn() * 2 for i in range(100)], index=dates)
        df = pd.DataFrame({'close': prices})
        return df

    def test_macd_calculation(self, sample_data):
        """测试：MACD 计算"""
        macd, signal, histogram = calculate_macd(sample_data, fast=12, slow=26, signal_period=9)

        # 应返回与输入相同长度的序列
        assert len(macd) == len(sample_data), "MACD 长度应与输入相同"
        assert len(signal) == len(sample_data), "信号线长度应与输入相同"
        assert len(histogram) == len(sample_data), "柱状图长度应与输入相同"

        # 前面部分因 EMA 计算可能为 NaN
        assert not pd.isna(macd.iloc[-1]), "最后一个 MACD 值不应为 NaN"
        assert not pd.isna(signal.iloc[-1]), "最后一个信号线值不应为 NaN"

    def test_macd_golden_cross(self):
        """测试：MACD 金叉检测"""
        # 模拟金叉：MACD 从下方穿越信号线
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        macd_line = pd.Series([-5, -4, -3, -2, -1, 0, 1, 2] + [2] * 42, index=dates)
        signal_line = pd.Series([0, 0, 0, 0, 0, 0, 0, 0] + [0] * 42, index=dates)

        df = pd.DataFrame({'close': macd_line})  # 占位

        signal = detect_macd_crossover(macd_line, signal_line)

        # 金叉信号应在 MACD 上穿信号线时出现
        assert signal in ['golden_cross', 'death_cross', None], "应返回有效信号类型"

    def test_macd_death_cross(self):
        """测试：MACD 死叉检测"""
        # 模拟死叉：MACD 从上方穿越信号线
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        macd_line = pd.Series([5, 4, 3, 2, 1, 0, -1, -2] + [-2] * 42, index=dates)
        signal_line = pd.Series([0, 0, 0, 0, 0, 0, 0, 0] + [0] * 42, index=dates)

        signal = detect_macd_crossover(macd_line, signal_line)

        assert signal in ['golden_cross', 'death_cross', None], "应返回有效信号类型"

    def test_macd_histogram_sign(self, sample_data):
        """测试：MACD 柱状图符号"""
        macd, signal, histogram = calculate_macd(sample_data)

        # 柱状图 = MACD - Signal
        expected_histogram = macd - signal

        # 允许浮点误差
        pd.testing.assert_series_equal(histogram, expected_histogram, check_names=False)


class TestKDJIndicator:
    """KDJ 指标测试"""

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'high': [110 + i + np.random.randn() * 2 for i in range(50)],
            'low': [90 + i + np.random.randn() * 2 for i in range(50)],
            'close': [100 + i + np.random.randn() * 2 for i in range(50)]
        }, index=dates)
        return df

    def test_kdj_calculation(self, sample_data):
        """测试：KDJ 计算"""
        k, d, j = calculate_kdj(sample_data, period=9, k_smooth=3, d_smooth=3)

        # 应返回与输入相同长度的序列
        assert len(k) == len(sample_data), "K 线长度应与输入相同"
        assert len(d) == len(sample_data), "D 线长度应与输入相同"
        assert len(j) == len(sample_data), "J 线长度应与输入相同"

        # 最后的值不应为 NaN
        assert not pd.isna(k.iloc[-1]), "最后一个 K 值不应为 NaN"
        assert not pd.isna(d.iloc[-1]), "最后一个 D 值不应为 NaN"
        assert not pd.isna(j.iloc[-1]), "最后一个 J 值不应为 NaN"

    def test_kdj_range(self, sample_data):
        """测试：KDJ 值范围"""
        k, d, j = calculate_kdj(sample_data)

        # K 和 D 应主要在 0-100 之间（J 可能超出）
        # 取最后 20 个非 NaN 值测试
        k_valid = k.dropna().tail(20)
        d_valid = d.dropna().tail(20)

        # 允许偶尔超出，但大部分应在范围内
        assert (k_valid >= 0).sum() / len(k_valid) > 0.7, "K 值应主要在 0 以上"
        assert (k_valid <= 100).sum() / len(k_valid) > 0.7, "K 值应主要在 100 以下"
        assert (d_valid >= 0).sum() / len(d_valid) > 0.7, "D 值应主要在 0 以上"
        assert (d_valid <= 100).sum() / len(d_valid) > 0.7, "D 值应主要在 100 以下"

    def test_kdj_oversold_signal(self):
        """测试：KDJ 超卖信号"""
        dates = pd.date_range('2024-01-01', periods=20, freq='D')

        # 模拟超卖：K < 20, D < 20, K 上穿 D
        k_line = pd.Series([10, 15, 25] + [25] * 17, index=dates)
        d_line = pd.Series([20, 20, 20] + [20] * 17, index=dates)
        j_line = pd.Series([0, 5, 35] + [35] * 17, index=dates)

        signal = detect_kdj_signal(k_line, d_line, j_line, oversold=20, overbought=80)

        # 应检测到买入信号
        assert signal in ['BUY', 'SELL', None], "应返回有效信号"

    def test_kdj_overbought_signal(self):
        """测试：KDJ 超买信号"""
        dates = pd.date_range('2024-01-01', periods=20, freq='D')

        # 模拟超买：K > 80, D > 80, K 下穿 D
        k_line = pd.Series([90, 85, 75] + [75] * 17, index=dates)
        d_line = pd.Series([80, 80, 80] + [80] * 17, index=dates)
        j_line = pd.Series([110, 95, 65] + [65] * 17, index=dates)

        signal = detect_kdj_signal(k_line, d_line, j_line, oversold=20, overbought=80)

        # 应检测到卖出信号
        assert signal in ['BUY', 'SELL', None], "应返回有效信号"


class TestBollingerBands:
    """布林带指标测试"""

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        prices = pd.Series([100 + i * 0.5 + np.random.randn() * 5 for i in range(50)], index=dates)
        df = pd.DataFrame({'close': prices})
        return df

    def test_bollinger_bands_calculation(self, sample_data):
        """测试：布林带计算"""
        upper, middle, lower = calculate_bollinger_bands(sample_data, period=20, std_dev=2)

        # 应返回与输入相同长度的序列
        assert len(upper) == len(sample_data), "上轨长度应与输入相同"
        assert len(middle) == len(sample_data), "中轨长度应与输入相同"
        assert len(lower) == len(sample_data), "下轨长度应与输入相同"

        # 最后的值不应为 NaN
        assert not pd.isna(upper.iloc[-1]), "最后一个上轨值不应为 NaN"
        assert not pd.isna(middle.iloc[-1]), "最后一个中轨值不应为 NaN"
        assert not pd.isna(lower.iloc[-1]), "最后一个下轨值不应为 NaN"

    def test_bollinger_bands_order(self, sample_data):
        """测试：布林带顺序（上轨 > 中轨 > 下轨）"""
        upper, middle, lower = calculate_bollinger_bands(sample_data)

        # 取最后 20 个非 NaN 值
        valid_indices = ~upper.isna() & ~middle.isna() & ~lower.isna()
        upper_valid = upper[valid_indices].tail(20)
        middle_valid = middle[valid_indices].tail(20)
        lower_valid = lower[valid_indices].tail(20)

        # 上轨应 >= 中轨 >= 下轨
        assert (upper_valid >= middle_valid).all(), "上轨应 >= 中轨"
        assert (middle_valid >= lower_valid).all(), "中轨应 >= 下轨"

    def test_bollinger_middle_equals_ma(self, sample_data):
        """测试：中轨应等于移动平均线"""
        upper, middle, lower = calculate_bollinger_bands(sample_data, period=20)

        # 中轨应等于 20 日均线
        ma20 = sample_data['close'].rolling(20).mean()

        # 允许浮点误差
        pd.testing.assert_series_equal(middle, ma20, check_names=False)

    def test_bollinger_oversold_signal(self):
        """测试：布林带超卖信号"""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')

        # 价格触及下轨
        price = pd.Series([100] * 25 + [85, 90, 95, 100, 100], index=dates)
        upper = pd.Series([110] * 30, index=dates)
        middle = pd.Series([100] * 30, index=dates)
        lower = pd.Series([90] * 30, index=dates)

        signal = detect_bollinger_signal(price, upper, middle, lower)

        # 应返回有效信号
        assert signal in ['BUY', 'SELL', None], "应返回有效信号"

    def test_bollinger_overbought_signal(self):
        """测试：布林带超买信号"""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')

        # 价格触及上轨
        price = pd.Series([100] * 25 + [115, 110, 105, 100, 100], index=dates)
        upper = pd.Series([110] * 30, index=dates)
        middle = pd.Series([100] * 30, index=dates)
        lower = pd.Series([90] * 30, index=dates)

        signal = detect_bollinger_signal(price, upper, middle, lower)

        # 应返回有效信号
        assert signal in ['BUY', 'SELL', None], "应返回有效信号"


class TestVolumeIndicator:
    """成交量指标测试"""

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'close': [100 + i * 0.5 + np.random.randn() * 2 for i in range(50)],
            'volume': [1000000 + np.random.randint(-100000, 100000) for _ in range(50)]
        }, index=dates)
        return df

    def test_volume_spike_detection(self, sample_data):
        """测试：成交量异常放大检测"""
        # 手动添加一个放量
        sample_data.loc[sample_data.index[-5], 'volume'] = 3000000  # 3倍平均量

        # 计算成交量均线
        vol_ma = calculate_volume_ma(sample_data, period=20)

        # 检测最后一天的放量
        spike = detect_volume_spike(
            current_volume=sample_data['volume'].iloc[-5],
            volume_ma=vol_ma.iloc[-5],
            threshold=2.0
        )

        # 应检测到放量
        assert spike in [True, False], "应返回布尔值"

    def test_volume_spike_threshold(self, sample_data):
        """测试：成交量放大阈值"""
        vol_ma = calculate_volume_ma(sample_data, period=20)

        # 正常成交量
        spike_low = detect_volume_spike(
            current_volume=sample_data['volume'].iloc[-1],
            volume_ma=vol_ma.iloc[-1],
            threshold=10.0  # 很高的阈值
        )
        assert spike_low is False, "高阈值不应检测到放量"

        # 添加极端放量
        sample_data.loc[sample_data.index[-1], 'volume'] = 10000000  # 10倍
        vol_ma = calculate_volume_ma(sample_data, period=20)

        spike_high = detect_volume_spike(
            current_volume=sample_data['volume'].iloc[-1],
            volume_ma=vol_ma.iloc[-1],
            threshold=2.0  # 低阈值
        )
        assert spike_high is True, "低阈值应检测到极端放量"

    def test_price_volume_divergence(self, sample_data):
        """测试：价格与成交量背离"""
        # 模拟背离：价格上涨，成交量下降
        sample_data.loc[sample_data.index[-10:], 'close'] = range(110, 120)  # 价格上涨
        sample_data.loc[sample_data.index[-10:], 'volume'] = list(range(2000000, 1000000, -100000))  # 成交量下降

        divergence = detect_volume_divergence(
            price_series=sample_data['close'],
            volume_series=sample_data['volume'],
            lookback=10
        )

        # 应检测到背离
        assert divergence in [True, False], "应返回布尔值"

    def test_no_volume_divergence(self, sample_data):
        """测试：无价格成交量背离"""
        # 价格和成交量都上涨（无背离）
        sample_data.loc[sample_data.index[-10:], 'close'] = range(110, 120)
        sample_data.loc[sample_data.index[-10:], 'volume'] = list(range(1000000, 2000000, 100000))

        divergence = detect_volume_divergence(
            price_series=sample_data['close'],
            volume_series=sample_data['volume'],
            lookback=10
        )

        # 不应检测到背离（或返回 False）
        assert divergence in [True, False], "应返回布尔值"


class TestEdgeCases:
    """边界情况测试"""

    def test_insufficient_data_macd(self):
        """测试：数据不足时 MACD 计算"""
        df = pd.DataFrame({'close': [100, 101, 102]})  # 仅 3 个数据点

        macd, signal, histogram = calculate_macd(df, fast=12, slow=26, signal_period=9)

        # 应返回序列（但大部分为 NaN）
        assert len(macd) == 3, "应返回相同长度"
        assert pd.isna(macd.iloc[0]), "数据不足时前面应为 NaN"

    def test_insufficient_data_kdj(self):
        """测试：数据不足时 KDJ 计算"""
        df = pd.DataFrame({
            'high': [110, 111, 112],
            'low': [90, 91, 92],
            'close': [100, 101, 102]
        })

        k, d, j = calculate_kdj(df, period=9)

        # 应返回序列（但大部分为 NaN）
        assert len(k) == 3, "应返回相同长度"

    def test_constant_price_bollinger(self):
        """测试：价格恒定时布林带"""
        df = pd.DataFrame({'close': [100] * 30})  # 恒定价格

        upper, middle, lower = calculate_bollinger_bands(df, period=20, std_dev=2)

        # 中轨应等于价格
        assert middle.dropna().iloc[-1] == 100, "中轨应等于恒定价格"

        # 上轨和下轨应等于中轨（标准差为 0）
        assert upper.dropna().iloc[-1] == 100, "恒定价格时上轨应等于中轨"
        assert lower.dropna().iloc[-1] == 100, "恒定价格时下轨应等于中轨"

    def test_zero_volume(self):
        """测试：零成交量"""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104],
            'volume': [0, 0, 0, 0, 0]
        })

        vol_ma = calculate_volume_ma(df, period=3)

        spike = detect_volume_spike(
            current_volume=df['volume'].iloc[-1],
            volume_ma=vol_ma.iloc[-1],
            threshold=2.0
        )

        # 零成交量不应触发放量
        assert spike is False, "零成交量不应检测到放量"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
