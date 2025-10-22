"""投资策略模块。

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

__all__ = [
    "BaseStrategy",
    "LivermoreStrategy",
    "MarketRotationStrategy",
    "StrategyRegistry",
    "StrategyInfo",
]
