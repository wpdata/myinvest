"""策略注册中心 - 管理和展示所有投资策略。

这个模块提供了一个中心化的策略管理系统，允许：
1. 注册和发现所有可用策略
2. 查看策略的详细说明、参数和使用示例
3. 获取策略的实例化方法
"""

from typing import Dict, List, Type, Any, Optional
from dataclasses import dataclass
from abc import ABC
import inspect


@dataclass
class StrategyInfo:
    """策略信息类。"""

    # 基本信息
    name: str  # 策略标识名称（用于代码中引用）
    display_name: str  # 策略显示名称（用于UI展示）
    description: str  # 策略简短描述

    # 详细说明
    logic: str  # 策略核心逻辑说明
    parameters: Dict[str, Any]  # 默认参数和说明

    # 特征标签
    tags: List[str]  # 策略标签（如：趋势跟随、价值投资、轮动策略等）
    risk_level: str  # 风险等级：LOW, MEDIUM, HIGH

    # 适用场景
    suitable_for: List[str]  # 适用的市场环境或品种

    # 实现细节
    strategy_class: Type  # 策略类
    example_code: str  # 使用示例代码

    # 性能特征
    typical_holding_period: str  # 典型持仓周期
    trade_frequency: str  # 交易频率：HIGH, MEDIUM, LOW


class StrategyRegistry:
    """策略注册中心。

    使用示例：
        # 获取所有策略
        all_strategies = StrategyRegistry.list_all()

        # 根据名称获取策略
        strategy_info = StrategyRegistry.get('ma_breakout_120')

        # 创建策略实例
        strategy = StrategyRegistry.create('ma_breakout_120', ma_period=120)

        # 按标签筛选
        trend_strategies = StrategyRegistry.filter_by_tag('趋势跟随')
    """

    _strategies: Dict[str, StrategyInfo] = {}

    @classmethod
    def register(cls, info: StrategyInfo):
        """注册一个策略。"""
        cls._strategies[info.name] = info

    @classmethod
    def get(cls, name: str) -> Optional[StrategyInfo]:
        """根据名称获取策略信息。"""
        return cls._strategies.get(name)

    @classmethod
    def list_all(cls) -> List[StrategyInfo]:
        """获取所有注册的策略。"""
        return list(cls._strategies.values())

    @classmethod
    def filter_by_tag(cls, tag: str) -> List[StrategyInfo]:
        """根据标签筛选策略。"""
        return [
            info for info in cls._strategies.values()
            if tag in info.tags
        ]

    @classmethod
    def filter_by_risk_level(cls, risk_level: str) -> List[StrategyInfo]:
        """根据风险等级筛选策略。"""
        return [
            info for info in cls._strategies.values()
            if info.risk_level == risk_level
        ]

    @classmethod
    def create(cls, name: str, **kwargs) -> Any:
        """创建策略实例。

        Args:
            name: 策略名称
            **kwargs: 策略参数（覆盖默认值）

        Returns:
            策略实例

        Raises:
            ValueError: 如果策略不存在
        """
        info = cls.get(name)
        if not info:
            raise ValueError(f"策略不存在: {name}")

        # 合并默认参数和用户参数
        params = {**info.parameters, **kwargs}

        # 创建实例
        return info.strategy_class(**params)

    @classmethod
    def print_summary(cls, name: Optional[str] = None):
        """打印策略摘要。

        Args:
            name: 策略名称。如果为 None，打印所有策略
        """
        if name:
            strategies = [cls.get(name)] if cls.get(name) else []
            if not strategies:
                print(f"❌ 策略不存在: {name}")
                return
        else:
            strategies = cls.list_all()

        if not strategies:
            print("📋 暂无注册的策略")
            return

        print(f"\n{'='*80}")
        print(f"📊 投资策略注册中心 - 共 {len(strategies)} 个策略")
        print(f"{'='*80}\n")

        for i, info in enumerate(strategies, 1):
            print(f"\n{i}. 【{info.display_name}】 ({info.name})")
            print(f"   {'-'*70}")
            print(f"   📝 描述: {info.description}")
            print(f"   🎯 逻辑: {info.logic}")
            print(f"   🏷️  标签: {', '.join(info.tags)}")
            print(f"   ⚠️  风险: {info.risk_level}")
            print(f"   📅 持仓周期: {info.typical_holding_period}")
            print(f"   🔄 交易频率: {info.trade_frequency}")
            print(f"   ✅ 适用于: {', '.join(info.suitable_for)}")

            # 打印参数
            if info.parameters:
                print(f"\n   ⚙️  参数:")
                for param_name, param_info in info.parameters.items():
                    if isinstance(param_info, dict):
                        default = param_info.get('default', 'N/A')
                        desc = param_info.get('description', '')
                        print(f"      • {param_name}: {default}  # {desc}")
                    else:
                        print(f"      • {param_name}: {param_info}")

            # 打印示例代码
            if info.example_code:
                print(f"\n   💻 使用示例:")
                for line in info.example_code.strip().split('\n'):
                    print(f"      {line}")

        print(f"\n{'='*80}\n")
