"""投资策略模块 - 所有策略的统一入口。

包含各种投资策略的实现和策略管理系统。

可用策略：
- LivermoreStrategy: 120日均线突破策略
- KrollStrategy: 风险控制策略（60日均线+RSI）
- MarketRotationStrategy: 市场轮动策略（多品种）

策略管理：
- StrategyRegistry: 策略注册中心
- StrategyInfo: 策略信息类
"""

from .base import BaseStrategy
from .livermore import LivermoreStrategy
from .market_rotation import MarketRotationStrategy
from .registry import StrategyRegistry, StrategyInfo

# 尝试导入Kroll策略（在旧位置）
try:
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from investlib_quant.kroll_strategy import KrollStrategy, register_strategy as register_kroll
    register_kroll()  # 手动触发注册
except ImportError:
    KrollStrategy = None

__all__ = [
    "BaseStrategy",
    "LivermoreStrategy",
    "MarketRotationStrategy",
    "KrollStrategy",
    "StrategyRegistry",
    "StrategyInfo",
]

# 便捷函数
def get_all_strategies():
    """获取所有已注册的策略。"""
    return StrategyRegistry.list_all()

def get_strategy(name: str):
    """根据名称获取策略实例。"""
    return StrategyRegistry.create(name)
