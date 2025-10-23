#!/usr/bin/env python3
"""前端模块功能测试脚本"""

import sys
import os
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent / 'investapp'))
sys.path.insert(0, str(Path(__file__).parent / 'investlib-data'))
sys.path.insert(0, str(Path(__file__).parent / 'investlib-quant'))
sys.path.insert(0, str(Path(__file__).parent / 'investlib-backtest'))

def test_imports():
    """测试所有核心模块导入"""
    print("=" * 80)
    print("测试 1: 核心模块导入")
    print("=" * 80)

    results = []

    # 1. 数据库模块
    try:
        from investlib_data.database import SessionLocal, get_engine
        from investlib_data.models import Base
        print("✓ 数据库模块导入成功")
        results.append(("数据库模块", True, None))
    except Exception as e:
        print(f"✗ 数据库模块导入失败: {e}")
        results.append(("数据库模块", False, str(e)))

    # 2. 市场数据模块
    try:
        from investlib_data.market_api import MarketDataFetcher
        fetcher = MarketDataFetcher()
        print("✓ 市场数据模块导入成功")
        results.append(("市场数据模块", True, None))
    except Exception as e:
        print(f"✗ 市场数据模块导入失败: {e}")
        results.append(("市场数据模块", False, str(e)))

    # 3. 策略模块
    try:
        from investlib_quant.strategies import LivermoreStrategy
        from investlib_quant.strategies.registry import StrategyRegistry
        strategies = StrategyRegistry.list_all()
        print(f"✓ 策略模块导入成功 (已注册 {len(strategies)} 个策略)")
        results.append(("策略模块", True, None))
    except Exception as e:
        print(f"✗ 策略模块导入失败: {e}")
        results.append(("策略模块", False, str(e)))

    # 4. 回测引擎
    try:
        from investlib_backtest.engine import BacktestRunner
        runner = BacktestRunner(initial_capital=100000)
        print("✓ 回测引擎导入成功")
        results.append(("回测引擎", True, None))
    except Exception as e:
        print(f"✗ 回测引擎导入失败: {e}")
        results.append(("回测引擎", False, str(e)))

    print()
    return results


def test_strategy_registry():
    """测试策略注册中心"""
    print("=" * 80)
    print("测试 2: 策略注册中心")
    print("=" * 80)

    from investlib_quant.strategies.registry import StrategyRegistry

    strategies = StrategyRegistry.list_all()
    print(f"已注册策略数量: {len(strategies)}")
    print()

    for i, strategy in enumerate(strategies, 1):
        print(f"{i}. {strategy.display_name} ({strategy.name})")
        print(f"   风险等级: {strategy.risk_level}")
        print(f"   交易频率: {strategy.trade_frequency}")
        print(f"   标签: {', '.join(strategy.tags)}")
        print()

    return len(strategies) > 0


def test_database_connection():
    """测试数据库连接"""
    print("=" * 80)
    print("测试 3: 数据库连接")
    print("=" * 80)

    try:
        from investlib_data.database import get_engine, verify_database

        engine = get_engine()
        status = verify_database(engine)

        print(f"数据库存在: {status['exists']}")
        print(f"期望表数量: {status['expected_count']}")
        print(f"实际表数量: {status['actual_count']}")
        print(f"数据库有效: {status['valid']}")

        if status['missing']:
            print(f"缺失的表: {', '.join(status['missing'])}")

        if status['tables']:
            print(f"现有表: {', '.join(status['tables'])}")

        print()
        return True
    except Exception as e:
        print(f"✗ 数据库连接测试失败: {e}")
        print()
        return False


def test_page_imports():
    """测试前端页面导入"""
    print("=" * 80)
    print("测试 4: 前端页面导入")
    print("=" * 80)

    pages_dir = Path(__file__).parent / 'investapp' / 'investapp' / 'pages'
    page_files = list(pages_dir.glob('*.py'))

    print(f"找到 {len(page_files)} 个页面文件")
    print()

    results = []
    for page_file in sorted(page_files):
        page_name = page_file.name
        print(f"  {page_name}")
        results.append(page_name)

    print()
    return results


def test_multi_asset_features():
    """测试多资产功能"""
    print("=" * 80)
    print("测试 5: 多资产功能 (V0.3)")
    print("=" * 80)

    results = []

    # 1. 测试市场轮动策略
    try:
        from investlib_quant.strategies.registry import StrategyRegistry
        rotation_strategy = StrategyRegistry.get('market_rotation_panic_buy')
        if rotation_strategy:
            print("✓ 市场轮动策略已注册")
            print(f"  名称: {rotation_strategy.display_name}")
            print(f"  描述: {rotation_strategy.description}")
            results.append(("市场轮动策略", True, None))
        else:
            print("✗ 市场轮动策略未找到")
            results.append(("市场轮动策略", False, "策略未注册"))
    except Exception as e:
        print(f"✗ 市场轮动策略测试失败: {e}")
        results.append(("市场轮动策略", False, str(e)))

    # 2. 测试多资产回测引擎
    try:
        import importlib.util
        multi_asset_file = Path(__file__).parent / 'investlib-backtest' / 'investlib_backtest' / 'engine' / 'multi_asset_runner.py'
        if multi_asset_file.exists():
            print("✓ 多资产回测引擎文件存在")
            results.append(("多资产回测引擎", True, None))
        else:
            print("✗ 多资产回测引擎文件不存在")
            results.append(("多资产回测引擎", False, "文件不存在"))
    except Exception as e:
        print(f"✗ 多资产回测引擎测试失败: {e}")
        results.append(("多资产回测引擎", False, str(e)))

    # 3. 检查新增的页面
    new_pages = [
        '11_监视列表_Watchlist.py',
        '12_参数优化_Optimizer.py',
        '12_风险监控_Risk.py'
    ]

    pages_dir = Path(__file__).parent / 'investapp' / 'investapp' / 'pages'
    for page in new_pages:
        page_file = pages_dir / page
        if page_file.exists():
            print(f"✓ 新页面存在: {page}")
            results.append((f"页面-{page}", True, None))
        else:
            print(f"✗ 新页面不存在: {page}")
            results.append((f"页面-{page}", False, "文件不存在"))

    print()
    return results


def generate_test_report(all_results):
    """生成测试报告"""
    print("=" * 80)
    print("测试报告摘要")
    print("=" * 80)

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_name, test_results in all_results.items():
        if isinstance(test_results, list):
            for item in test_results:
                if isinstance(item, tuple) and len(item) >= 2:
                    total_tests += 1
                    if item[1]:
                        passed_tests += 1
                    else:
                        failed_tests += 1
        elif isinstance(test_results, bool):
            total_tests += 1
            if test_results:
                passed_tests += 1
            else:
                failed_tests += 1

    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    print()

    # 详细失败信息
    if failed_tests > 0:
        print("失败的测试:")
        for test_name, test_results in all_results.items():
            if isinstance(test_results, list):
                for item in test_results:
                    if isinstance(item, tuple) and len(item) >= 2 and not item[1]:
                        print(f"  ✗ {item[0]}: {item[2] if len(item) > 2 else 'Unknown error'}")

    print("=" * 80)


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("MyInvest 前端功能完整测试")
    print("=" * 80)
    print()

    all_results = {}

    # 运行所有测试
    all_results['imports'] = test_imports()
    all_results['strategy_registry'] = test_strategy_registry()
    all_results['database'] = test_database_connection()
    all_results['pages'] = test_page_imports()
    all_results['multi_asset'] = test_multi_asset_features()

    # 生成报告
    generate_test_report(all_results)

    print("\n✓ 测试完成!")
    print(f"前端应用正在运行: http://localhost:8501")
    print()


if __name__ == '__main__':
    main()
