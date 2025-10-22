#!/usr/bin/env python3
"""验证系统中所有地方都使用统一的策略注册中心。"""

import os
import re
from pathlib import Path


def check_file_for_old_imports(file_path):
    """检查文件是否使用了旧的策略导入方式。"""
    old_imports = [
        r'from investlib_quant\.livermore_strategy import LivermoreStrategy',
        r'from investlib_quant\.kroll_strategy import KrollStrategy',
        r'from investlib_quant\.fusion_strategy import FusionStrategy',
        r'LivermoreStrategy\(\)',
        r'KrollStrategy\(\)',
        r'FusionStrategy\(',
    ]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []
        for pattern in old_imports:
            matches = re.findall(pattern, content)
            if matches:
                issues.append(pattern)

        return issues
    except Exception as e:
        return None


def main():
    print("=" * 80)
    print("验证策略使用统一性")
    print("=" * 80)

    # 需要检查的目录
    check_dirs = [
        "/Users/pw/ai/myinvest/investapp/investapp/pages",
        "/Users/pw/ai/myinvest/investapp/investapp/scheduler",
        "/Users/pw/ai/myinvest/investapp/investapp/utils",
    ]

    # 排除的文件
    exclude_files = [
        'strategy_helper.py',  # 这个文件有向后兼容代码
    ]

    total_files = 0
    files_with_issues = []

    for check_dir in check_dirs:
        if not os.path.exists(check_dir):
            print(f"⚠️  目录不存在: {check_dir}")
            continue

        print(f"\n📁 检查目录: {check_dir}")

        for file_path in Path(check_dir).rglob("*.py"):
            if file_path.name in exclude_files:
                continue

            total_files += 1
            issues = check_file_for_old_imports(str(file_path))

            if issues:
                files_with_issues.append((str(file_path), issues))
                print(f"  ❌ {file_path.name}")
                for issue in issues:
                    print(f"      - {issue}")
            else:
                print(f"  ✅ {file_path.name}")

    # 验证策略注册
    print("\n" + "=" * 80)
    print("验证策略注册中心")
    print("=" * 80)

    try:
        from investlib_quant.strategies import StrategyRegistry

        strategies = StrategyRegistry.list_all()
        print(f"\n✅ 策略注册中心正常工作")
        print(f"✅ 已注册策略数量: {len(strategies)}")
        print("\n注册的策略:")
        for s in strategies:
            print(f"  • {s.display_name} ({s.name})")
            print(f"    风险: {s.risk_level} | 标签: {', '.join(s.tags[:2])}")

        if len(strategies) < 3:
            print(f"\n⚠️  警告: 只注册了 {len(strategies)} 个策略，预期至少3个")

    except Exception as e:
        print(f"\n❌ 策略注册中心验证失败: {e}")
        import traceback
        traceback.print_exc()

    # 总结
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)

    print(f"\n检查的文件数: {total_files}")
    print(f"有问题的文件: {len(files_with_issues)}")

    if files_with_issues:
        print("\n需要修复的文件:")
        for file_path, issues in files_with_issues:
            print(f"  ❌ {file_path}")
            print(f"     发现 {len(issues)} 个老式导入")
    else:
        print("\n🎉 所有文件都使用统一的策略注册中心！")

    # 验证推荐
    print("\n" + "=" * 80)
    print("推荐验证步骤")
    print("=" * 80)
    print("""
1. 启动 Streamlit 应用:
   cd investapp && streamlit run investapp/app.py

2. 检查回测页面:
   - 访问 "Backtest" 页面
   - 策略下拉菜单应该显示：
     • 120日均线突破策略
     • Kroll风险控制策略
     • 市场轮动策略（大盘恐慌买入）

3. 检查策略管理页面:
   - 访问 "Strategies" 页面
   - 应该显示所有3个策略的详细信息

4. 运行命令行测试:
   python scripts/show_strategies.py
    """)

    return len(files_with_issues) == 0


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
