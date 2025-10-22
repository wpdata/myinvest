#!/usr/bin/env python3
"""测试所有关键导入是否正常工作。"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'investlib-quant/src'))

def test_strategy_imports():
    """测试策略模块导入。"""
    print("=" * 60)
    print("测试策略模块导入...")
    print("=" * 60)

    try:
        from investlib_quant.strategies import (
            StrategyRegistry,
            StrategyInfo,
            BaseStrategy,
            LivermoreStrategy,
            MarketRotationStrategy
        )
        print("✅ 策略模块导入成功")

        # 测试策略注册
        strategies = StrategyRegistry.list_all()
        print(f"✅ 已注册策略数量: {len(strategies)}")

        for s in strategies:
            print(f"   - {s.display_name} ({s.name})")

        return True
    except Exception as e:
        print(f"❌ 策略模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backtest_imports():
    """测试回测模块导入。"""
    print("\n" + "=" * 60)
    print("测试回测模块导入...")
    print("=" * 60)

    try:
        from investlib_backtest.engine.backtest_runner import BacktestRunner
        from investlib_backtest.engine.rotation_backtest import RotationBacktestRunner
        print("✅ 回测模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 回测模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_imports():
    """测试数据模块导入。"""
    print("\n" + "=" * 60)
    print("测试数据模块导入...")
    print("=" * 60)

    try:
        from investlib_data.market_api import MarketDataFetcher
        from investlib_data.cache_manager import CacheManager
        print("✅ 数据模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 数据模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streamlit_page_imports():
    """测试 Streamlit 页面导入（不运行）。"""
    print("\n" + "=" * 60)
    print("测试 Streamlit 页面导入...")
    print("=" * 60)

    # 注意：不能直接导入 Streamlit 页面，因为它们会执行
    # 我们只检查文件是否存在
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pages = [
        os.path.join(base_dir, "investapp/investapp/pages/9_strategies.py"),
        os.path.join(base_dir, "investapp/investapp/pages/10_rotation_strategy.py")
    ]

    all_exist = True
    for page in pages:
        if os.path.exists(page):
            print(f"✅ 页面文件存在: {page}")
        else:
            print(f"❌ 页面文件不存在: {page}")
            all_exist = False

    return all_exist


def main():
    """运行所有测试。"""
    print("\n" + "=" * 60)
    print("MyInvest 导入测试")
    print("=" * 60 + "\n")

    results = []

    # 运行所有测试
    results.append(("策略模块", test_strategy_imports()))
    results.append(("回测模块", test_backtest_imports()))
    results.append(("数据模块", test_data_imports()))
    results.append(("页面文件", test_streamlit_page_imports()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！可以启动 Streamlit 应用。")
        print("\n启动命令:")
        print("cd investapp && streamlit run investapp/app.py")
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
    print("=" * 60 + "\n")

    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
