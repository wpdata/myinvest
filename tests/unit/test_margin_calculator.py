"""
单元测试：保证金计算器
测试 investlib-margin/calculator.py 中的保证金计算逻辑
"""

import pytest
import sys
from pathlib import Path

# 添加 investlib-margin 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'investlib-margin'))

from investlib_margin.calculator import MarginCalculator


class TestMarginCalculation:
    """保证金计算测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return MarginCalculator()

    def test_futures_margin_calculation(self, calculator):
        """测试：期货保证金计算"""
        # IF2506 期货：价格5000，1手，乘数300，保证金率15%
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=1,
            price=5000,
            multiplier=300,
            margin_rate=0.15
        )

        expected = 1 * 5000 * 300 * 0.15  # 225,000
        assert margin == pytest.approx(expected), f"期货保证金应为 ¥{expected:,.2f}"

    def test_option_margin_calculation(self, calculator):
        """测试：期权保证金计算"""
        # 卖出期权：价格3，10手，乘数10000，保证金率20%
        margin = calculator.calculate_margin(
            contract_type='option',
            quantity=10,
            price=3,
            multiplier=10000,
            margin_rate=0.20
        )

        expected = 10 * 3 * 10000 * 0.20  # 60,000
        assert margin == pytest.approx(expected), f"期权保证金应为 ¥{expected:,.2f}"

    def test_negative_quantity_margin(self, calculator):
        """测试：负数量（空头）保证金计算"""
        # 空头：-1手
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=-1,
            price=4000,
            multiplier=300,
            margin_rate=0.15
        )

        expected = 1 * 4000 * 300 * 0.15  # 使用绝对值，180,000
        assert margin == pytest.approx(expected), "空头保证金应使用数量绝对值"

    def test_zero_quantity_margin(self, calculator):
        """测试：零数量保证金"""
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=0,
            price=5000,
            multiplier=300,
            margin_rate=0.15
        )

        assert margin == 0, "零数量保证金应为 0"

    def test_different_margin_rates(self, calculator):
        """测试：不同保证金率"""
        base_params = {
            'contract_type': 'futures',
            'quantity': 1,
            'price': 5000,
            'multiplier': 300
        }

        # 10% 保证金率
        margin_10 = calculator.calculate_margin(**base_params, margin_rate=0.10)
        expected_10 = 1 * 5000 * 300 * 0.10  # 150,000

        # 20% 保证金率
        margin_20 = calculator.calculate_margin(**base_params, margin_rate=0.20)
        expected_20 = 1 * 5000 * 300 * 0.20  # 300,000

        assert margin_10 == pytest.approx(expected_10), "10% 保证金率计算错误"
        assert margin_20 == pytest.approx(expected_20), "20% 保证金率计算错误"
        assert margin_20 == pytest.approx(margin_10 * 2), "20% 应为 10% 的两倍"


class TestLiquidationPrice:
    """强平价格计算测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return MarginCalculator()

    def test_long_liquidation_price(self, calculator):
        """测试：多头强平价格"""
        # 多头：入场5000，保证金15%，强平阈值10%
        liq_price = calculator.calculate_liquidation_price(
            entry_price=5000,
            direction='long',
            margin_rate=0.15,
            force_close_margin_rate=0.10
        )

        # 多头强平价 = 5000 * (1 - (0.15 - 0.10)) = 5000 * 0.95 = 4750
        expected = 5000 * 0.95
        assert liq_price == pytest.approx(expected), f"多头强平价应为 {expected}"

    def test_short_liquidation_price(self, calculator):
        """测试：空头强平价格"""
        # 空头：入场5000，保证金15%，强平阈值10%
        liq_price = calculator.calculate_liquidation_price(
            entry_price=5000,
            direction='short',
            margin_rate=0.15,
            force_close_margin_rate=0.10
        )

        # 空头强平价 = 5000 * (1 + (0.15 - 0.10)) = 5000 * 1.05 = 5250
        expected = 5000 * 1.05
        assert liq_price == pytest.approx(expected), f"空头强平价应为 {expected}"

    def test_tighter_margin_buffer(self, calculator):
        """测试：更紧的保证金缓冲"""
        # 保证金率12%，强平阈值10%（缓冲仅2%）
        liq_price = calculator.calculate_liquidation_price(
            entry_price=5000,
            direction='long',
            margin_rate=0.12,
            force_close_margin_rate=0.10
        )

        # 缓冲 = 0.12 - 0.10 = 0.02
        # 强平价 = 5000 * (1 - 0.02) = 4900
        expected = 5000 * 0.98
        assert liq_price == pytest.approx(expected), f"强平价应为 {expected}"

    def test_wider_margin_buffer(self, calculator):
        """测试：更宽的保证金缓冲"""
        # 保证金率30%，强平阈值10%（缓冲20%）
        liq_price = calculator.calculate_liquidation_price(
            entry_price=5000,
            direction='long',
            margin_rate=0.30,
            force_close_margin_rate=0.10
        )

        # 缓冲 = 0.30 - 0.10 = 0.20
        # 强平价 = 5000 * (1 - 0.20) = 4000
        expected = 5000 * 0.80
        assert liq_price == pytest.approx(expected), f"强平价应为 {expected}"


class TestForcedLiquidation:
    """强制平仓检测测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return MarginCalculator()

    def test_long_forced_liquidation_triggered(self, calculator):
        """测试：多头触发强平"""
        # 多头强平价 = 4750
        liquidation_price = 4750

        # 当前价格 4700 < 4750，应触发强平
        is_liquidated = calculator.is_forced_liquidation(
            current_price=4700,
            liquidation_price=liquidation_price,
            direction='long'
        )

        assert is_liquidated is True, "多头价格跌破强平价应触发强平"

    def test_long_forced_liquidation_not_triggered(self, calculator):
        """测试：多头未触发强平"""
        # 多头强平价 = 4750
        liquidation_price = 4750

        # 当前价格 4800 > 4750，不应触发强平
        is_liquidated = calculator.is_forced_liquidation(
            current_price=4800,
            liquidation_price=liquidation_price,
            direction='long'
        )

        assert is_liquidated is False, "多头价格高于强平价不应触发强平"

    def test_long_forced_liquidation_at_threshold(self, calculator):
        """测试：多头恰好在强平价"""
        # 多头强平价 = 4750
        liquidation_price = 4750

        # 当前价格 = 4750，应触发强平 (<=)
        is_liquidated = calculator.is_forced_liquidation(
            current_price=4750,
            liquidation_price=liquidation_price,
            direction='long'
        )

        assert is_liquidated is True, "多头价格等于强平价应触发强平"

    def test_short_forced_liquidation_triggered(self, calculator):
        """测试：空头触发强平"""
        # 空头强平价 = 5250
        liquidation_price = 5250

        # 当前价格 5300 > 5250，应触发强平
        is_liquidated = calculator.is_forced_liquidation(
            current_price=5300,
            liquidation_price=liquidation_price,
            direction='short'
        )

        assert is_liquidated is True, "空头价格突破强平价应触发强平"

    def test_short_forced_liquidation_not_triggered(self, calculator):
        """测试：空头未触发强平"""
        # 空头强平价 = 5250
        liquidation_price = 5250

        # 当前价格 5200 < 5250，不应触发强平
        is_liquidated = calculator.is_forced_liquidation(
            current_price=5200,
            liquidation_price=liquidation_price,
            direction='short'
        )

        assert is_liquidated is False, "空头价格低于强平价不应触发强平"


class TestMarginRatio:
    """保证金使用率测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return MarginCalculator()

    def test_margin_ratio_50_percent(self, calculator):
        """测试：50% 保证金使用率"""
        ratio = calculator.calculate_margin_ratio(
            account_equity=100000,
            margin_used=50000
        )

        assert ratio == pytest.approx(0.5), "保证金使用率应为 50%"

    def test_margin_ratio_100_percent(self, calculator):
        """测试：100% 保证金使用率"""
        ratio = calculator.calculate_margin_ratio(
            account_equity=100000,
            margin_used=100000
        )

        assert ratio == pytest.approx(1.0), "保证金使用率应为 100%"

    def test_margin_ratio_over_100_percent(self, calculator):
        """测试：超过 100% 保证金使用率（应限制在 100%）"""
        ratio = calculator.calculate_margin_ratio(
            account_equity=100000,
            margin_used=150000
        )

        # 应限制在 1.0 (100%)
        assert ratio == pytest.approx(1.0), "保证金使用率应限制在 100%"

    def test_margin_ratio_zero_margin(self, calculator):
        """测试：零保证金使用"""
        ratio = calculator.calculate_margin_ratio(
            account_equity=100000,
            margin_used=0
        )

        assert ratio == 0.0, "零保证金使用率应为 0"

    def test_margin_ratio_zero_equity(self, calculator):
        """测试：零权益（特殊情况）"""
        ratio = calculator.calculate_margin_ratio(
            account_equity=0,
            margin_used=50000
        )

        # 权益为 0 时，应返回无穷大（但限制在 1.0）
        assert ratio == pytest.approx(1.0), "权益为 0 时保证金使用率应为 100%"

    def test_margin_ratio_negative_equity(self, calculator):
        """测试：负权益（爆仓情况）"""
        ratio = calculator.calculate_margin_ratio(
            account_equity=-10000,
            margin_used=50000
        )

        # 负权益时，应返回 1.0（已爆仓）
        assert ratio == pytest.approx(1.0), "负权益时保证金使用率应为 100%"


class TestEdgeCases:
    """边界情况测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return MarginCalculator()

    def test_very_high_price(self, calculator):
        """测试：极高价格"""
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=1,
            price=1000000,
            multiplier=1,
            margin_rate=0.15
        )

        expected = 1 * 1000000 * 1 * 0.15
        assert margin == pytest.approx(expected), "极高价格应正确计算"

    def test_very_low_price(self, calculator):
        """测试：极低价格"""
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=100,
            price=0.01,
            multiplier=1,
            margin_rate=0.15
        )

        expected = 100 * 0.01 * 1 * 0.15
        assert margin == pytest.approx(expected), "极低价格应正确计算"

    def test_high_multiplier(self, calculator):
        """测试：高乘数"""
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=1,
            price=100,
            multiplier=10000,
            margin_rate=0.15
        )

        expected = 1 * 100 * 10000 * 0.15  # 150,000
        assert margin == pytest.approx(expected), "高乘数应正确计算"

    def test_low_margin_rate(self, calculator):
        """测试：极低保证金率"""
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=1,
            price=5000,
            multiplier=300,
            margin_rate=0.01  # 1%
        )

        expected = 1 * 5000 * 300 * 0.01  # 15,000
        assert margin == pytest.approx(expected), "极低保证金率应正确计算"

    def test_high_margin_rate(self, calculator):
        """测试：极高保证金率"""
        margin = calculator.calculate_margin(
            contract_type='futures',
            quantity=1,
            price=5000,
            multiplier=300,
            margin_rate=0.50  # 50%
        )

        expected = 1 * 5000 * 300 * 0.50  # 750,000
        assert margin == pytest.approx(expected), "极高保证金率应正确计算"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
