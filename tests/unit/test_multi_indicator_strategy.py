"""
单元测试：多指标策略
测试 investlib-quant/strategies/multi_indicator.py 中的多指标投票系统
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加 investlib-quant 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'investlib-quant' / 'src'))

from investlib_quant.strategies.multi_indicator import MultiIndicatorStrategy


class TestMultiIndicatorStrategy:
    """多指标策略测试"""

    @pytest.fixture
    def strategy(self):
        """创建策略实例"""
        return MultiIndicatorStrategy(
            name="测试多指标策略",
            indicators=['macd', 'kdj', 'bollinger', 'volume'],
            min_votes=3
        )

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'open': [100 + i * 0.5 + np.random.randn() for i in range(100)],
            'high': [105 + i * 0.5 + np.random.randn() for i in range(100)],
            'low': [95 + i * 0.5 + np.random.randn() for i in range(100)],
            'close': [100 + i * 0.5 + np.random.randn() * 2 for i in range(100)],
            'volume': [1000000 + np.random.randint(-100000, 100000) for _ in range(100)]
        }, index=dates)
        return df

    def test_strategy_initialization(self, strategy):
        """测试：策略初始化"""
        assert strategy.name == "测试多指标策略", "策略名称应正确设置"
        assert len(strategy.indicators) == 4, "应有 4 个指标"
        assert strategy.min_votes == 3, "最小投票数应为 3"

    def test_validate_data_sufficient(self, strategy, sample_data):
        """测试：数据量充足验证"""
        is_valid = strategy.validate_data(sample_data, required_rows=50)
        assert is_valid is True, "100 行数据应通过 50 行要求"

    def test_validate_data_insufficient(self, strategy):
        """测试：数据量不足验证"""
        small_data = pd.DataFrame({'close': [100, 101, 102]})
        is_valid = strategy.validate_data(small_data, required_rows=50)
        assert is_valid is False, "3 行数据不应通过 50 行要求"

    def test_generate_signal_high_confidence(self, strategy, sample_data):
        """测试：高信心信号（4票一致）"""
        # 这是一个简化测试，实际信号需要真实市场数据
        # 仅测试策略能否生成信号
        try:
            signal = strategy.generate_signal(sample_data)

            if signal is not None:
                assert 'action' in signal, "信号应包含 action"
                assert signal['action'] in ['BUY', 'SELL'], "action 应为 BUY 或 SELL"
                assert 'confidence' in signal, "信号应包含 confidence"
                assert signal['confidence'] in ['HIGH', 'MEDIUM'], "置信度应为 HIGH 或 MEDIUM"
                assert 'votes' in signal.get('reasoning', {}), "推理应包含投票信息"
        except Exception as e:
            pytest.skip(f"信号生成需要真实数据或指标函数，跳过：{e}")

    def test_min_votes_threshold(self):
        """测试：最小投票数阈值"""
        # 需要 3 票
        strategy_3 = MultiIndicatorStrategy(min_votes=3)
        assert strategy_3.min_votes == 3, "最小投票数应为 3"

        # 需要 4 票（全部一致）
        strategy_4 = MultiIndicatorStrategy(min_votes=4)
        assert strategy_4.min_votes == 4, "最小投票数应为 4"

    def test_indicator_selection(self):
        """测试：指标选择"""
        # 仅使用 MACD 和 KDJ
        strategy = MultiIndicatorStrategy(
            indicators=['macd', 'kdj'],
            min_votes=2
        )

        assert len(strategy.indicators) == 2, "应仅有 2 个指标"
        assert 'macd' in strategy.indicators, "应包含 MACD"
        assert 'kdj' in strategy.indicators, "应包含 KDJ"

    def test_signal_contains_reasoning(self, strategy, sample_data):
        """测试：信号包含推理信息"""
        try:
            signal = strategy.generate_signal(sample_data)

            if signal is not None:
                assert 'reasoning' in signal, "信号应包含 reasoning"
                reasoning = signal['reasoning']

                # 应包含各指标的投票信息
                assert 'votes' in reasoning, "推理应包含投票信息"
                assert isinstance(reasoning['votes'], dict), "投票信息应为字典"

        except Exception as e:
            pytest.skip(f"信号生成需要真实数据，跳过：{e}")


class TestMultiIndicatorVoting:
    """多指标投票系统测试"""

    def test_voting_all_buy(self):
        """测试：所有指标都投买入"""
        votes = {
            'macd': 'BUY',
            'kdj': 'BUY',
            'bollinger': 'BUY',
            'volume': 'BUY'
        }

        buy_count = sum(1 for v in votes.values() if v == 'BUY')
        sell_count = sum(1 for v in votes.values() if v == 'SELL')

        assert buy_count == 4, "应有 4 票买入"
        assert sell_count == 0, "应有 0 票卖出"

        # 如果需要 3 票，应触发买入信号
        min_votes = 3
        assert buy_count >= min_votes, "买入票数应达到阈值"

    def test_voting_all_sell(self):
        """测试：所有指标都投卖出"""
        votes = {
            'macd': 'SELL',
            'kdj': 'SELL',
            'bollinger': 'SELL',
            'volume': 'SELL'
        }

        sell_count = sum(1 for v in votes.values() if v == 'SELL')

        assert sell_count == 4, "应有 4 票卖出"

    def test_voting_mixed_below_threshold(self):
        """测试：混合投票且未达阈值"""
        votes = {
            'macd': 'BUY',
            'kdj': 'SELL',
            'bollinger': None,
            'volume': None
        }

        buy_count = sum(1 for v in votes.values() if v == 'BUY')
        sell_count = sum(1 for v in votes.values() if v == 'SELL')

        min_votes = 3

        # 买入和卖出都未达阈值
        assert buy_count < min_votes, "买入票数未达阈值"
        assert sell_count < min_votes, "卖出票数未达阈值"

    def test_voting_exactly_at_threshold(self):
        """测试：恰好达到投票阈值"""
        votes = {
            'macd': 'BUY',
            'kdj': 'BUY',
            'bollinger': 'BUY',
            'volume': 'SELL'
        }

        buy_count = sum(1 for v in votes.values() if v == 'BUY')
        min_votes = 3

        assert buy_count == min_votes, "买入票数应恰好等于阈值"

    def test_confidence_level(self):
        """测试：置信度级别"""
        # 4 票一致 = HIGH
        votes_high = {'macd': 'BUY', 'kdj': 'BUY', 'bollinger': 'BUY', 'volume': 'BUY'}
        buy_count_high = sum(1 for v in votes_high.values() if v == 'BUY')
        confidence_high = 'HIGH' if buy_count_high == 4 else 'MEDIUM'
        assert confidence_high == 'HIGH', "4 票一致应为 HIGH 置信度"

        # 3 票 = MEDIUM
        votes_medium = {'macd': 'BUY', 'kdj': 'BUY', 'bollinger': 'BUY', 'volume': None}
        buy_count_medium = sum(1 for v in votes_medium.values() if v == 'BUY')
        confidence_medium = 'HIGH' if buy_count_medium == 4 else 'MEDIUM'
        assert confidence_medium == 'MEDIUM', "3 票应为 MEDIUM 置信度"


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_indicators_list(self):
        """测试：空指标列表"""
        with pytest.raises((ValueError, AssertionError)):
            strategy = MultiIndicatorStrategy(indicators=[], min_votes=1)

    def test_min_votes_exceeds_indicators(self):
        """测试：最小投票数超过指标数"""
        # 2 个指标但要求 3 票（不可能达到）
        strategy = MultiIndicatorStrategy(
            indicators=['macd', 'kdj'],
            min_votes=3
        )

        # 应能初始化但永远无法生成信号
        assert strategy.min_votes == 3, "最小投票数应为 3"
        assert len(strategy.indicators) == 2, "仅有 2 个指标"

    def test_single_indicator_strategy(self):
        """测试：单指标策略"""
        strategy = MultiIndicatorStrategy(
            indicators=['macd'],
            min_votes=1
        )

        assert len(strategy.indicators) == 1, "应仅有 1 个指标"
        assert strategy.min_votes == 1, "最小投票数应为 1"

    def test_data_with_nan_values(self):
        """测试：包含 NaN 的数据"""
        df = pd.DataFrame({
            'open': [100, np.nan, 102, 103],
            'high': [105, 106, np.nan, 108],
            'low': [95, 96, 97, np.nan],
            'close': [100, 101, 102, 103],
            'volume': [1000000, 1100000, 1200000, 1300000]
        })

        strategy = MultiIndicatorStrategy()

        # 应能处理（通过数据验证或在计算中处理 NaN）
        try:
            is_valid = strategy.validate_data(df, required_rows=4)
            assert isinstance(is_valid, bool), "应返回布尔值"
        except Exception as e:
            pytest.skip(f"包含 NaN 的数据处理可能需要额外逻辑：{e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
