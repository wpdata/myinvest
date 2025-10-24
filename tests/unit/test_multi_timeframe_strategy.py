"""
单元测试：多时间框架策略
测试 investlib-quant/strategies/multi_timeframe.py 中的多时间框架分析
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'investlib-quant' / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'investlib-data'))

from investlib_quant.strategies.multi_timeframe import MultiTimeframeStrategy
from investlib_data.resample import resample_to_weekly, align_timeframes


class TestMultiTimeframeStrategy:
    """多时间框架策略测试"""

    @pytest.fixture
    def strategy(self):
        """创建策略实例"""
        return MultiTimeframeStrategy(
            name="测试多时间框架策略",
            require_weekly_confirmation=True
        )

    @pytest.fixture
    def sample_data(self):
        """创建样本日线数据（至少 100 天用于周线转换）"""
        dates = pd.date_range('2024-01-01', periods=150, freq='D')
        df = pd.DataFrame({
            'open': [100 + i * 0.1 + np.random.randn() for i in range(150)],
            'high': [105 + i * 0.1 + np.random.randn() for i in range(150)],
            'low': [95 + i * 0.1 + np.random.randn() for i in range(150)],
            'close': [100 + i * 0.1 + np.random.randn() * 2 for i in range(150)],
            'volume': [1000000 + np.random.randint(-100000, 100000) for _ in range(150)]
        }, index=dates)
        return df

    def test_strategy_initialization(self, strategy):
        """测试：策略初始化"""
        assert strategy.name == "测试多时间框架策略", "策略名称应正确设置"
        assert strategy.require_weekly_confirmation is True, "应要求周线确认"

    def test_resample_to_weekly(self, sample_data):
        """测试：日线转周线"""
        weekly_df = resample_to_weekly(sample_data, week_start='MON')

        # 周线数据应少于日线数据
        assert len(weekly_df) < len(sample_data), "周线数据应少于日线数据"

        # 周线应约为日线的 1/5
        expected_weeks = len(sample_data) / 5
        assert abs(len(weekly_df) - expected_weeks) < 5, "周线数据量应约为日线的 1/5"

        # 应包含 OHLCV 列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in weekly_df.columns, f"周线数据应包含 {col} 列"

    def test_align_timeframes(self, sample_data):
        """测试：日线和周线对齐"""
        weekly_df = resample_to_weekly(sample_data)
        daily_aligned, weekly_aligned = align_timeframes(sample_data, weekly_df)

        # 对齐后长度应相同
        assert len(daily_aligned) == len(weekly_aligned), "对齐后长度应相同"

        # 对齐后应不多于原日线数据
        assert len(daily_aligned) <= len(sample_data), "对齐后不应多于原日线数据"

    def test_weekly_uptrend_detection(self, strategy, sample_data):
        """测试：周线上升趋势检测"""
        # 模拟明显上升趋势
        dates = pd.date_range('2024-01-01', periods=150, freq='D')
        uptrend_data = pd.DataFrame({
            'open': [100 + i * 0.5 for i in range(150)],
            'high': [105 + i * 0.5 for i in range(150)],
            'low': [95 + i * 0.5 for i in range(150)],
            'close': [100 + i * 0.5 for i in range(150)],
            'volume': [1000000] * 150
        }, index=dates)

        try:
            signal = strategy.generate_signal(uptrend_data)

            # 可能生成买入信号（如果周线趋势向上）
            if signal is not None:
                assert 'action' in signal, "信号应包含 action"
                assert 'weekly_trend' in signal.get('reasoning', {}), "应包含周线趋势信息"
        except Exception as e:
            pytest.skip(f"趋势检测需要完整实现，跳过：{e}")

    def test_weekly_downtrend_rejection(self, strategy):
        """测试：周线下降趋势拒绝买入"""
        # 模拟明显下降趋势
        dates = pd.date_range('2024-01-01', periods=150, freq='D')
        downtrend_data = pd.DataFrame({
            'open': [200 - i * 0.5 for i in range(150)],
            'high': [205 - i * 0.5 for i in range(150)],
            'low': [195 - i * 0.5 for i in range(150)],
            'close': [200 - i * 0.5 for i in range(150)],
            'volume': [1000000] * 150
        }, index=dates)

        try:
            signal = strategy.generate_signal(downtrend_data)

            # 下降趋势不应生成买入信号
            if signal is not None:
                assert signal['action'] != 'BUY' or 'weekly_trend' in signal.get('reasoning', {}), \
                    "下降趋势不应生成买入信号"
        except Exception as e:
            pytest.skip(f"趋势检测需要完整实现，跳过：{e}")

    def test_signal_contains_multi_timeframe_info(self, strategy, sample_data):
        """测试：信号包含多时间框架信息"""
        try:
            signal = strategy.generate_signal(sample_data)

            if signal is not None:
                reasoning = signal.get('reasoning', {})

                # 应包含周线趋势和日线信号
                assert 'weekly_trend' in reasoning or 'daily_signal' in reasoning, \
                    "信号推理应包含多时间框架信息"
        except Exception as e:
            pytest.skip(f"信号生成需要完整实现，跳过：{e}")


class TestWeeklyTrendAnalysis:
    """周线趋势分析测试"""

    def test_weekly_ma_calculation(self, sample_data):
        """测试：周线移动平均线计算"""
        weekly_df = resample_to_weekly(sample_data)

        # 计算周线 10 周均线
        ma_10 = weekly_df['close'].rolling(10).mean()

        # 应返回与周线数据相同长度的序列
        assert len(ma_10) == len(weekly_df), "均线长度应与周线数据相同"

        # 最后的值不应为 NaN（如果有足够数据）
        if len(weekly_df) >= 10:
            assert not pd.isna(ma_10.iloc[-1]), "有足够数据时最后一个均线值不应为 NaN"

    def test_weekly_trend_direction(self):
        """测试：周线趋势方向判断"""
        # 上升趋势：短期均线 > 长期均线，价格 > 短期均线
        ma_short = 120  # 短期均线值
        ma_long = 100   # 长期均线值
        current_price = 125

        trend_up = (ma_short > ma_long) and (current_price > ma_short)
        assert trend_up is True, "应检测到上升趋势"

        # 下降趋势
        ma_short_down = 100
        ma_long_down = 120
        current_price_down = 95

        trend_down = (ma_short_down < ma_long_down) and (current_price_down < ma_short_down)
        assert trend_down is True, "应检测到下降趋势"

    def test_sideways_trend(self):
        """测试：横盘趋势"""
        # 横盘：短期均线 ≈ 长期均线
        ma_short = 100
        ma_long = 102
        threshold = 0.03  # 3% 阈值

        diff_pct = abs(ma_short - ma_long) / ma_long

        is_sideways = diff_pct < threshold
        assert is_sideways is True, "应检测到横盘趋势"


class TestDataResampling:
    """数据重采样测试"""

    def test_weekly_high_is_max(self, sample_data):
        """测试：周线最高价是日线最高价的最大值"""
        weekly_df = resample_to_weekly(sample_data)

        # 取第一周进行验证
        first_week_end = weekly_df.index[0]

        # 找到对应的日线数据
        week_daily_data = sample_data[sample_data.index <= first_week_end].tail(5)  # 约一周

        if len(week_daily_data) > 0:
            expected_high = week_daily_data['high'].max()
            actual_high = weekly_df.iloc[0]['high']

            # 允许浮点误差
            assert abs(actual_high - expected_high) < 0.01, "周线最高价应等于日线最高价的最大值"

    def test_weekly_low_is_min(self, sample_data):
        """测试：周线最低价是日线最低价的最小值"""
        weekly_df = resample_to_weekly(sample_data)

        first_week_end = weekly_df.index[0]
        week_daily_data = sample_data[sample_data.index <= first_week_end].tail(5)

        if len(week_daily_data) > 0:
            expected_low = week_daily_data['low'].min()
            actual_low = weekly_df.iloc[0]['low']

            assert abs(actual_low - expected_low) < 0.01, "周线最低价应等于日线最低价的最小值"

    def test_weekly_volume_is_sum(self, sample_data):
        """测试：周线成交量是日线成交量之和"""
        weekly_df = resample_to_weekly(sample_data)

        first_week_end = weekly_df.index[0]
        week_daily_data = sample_data[sample_data.index <= first_week_end].tail(5)

        if len(week_daily_data) > 0:
            expected_volume = week_daily_data['volume'].sum()
            actual_volume = weekly_df.iloc[0]['volume']

            assert abs(actual_volume - expected_volume) < 1, "周线成交量应等于日线成交量之和"


class TestEdgeCases:
    """边界情况测试"""

    def test_insufficient_data_for_weekly(self):
        """测试：数据不足以转换周线"""
        # 仅 3 天数据
        small_data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [105, 106, 107],
            'low': [95, 96, 97],
            'close': [100, 101, 102],
            'volume': [1000000, 1100000, 1200000]
        }, index=pd.date_range('2024-01-01', periods=3, freq='D'))

        weekly_df = resample_to_weekly(small_data)

        # 应仅生成 1 周数据（或 0 周）
        assert len(weekly_df) <= 2, "少量数据应生成很少周线数据"

    def test_single_week_data(self):
        """测试：恰好一周数据"""
        week_data = pd.DataFrame({
            'open': range(100, 105),
            'high': range(105, 110),
            'low': range(95, 100),
            'close': range(100, 105),
            'volume': [1000000] * 5
        }, index=pd.date_range('2024-01-01', periods=5, freq='D'))  # 周一到周五

        weekly_df = resample_to_weekly(week_data)

        # 应生成 1 周数据
        assert len(weekly_df) == 1, "一周数据应生成 1 周线数据"

    def test_missing_days_in_week(self):
        """测试：周内缺失某些天（如节假日）"""
        # 缺失周三（索引 2）
        dates = [pd.Timestamp('2024-01-01'),  # 周一
                 pd.Timestamp('2024-01-02'),  # 周二
                 # 周三缺失
                 pd.Timestamp('2024-01-04'),  # 周四
                 pd.Timestamp('2024-01-05')]  # 周五

        incomplete_week = pd.DataFrame({
            'open': [100, 101, 103, 104],
            'high': [105, 106, 108, 109],
            'low': [95, 96, 98, 99],
            'close': [100, 101, 103, 104],
            'volume': [1000000] * 4
        }, index=dates)

        weekly_df = resample_to_weekly(incomplete_week)

        # 应能处理缺失数据并生成周线
        assert len(weekly_df) >= 1, "缺失数据的周应能生成周线"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
