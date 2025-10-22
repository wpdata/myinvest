#!/usr/bin/env python3
"""查看所有可用的投资策略。

使用方法:
    python scripts/show_strategies.py              # 显示所有策略
    python scripts/show_strategies.py ma_breakout_120  # 显示特定策略
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../investlib-quant/src'))

from investlib_quant.strategies import StrategyRegistry


def main():
    if len(sys.argv) > 1:
        # 显示特定策略
        strategy_name = sys.argv[1]
        StrategyRegistry.print_summary(name=strategy_name)
    else:
        # 显示所有策略
        StrategyRegistry.print_summary()


if __name__ == '__main__':
    main()
