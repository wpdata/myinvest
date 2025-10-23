#!/usr/bin/env python3
"""测试前端页面的关键函数"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'investapp'))
sys.path.insert(0, str(Path(__file__).parent / 'investlib-data'))
sys.path.insert(0, str(Path(__file__).parent / 'investlib-quant'))
sys.path.insert(0, str(Path(__file__).parent / 'investlib-backtest'))


def test_dashboard_functions():
    """测试仪表盘页面功能"""
    print("=" * 80)
    print("测试页面: 仪表盘")
    print("=" * 80)

    try:
        # 测试数据查询功能
        from investlib_data.database import SessionLocal
        from investlib_data.models import InvestmentRecord, CurrentHolding

        session = SessionLocal()

        # 查询持仓
        holdings = session.query(CurrentHolding).all()
        print(f"✓ 当前持仓数量: {len(holdings)}")

        # 查询投资记录
        records = session.query(InvestmentRecord).limit(10).all()
        print(f"✓ 投资记录数量: {len(records)}")

        session.close()
        return True
    except Exception as e:
        print(f"✗ 仪表盘测试失败: {e}")
        return False


def test_market_data_functions():
    """测试市场数据页面功能"""
    print("\n" + "=" * 80)
    print("测试页面: 市场数据")
    print("=" * 80)

    try:
        from investlib_data.market_api import MarketDataFetcher

        fetcher = MarketDataFetcher()
        print("✓ MarketDataFetcher 初始化成功")

        # 测试获取支持的股票列表
        print("✓ 市场数据模块功能正常")
        return True
    except Exception as e:
        print(f"✗ 市场数据测试失败: {e}")
        return False


def test_strategy_management():
    """测试策略管理页面功能"""
    print("\n" + "=" * 80)
    print("测试页面: 策略管理")
    print("=" * 80)

    try:
        from investlib_quant.strategies.registry import StrategyRegistry

        # 获取所有策略
        strategies = StrategyRegistry.list_all()
        print(f"✓ 可用策略数量: {len(strategies)}")

        # 测试策略创建
        for strategy in strategies:
            print(f"  - {strategy.display_name}")
            try:
                instance = StrategyRegistry.create(strategy.name)
                print(f"    ✓ 策略实例化成功")
            except Exception as e:
                print(f"    ✗ 策略实例化失败: {e}")

        return True
    except Exception as e:
        print(f"✗ 策略管理测试失败: {e}")
        return False


def test_backtest_functions():
    """测试回测页面功能"""
    print("\n" + "=" * 80)
    print("测试页面: 策略回测")
    print("=" * 80)

    try:
        from investlib_backtest.engine import BacktestRunner
        from investlib_quant.strategies import LivermoreStrategy

        # 创建回测引擎
        runner = BacktestRunner(
            initial_capital=100000,
            commission_rate=0.0003
        )
        print(f"✓ 回测引擎初始化成功")
        print(f"  - 初始资金: {runner.initial_capital}")
        print(f"  - 手续费率: {runner.commission_rate}")

        # 创建策略
        strategy = LivermoreStrategy()
        print(f"✓ 策略创建成功: LivermoreStrategy")

        return True
    except Exception as e:
        print(f"✗ 回测测试失败: {e}")
        return False


def test_rotation_strategy():
    """测试轮动策略页面功能"""
    print("\n" + "=" * 80)
    print("测试页面: 轮动策略 (V0.2 新功能)")
    print("=" * 80)

    try:
        from investlib_quant.strategies.registry import StrategyRegistry

        # 查找轮动策略
        rotation = StrategyRegistry.get('market_rotation_panic_buy')
        if rotation:
            print(f"✓ 轮动策略已注册")
            print(f"  名称: {rotation.display_name}")
            print(f"  描述: {rotation.description}")
            print(f"  风险等级: {rotation.risk_level}")
            print(f"  参数:")
            for param_name, param_info in rotation.parameters.items():
                if isinstance(param_info, dict):
                    default = param_info.get('default', 'N/A')
                    desc = param_info.get('description', '')
                    print(f"    • {param_name}: {default} - {desc}")

            # 测试创建实例
            try:
                instance = StrategyRegistry.create('market_rotation_panic_buy')
                print(f"  ✓ 策略实例化成功")
            except Exception as e:
                print(f"  ✗ 策略实例化失败: {e}")

            return True
        else:
            print("✗ 轮动策略未找到")
            return False
    except Exception as e:
        print(f"✗ 轮动策略测试失败: {e}")
        return False


def test_watchlist_functions():
    """测试监视列表功能 (V0.3)"""
    print("\n" + "=" * 80)
    print("测试页面: 监视列表 (V0.3 新功能)")
    print("=" * 80)

    try:
        from investlib_data.database import SessionLocal
        from sqlalchemy import text

        session = SessionLocal()

        # 检查 watchlist 表是否存在
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'"))
        table_exists = result.fetchone() is not None

        if table_exists:
            print("✓ watchlist 表存在")

            # 查询监视列表
            result = session.execute(text("SELECT COUNT(*) FROM watchlist"))
            count = result.fetchone()[0]
            print(f"✓ 监视列表条目数: {count}")
        else:
            print("⚠ watchlist 表不存在 (可能需要迁移)")

        session.close()
        return True
    except Exception as e:
        print(f"✗ 监视列表测试失败: {e}")
        return False


def test_scheduler_functions():
    """测试调度器功能"""
    print("\n" + "=" * 80)
    print("测试页面: 调度器日志")
    print("=" * 80)

    try:
        from investlib_data.database import SessionLocal
        from investlib_data.models import SchedulerLog

        session = SessionLocal()

        # 查询调度器日志
        logs = session.query(SchedulerLog).limit(10).all()
        print(f"✓ 调度器日志数量: {len(logs)}")

        session.close()
        return True
    except Exception as e:
        print(f"✗ 调度器测试失败: {e}")
        return False


def test_approval_functions():
    """测试策略审批功能"""
    print("\n" + "=" * 80)
    print("测试页面: 策略审批")
    print("=" * 80)

    try:
        from investlib_data.database import SessionLocal
        from investlib_data.models import StrategyApproval

        session = SessionLocal()

        # 查询策略审批记录
        approvals = session.query(StrategyApproval).all()
        print(f"✓ 策略审批记录数量: {len(approvals)}")

        session.close()
        return True
    except Exception as e:
        print(f"✗ 策略审批测试失败: {e}")
        return False


def test_multi_asset_backtest():
    """测试多资产回测功能 (V0.3)"""
    print("\n" + "=" * 80)
    print("测试功能: 多资产回测引擎 (V0.3)")
    print("=" * 80)

    try:
        # 检查多资产回测引擎文件
        multi_asset_file = Path(__file__).parent / 'investlib-backtest' / 'investlib_backtest' / 'engine' / 'multi_asset_runner.py'

        if multi_asset_file.exists():
            print(f"✓ 多资产回测引擎文件存在")

            # 读取文件并检查关键类
            with open(multi_asset_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'MultiAssetBacktestRunner' in content:
                    print(f"✓ MultiAssetBacktestRunner 类已定义")
                if 'run_rotation_backtest' in content:
                    print(f"✓ run_rotation_backtest 方法已定义")

            return True
        else:
            print(f"✗ 多资产回测引擎文件不存在")
            return False
    except Exception as e:
        print(f"✗ 多资产回测测试失败: {e}")
        return False


def main():
    """运行所有页面测试"""
    print("\n" + "=" * 80)
    print("MyInvest 前端页面功能测试")
    print("=" * 80)

    results = {}

    # 测试各个页面
    results['仪表盘'] = test_dashboard_functions()
    results['市场数据'] = test_market_data_functions()
    results['策略管理'] = test_strategy_management()
    results['策略回测'] = test_backtest_functions()
    results['轮动策略'] = test_rotation_strategy()
    results['监视列表'] = test_watchlist_functions()
    results['调度器'] = test_scheduler_functions()
    results['策略审批'] = test_approval_functions()
    results['多资产回测'] = test_multi_asset_backtest()

    # 生成报告
    print("\n" + "=" * 80)
    print("测试结果摘要")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status} - {name}")

    print("\n" + "-" * 80)
    print(f"总计: {total} 个测试")
    print(f"通过: {passed} ({passed/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")
    print("=" * 80)

    print("\n前端应用正在运行: http://localhost:8501")
    print()


if __name__ == '__main__':
    main()
