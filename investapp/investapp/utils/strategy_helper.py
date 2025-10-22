"""策略助手工具 - 统一的策略获取和管理接口。

这个模块提供统一的方法来获取和使用策略，确保所有地方都从策略注册中心获取策略。
所有页面和调度器应该使用这个模块而不是直接导入策略类。
"""

from typing import List, Dict, Any, Optional
import sys
import os

# 确保可以导入策略模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))

from investlib_quant.strategies import StrategyRegistry, StrategyInfo


def get_all_strategies() -> List[StrategyInfo]:
    """获取所有注册的策略。

    Returns:
        策略信息列表
    """
    return StrategyRegistry.list_all()


def get_strategy_by_name(name: str):
    """根据策略名称获取策略实例。

    Args:
        name: 策略名称（如 'ma_breakout_120'）

    Returns:
        策略实例

    Raises:
        ValueError: 如果策略不存在
    """
    return StrategyRegistry.create(name)


def get_strategy_info(name: str) -> Optional[StrategyInfo]:
    """获取策略信息。

    Args:
        name: 策略名称

    Returns:
        策略信息对象，如果不存在则返回 None
    """
    return StrategyRegistry.get(name)


def get_strategy_options_for_ui() -> Dict[str, str]:
    """获取用于UI选择的策略选项。

    Returns:
        字典，键为显示名称，值为策略代码名称

    示例:
        {
            "120日均线突破策略": "ma_breakout_120",
            "市场轮动策略（大盘恐慌买入）": "market_rotation_panic_buy"
        }
    """
    all_strategies = StrategyRegistry.list_all()
    return {s.display_name: s.name for s in all_strategies}


def filter_strategies_by_tag(tag: str) -> List[StrategyInfo]:
    """按标签筛选策略。

    Args:
        tag: 标签名称（如 '趋势跟随', '风险控制' 等）

    Returns:
        匹配的策略列表
    """
    return StrategyRegistry.filter_by_tag(tag)


def filter_strategies_by_risk(risk_level: str) -> List[StrategyInfo]:
    """按风险等级筛选策略。

    Args:
        risk_level: 风险等级（LOW, MEDIUM, HIGH）

    Returns:
        匹配的策略列表
    """
    return StrategyRegistry.filter_by_risk_level(risk_level)


def get_single_asset_strategies() -> List[StrategyInfo]:
    """获取所有单品种策略（非轮动策略）。

    Returns:
        单品种策略列表
    """
    all_strategies = StrategyRegistry.list_all()
    return [s for s in all_strategies if '轮动' not in s.tags]


def get_rotation_strategies() -> List[StrategyInfo]:
    """获取所有轮动策略。

    Returns:
        轮动策略列表
    """
    all_strategies = StrategyRegistry.list_all()
    return [s for s in all_strategies if '轮动' in s.tags or '多品种' in s.tags]


# 向后兼容：提供老策略名称的映射
LEGACY_STRATEGY_MAPPING = {
    'Livermore': 'ma_breakout_120',
    'livermore': 'ma_breakout_120',
    'LivermoreStrategy': 'ma_breakout_120',
    'Kroll': 'ma60_rsi_volatility',
    'kroll': 'ma60_rsi_volatility',
    'KrollStrategy': 'ma60_rsi_volatility',
}


def get_strategy_by_legacy_name(legacy_name: str):
    """根据老的策略名称获取策略（向后兼容）。

    Args:
        legacy_name: 老的策略名称（如 'Livermore', 'Kroll'）

    Returns:
        策略实例

    Raises:
        ValueError: 如果找不到对应的策略
    """
    # 先尝试直接查找
    strategy_info = StrategyRegistry.get(legacy_name)
    if strategy_info:
        return StrategyRegistry.create(legacy_name)

    # 尝试映射
    if legacy_name in LEGACY_STRATEGY_MAPPING:
        new_name = LEGACY_STRATEGY_MAPPING[legacy_name]
        return StrategyRegistry.create(new_name)

    raise ValueError(
        f"找不到策略 '{legacy_name}'。"
        f"可用策略: {[s.name for s in StrategyRegistry.list_all()]}"
    )


def print_strategy_summary():
    """打印策略摘要（用于调试）。"""
    StrategyRegistry.print_summary()


# 示例用法
if __name__ == '__main__':
    print("=" * 60)
    print("策略助手工具测试")
    print("=" * 60)

    # 获取所有策略
    strategies = get_all_strategies()
    print(f"\n共有 {len(strategies)} 个策略:")
    for s in strategies:
        print(f"  - {s.display_name} ({s.name})")

    # 获取UI选项
    print("\nUI选项:")
    options = get_strategy_options_for_ui()
    for display_name, code_name in options.items():
        print(f"  {display_name} → {code_name}")

    # 测试向后兼容
    print("\n测试向后兼容:")
    try:
        old_strategy = get_strategy_by_legacy_name('Livermore')
        print(f"  ✅ 'Livermore' → {old_strategy.name}")
    except Exception as e:
        print(f"  ❌ {e}")
