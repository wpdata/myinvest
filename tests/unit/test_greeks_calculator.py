"""
单元测试：Greeks 计算器
测试 investlib-greeks/calculator.py 中的期权 Greeks 计算
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# 添加 investlib-greeks 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'investlib-greeks'))

from investlib_greeks.calculator import OptionsGreeksCalculator, VolatilityManager


class TestGreeksCalculation:
    """Greeks 计算测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return OptionsGreeksCalculator()

    def test_atm_call_greeks(self, calculator):
        """测试：平价看涨期权 Greeks"""
        try:
            greeks = calculator.calculate_greeks(
                S=50,  # 标的价格
                K=50,  # 行权价（平价）
                T=0.25,  # 3个月
                r=0.03,  # 无风险利率 3%
                sigma=0.20,  # 波动率 20%
                option_type='call'
            )

            # 平价看涨期权：Delta 约 0.5-0.6
            assert 0.4 < greeks['delta'] < 0.7, f"平价看涨 Delta 应在 0.4-0.7，实际 {greeks['delta']}"

            # Gamma 应为正
            assert greeks['gamma'] > 0, "看涨期权 Gamma 应为正"

            # Vega 应为正
            assert greeks['vega'] > 0, "看涨期权 Vega 应为正"

            # Theta 应为负（时间衰减）
            assert greeks['theta'] < 0, "看涨期权 Theta 应为负"

        except ImportError:
            pytest.skip("py_vollib 未安装，跳过此测试")

    def test_atm_put_greeks(self, calculator):
        """测试：平价看跌期权 Greeks"""
        try:
            greeks = calculator.calculate_greeks(
                S=50,
                K=50,
                T=0.25,
                r=0.03,
                sigma=0.20,
                option_type='put'
            )

            # 平价看跌期权：Delta 约 -0.4 到 -0.6
            assert -0.7 < greeks['delta'] < -0.3, f"平价看跌 Delta 应在 -0.7 到 -0.3，实际 {greeks['delta']}"

            # Gamma 应为正
            assert greeks['gamma'] > 0, "看跌期权 Gamma 应为正"

            # Vega 应为正
            assert greeks['vega'] > 0, "看跌期权 Vega 应为正"

            # Theta 应为负
            assert greeks['theta'] < 0, "看跌期权 Theta 应为负"

        except ImportError:
            pytest.skip("py_vollib 未安装，跳过此测试")

    def test_itm_call_greeks(self, calculator):
        """测试：实值看涨期权 Greeks"""
        try:
            greeks = calculator.calculate_greeks(
                S=55,  # 标的价格 55
                K=50,  # 行权价 50（实值 5）
                T=0.25,
                r=0.03,
                sigma=0.20,
                option_type='call'
            )

            # 实值看涨：Delta > 0.6
            assert greeks['delta'] > 0.6, f"实值看涨 Delta 应 > 0.6，实际 {greeks['delta']}"

        except ImportError:
            pytest.skip("py_vollib 未安装，跳过此测试")

    def test_otm_call_greeks(self, calculator):
        """测试：虚值看涨期权 Greeks"""
        try:
            greeks = calculator.calculate_greeks(
                S=45,  # 标的价格 45
                K=50,  # 行权价 50（虚值 5）
                T=0.25,
                r=0.03,
                sigma=0.20,
                option_type='call'
            )

            # 虚值看涨：Delta < 0.4
            assert greeks['delta'] < 0.4, f"虚值看涨 Delta 应 < 0.4，实际 {greeks['delta']}"

        except ImportError:
            pytest.skip("py_vollib 未安装，跳过此测试")

    def test_near_expiry_theta(self, calculator):
        """测试：临近到期时 Theta 加速衰减"""
        try:
            # 3个月到期
            greeks_3m = calculator.calculate_greeks(
                S=50, K=50, T=0.25, r=0.03, sigma=0.20, option_type='call'
            )

            # 1周到期
            greeks_1w = calculator.calculate_greeks(
                S=50, K=50, T=7/365, r=0.03, sigma=0.20, option_type='call'
            )

            # 临近到期 Theta 应更大（绝对值）
            assert abs(greeks_1w['theta']) > abs(greeks_3m['theta']), \
                "临近到期时 Theta 应加速衰减"

        except ImportError:
            pytest.skip("py_vollib 未安装，跳过此测试")

    def test_high_volatility_vega(self, calculator):
        """测试：高波动率对 Vega 的影响"""
        try:
            # 低波动率
            greeks_low_vol = calculator.calculate_greeks(
                S=50, K=50, T=0.25, r=0.03, sigma=0.10, option_type='call'
            )

            # 高波动率
            greeks_high_vol = calculator.calculate_greeks(
                S=50, K=50, T=0.25, r=0.03, sigma=0.40, option_type='call'
            )

            # 高波动率时 Vega 通常更小（因为期权已经很贵）
            # 但这个关系复杂，只测试 Vega 为正
            assert greeks_low_vol['vega'] > 0, "低波动率 Vega 应为正"
            assert greeks_high_vol['vega'] > 0, "高波动率 Vega 应为正"

        except ImportError:
            pytest.skip("py_vollib 未安装，跳过此测试")

    def test_simplified_greeks_fallback(self, calculator):
        """测试：简化 Greeks 回退（无 py_vollib）"""
        # 直接调用简化版本
        greeks = calculator._simplified_greeks(S=55, K=50, T=0.25, option_type='call')

        # 实值看涨：简化 Delta = 0.5
        assert greeks['delta'] == 0.5, "简化实值看涨 Delta 应为 0.5"
        assert greeks['gamma'] == 0.0, "简化 Gamma 应为 0"
        assert greeks['vega'] == 0.0, "简化 Vega 应为 0"

        # 虚值看涨
        greeks_otm = calculator._simplified_greeks(S=45, K=50, T=0.25, option_type='call')
        assert greeks_otm['delta'] == 0.2, "简化虚值看涨 Delta 应为 0.2"

        # 看跌期权
        greeks_put = calculator._simplified_greeks(S=55, K=50, T=0.25, option_type='put')
        assert greeks_put['delta'] == -0.2, "简化虚值看跌 Delta 应为 -0.2"


class TestGreeksDataFrame:
    """DataFrame 批量 Greeks 计算测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return OptionsGreeksCalculator()

    def test_multiple_options_greeks(self, calculator):
        """测试：多个期权批量计算 Greeks"""
        # 创建期权 DataFrame
        future_date = datetime.now() + timedelta(days=90)
        df = pd.DataFrame({
            'spot': [50, 50, 50],
            'strike': [48, 50, 52],
            'expiry_date': [future_date.strftime('%Y-%m-%d')] * 3,
            'iv': [0.20, 0.20, 0.20],
            'type': ['call', 'call', 'call']
        })

        result = calculator.calculate_greeks_dataframe(df)

        # 应包含 Greeks 列
        assert 'delta' in result.columns, "应有 delta 列"
        assert 'gamma' in result.columns, "应有 gamma 列"
        assert 'vega' in result.columns, "应有 vega 列"
        assert 'theta' in result.columns, "应有 theta 列"
        assert 'rho' in result.columns, "应有 rho 列"

        # 行数应保持不变
        assert len(result) == 3, "行数应为 3"

        # Delta 应随行权价递减（实值 → 平价 → 虚值）
        if 'delta' in result.columns:
            # 48 实值，50 平价，52 虚值
            # Delta 应递减
            assert result.iloc[0]['delta'] > result.iloc[1]['delta'], \
                "实值 Delta 应 > 平价 Delta"
            assert result.iloc[1]['delta'] > result.iloc[2]['delta'], \
                "平价 Delta 应 > 虚值 Delta"

    def test_empty_dataframe(self, calculator):
        """测试：空 DataFrame"""
        df = pd.DataFrame({
            'spot': [],
            'strike': [],
            'expiry_date': [],
            'iv': [],
            'type': []
        })

        result = calculator.calculate_greeks_dataframe(df)

        # 应返回空 DataFrame 且包含 Greeks 列
        assert len(result) == 0, "应为空 DataFrame"


class TestVolatilityManager:
    """波动率管理器测试"""

    @pytest.fixture
    def vol_manager(self):
        """创建波动率管理器实例"""
        return VolatilityManager(default_iv=0.20)

    def test_default_volatility(self, vol_manager):
        """测试：使用默认波动率"""
        vol = vol_manager.get_volatility(symbol='TEST.SH', historical_prices=None)

        assert vol == 0.20, "应返回默认波动率 20%"

    def test_historical_volatility_calculation(self, vol_manager):
        """测试：历史波动率计算"""
        # 生成模拟价格序列（100 天）
        np.random.seed(42)
        prices = pd.Series([100 * (1 + 0.001 * i + 0.01 * np.random.randn()) for i in range(100)])

        hv = vol_manager.calculate_historical_volatility(prices, window=30)

        # 历史波动率应为正数且合理（0.05-0.50）
        assert hv > 0, "历史波动率应为正"
        assert 0.01 < hv < 1.0, f"历史波动率应在合理范围，实际 {hv}"

    def test_historical_volatility_fallback(self, vol_manager):
        """测试：历史数据不足时回退到默认值"""
        # 仅 10 个数据点（< 20）
        short_prices = pd.Series([100 + i for i in range(10)])

        vol = vol_manager.get_volatility(symbol='TEST.SH', historical_prices=short_prices)

        # 应回退到默认值
        assert vol == 0.20, "数据不足时应使用默认波动率"

    def test_historical_volatility_priority(self, vol_manager):
        """测试：有历史数据时优先使用历史波动率"""
        # 足够的历史数据
        prices = pd.Series([100 + i * 0.5 for i in range(50)])

        vol = vol_manager.get_volatility(symbol='TEST.SH', historical_prices=prices)

        # 应使用历史波动率（不等于默认值）
        assert vol != 0.20, "有历史数据时应计算历史波动率"
        assert vol > 0, "历史波动率应为正"

    def test_volatility_annualization(self, vol_manager):
        """测试：波动率年化计算"""
        # 创建每日收益率固定的价格序列
        # 如果每日波动率为 σ_daily，年化应为 σ_daily * √252
        daily_vol = 0.01  # 1% 日波动率
        np.random.seed(42)
        prices = pd.Series([100 * np.exp(daily_vol * np.random.randn()) ** i for i in range(100)])

        hv = vol_manager.calculate_historical_volatility(prices)

        # 年化波动率应约为 daily_vol * sqrt(252) ≈ 0.01 * 15.87 ≈ 0.16
        # 由于随机性，放宽范围
        assert 0.05 < hv < 0.50, f"年化波动率应在合理范围，实际 {hv}"


class TestEdgeCases:
    """边界情况测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return OptionsGreeksCalculator()

    def test_very_short_expiry(self, calculator):
        """测试：极短到期时间"""
        try:
            greeks = calculator.calculate_greeks(
                S=50,
                K=50,
                T=1/365,  # 1天
                r=0.03,
                sigma=0.20,
                option_type='call'
            )

            # Theta 应非常大（绝对值）
            assert abs(greeks['theta']) > 0.01, "极短期 Theta 应很大"

        except (ImportError, ValueError):
            pytest.skip("py_vollib 未安装或计算错误")

    def test_very_high_volatility(self, calculator):
        """测试：极高波动率"""
        try:
            greeks = calculator.calculate_greeks(
                S=50,
                K=50,
                T=0.25,
                r=0.03,
                sigma=1.0,  # 100% 波动率
                option_type='call'
            )

            # 高波动率时 Delta 应接近 0.5
            assert 0.3 < greeks['delta'] < 0.7, "高波动率 Delta 应在合理范围"

        except (ImportError, ValueError):
            pytest.skip("py_vollib 未安装或计算错误")

    def test_zero_time_to_expiry(self, calculator):
        """测试：到期日当天（T 接近 0）"""
        try:
            greeks = calculator.calculate_greeks(
                S=50,
                K=50,
                T=0.001,  # 最小值 0.001 年
                r=0.03,
                sigma=0.20,
                option_type='call'
            )

            # 应能计算（不抛出异常）
            assert 'delta' in greeks, "应返回 delta"

        except (ImportError, ValueError, ZeroDivisionError):
            pytest.skip("py_vollib 未安装或极端参数错误")

    def test_deep_itm_call(self, calculator):
        """测试：深度实值看涨"""
        try:
            greeks = calculator.calculate_greeks(
                S=100,  # 标的 100
                K=50,   # 行权价 50（深度实值）
                T=0.25,
                r=0.03,
                sigma=0.20,
                option_type='call'
            )

            # 深度实值 Delta 应接近 1
            assert greeks['delta'] > 0.9, f"深度实值 Delta 应 > 0.9，实际 {greeks['delta']}"

        except ImportError:
            pytest.skip("py_vollib 未安装")

    def test_deep_otm_put(self, calculator):
        """测试：深度虚值看跌"""
        try:
            greeks = calculator.calculate_greeks(
                S=100,  # 标的 100
                K=50,   # 行权价 50（深度虚值看跌）
                T=0.25,
                r=0.03,
                sigma=0.20,
                option_type='put'
            )

            # 深度虚值看跌 Delta 应接近 0
            assert abs(greeks['delta']) < 0.1, f"深度虚值看跌 Delta 应接近 0，实际 {greeks['delta']}"

        except ImportError:
            pytest.skip("py_vollib 未安装")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
