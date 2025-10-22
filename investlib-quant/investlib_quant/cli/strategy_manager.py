#!/usr/bin/env python3
"""策略管理CLI工具。

提供命令行界面来查看、搜索和管理投资策略。

使用方法：
    # 列出所有策略
    python -m investlib_quant.cli.strategy_manager list

    # 查看特定策略
    python -m investlib_quant.cli.strategy_manager show ma_breakout_120

    # 按标签筛选
    python -m investlib_quant.cli.strategy_manager filter --tag 趋势跟随

    # 按风险等级筛选
    python -m investlib_quant.cli.strategy_manager filter --risk LOW
"""

import argparse
import sys
from typing import Optional


def list_strategies():
    """列出所有策略。"""
    from investlib_quant.strategies import StrategyRegistry

    StrategyRegistry.print_summary()


def show_strategy(name: str):
    """显示特定策略的详细信息。"""
    from investlib_quant.strategies import StrategyRegistry

    StrategyRegistry.print_summary(name=name)


def filter_strategies(tag: Optional[str] = None, risk: Optional[str] = None):
    """按条件筛选策略。"""
    from investlib_quant.strategies import StrategyRegistry

    if tag:
        strategies = StrategyRegistry.filter_by_tag(tag)
        print(f"\n📋 包含标签 '{tag}' 的策略（共 {len(strategies)} 个）:\n")
    elif risk:
        strategies = StrategyRegistry.filter_by_risk_level(risk)
        print(f"\n📋 风险等级为 '{risk}' 的策略（共 {len(strategies)} 个）:\n")
    else:
        print("❌ 请指定筛选条件（--tag 或 --risk）")
        return

    if not strategies:
        print("未找到匹配的策略")
        return

    for i, info in enumerate(strategies, 1):
        print(f"{i}. {info.display_name} ({info.name})")
        print(f"   {info.description}")
        print(f"   标签: {', '.join(info.tags)}")
        print()


def list_tags():
    """列出所有可用的标签。"""
    from investlib_quant.strategies import StrategyRegistry

    all_strategies = StrategyRegistry.list_all()
    all_tags = set()
    for strategy in all_strategies:
        all_tags.update(strategy.tags)

    print("\n📌 所有可用标签:\n")
    for tag in sorted(all_tags):
        count = len([s for s in all_strategies if tag in s.tags])
        print(f"  • {tag} ({count} 个策略)")
    print()


def compare_strategies(*names):
    """对比多个策略。"""
    from investlib_quant.strategies import StrategyRegistry

    if not names:
        print("❌ 请指定至少一个策略名称")
        return

    strategies = [StrategyRegistry.get(name) for name in names]
    strategies = [s for s in strategies if s is not None]

    if not strategies:
        print("❌ 未找到任何匹配的策略")
        return

    print(f"\n{'='*100}")
    print(f"📊 策略对比 - {len(strategies)} 个策略")
    print(f"{'='*100}\n")

    # 创建对比表格
    print(f"{'属性':<20} | " + " | ".join([f"{s.display_name[:15]:<15}" for s in strategies]))
    print("-" * 100)

    # 风险等级
    print(f"{'风险等级':<20} | " + " | ".join([f"{s.risk_level:<15}" for s in strategies]))

    # 持仓周期
    print(f"{'持仓周期':<20} | " + " | ".join([f"{s.typical_holding_period[:15]:<15}" for s in strategies]))

    # 交易频率
    print(f"{'交易频率':<20} | " + " | ".join([f"{s.trade_frequency:<15}" for s in strategies]))

    # 核心逻辑
    print("\n详细对比:\n")
    for strategy in strategies:
        print(f"【{strategy.display_name}】")
        print(f"  逻辑: {strategy.logic}")
        print(f"  标签: {', '.join(strategy.tags)}")
        print(f"  适用: {', '.join(strategy.suitable_for)}")
        print()


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(
        description="投资策略管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s list                              # 列出所有策略
  %(prog)s show ma_breakout_120              # 查看特定策略
  %(prog)s filter --tag 趋势跟随              # 按标签筛选
  %(prog)s filter --risk LOW                 # 按风险等级筛选
  %(prog)s tags                              # 列出所有标签
  %(prog)s compare ma_breakout_120 ma60_rsi_volatility  # 对比策略
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # list 命令
    subparsers.add_parser('list', help='列出所有策略')

    # show 命令
    show_parser = subparsers.add_parser('show', help='显示特定策略详情')
    show_parser.add_argument('name', help='策略名称')

    # filter 命令
    filter_parser = subparsers.add_parser('filter', help='筛选策略')
    filter_group = filter_parser.add_mutually_exclusive_group(required=True)
    filter_group.add_argument('--tag', help='按标签筛选')
    filter_group.add_argument('--risk', help='按风险等级筛选 (LOW/MEDIUM/HIGH)')

    # tags 命令
    subparsers.add_parser('tags', help='列出所有可用标签')

    # compare 命令
    compare_parser = subparsers.add_parser('compare', help='对比多个策略')
    compare_parser.add_argument('strategies', nargs='+', help='策略名称列表')

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    if args.command == 'list':
        list_strategies()
    elif args.command == 'show':
        show_strategy(args.name)
    elif args.command == 'filter':
        filter_strategies(tag=args.tag, risk=args.risk)
    elif args.command == 'tags':
        list_tags()
    elif args.command == 'compare':
        compare_strategies(*args.strategies)


if __name__ == '__main__':
    main()
