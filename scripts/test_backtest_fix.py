#!/usr/bin/env python
"""测试回测引擎修复后的BUY/SELL配对。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_quant.strategies.livermore import LivermoreStrategy
from investlib_backtest.engine.backtest_runner import BacktestRunner
import logging
import os

# 禁用缓存，强制获取新数据
os.environ['DISABLE_CACHE'] = '1'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_backtest_pairing():
    """测试回测引擎的BUY/SELL配对。"""

    print("="*80)
    print("测试回测引擎修复后的BUY/SELL配对")
    print("="*80 + "\n")

    # 创建策略和回测引擎
    strategy = LivermoreStrategy()
    runner = BacktestRunner()

    # 运行回测
    print("运行回测: 600519.SH (贵州茅台)")
    print("时间范围: 2022-01-01 到 2025-10-24\n")

    result = runner.run(
        strategy=strategy,
        symbols=['600519'],
        start_date='2022-01-01',
        end_date='2025-10-24',
        capital=100000
    )

    # 分析交易记录
    trade_log = result['trade_log']

    buy_count = sum(1 for t in trade_log if t['action'] == 'BUY')
    sell_count = sum(1 for t in trade_log if t['action'] == 'SELL')

    print(f"交易统计:")
    print(f"  BUY 数量: {buy_count}")
    print(f"  SELL 数量: {sell_count}")
    print(f"  是否匹配: {'✓ 是' if buy_count == sell_count else '✗ 否'}\n")

    # 显示交易序列
    print("交易序列:")
    for i, trade in enumerate(trade_log, 1):
        action = trade['action']
        price = trade['price']
        date = trade['timestamp']
        quantity = trade['quantity']
        print(f"  {i:2d}. {action:4s} | {date} | ¥{price:,.2f} | {quantity} 股")

    print("\n" + "="*80)

    # 显示统计结果
    stats = result.get('trade_statistics', {})
    print("\n交易统计结果:")
    print(f"  总交易对数: {stats.get('total_trades', 0)}")
    print(f"  胜率: {stats.get('win_rate_pct', 0):.1f}%")
    print(f"  盈利因子: {stats.get('profit_factor', 0):.2f}")
    print(f"  平均盈利: ¥{stats.get('avg_win', 0):,.2f}")
    print(f"  平均亏损: ¥{stats.get('avg_loss', 0):,.2f}")

    print("\n" + "="*80)
    print("结论:")
    if buy_count == sell_count and stats.get('total_trades', 0) > 0:
        print("✓ 修复成功！BUY/SELL完全配对，统计数据正常显示。")
    else:
        print("✗ 仍有问题，需要进一步检查。")
    print("="*80)

if __name__ == '__main__':
    test_backtest_pairing()
