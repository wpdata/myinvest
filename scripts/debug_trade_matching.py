#!/usr/bin/env python
"""调试交易配对问题。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_backtest.engine.backtest_runner import BacktestRunner
from investlib_backtest.metrics.trade_analysis import TradeAnalysis

def debug_trade_matching():
    """模拟一个简单的交易来测试配对逻辑。"""

    print("="*80)
    print("调试交易配对逻辑")
    print("="*80 + "\n")

    # 创建一个模拟的trade_log
    # 典型的回测应该有：2次BUY -> 2次SELL (完整的买卖对)
    mock_trade_log = [
        {
            'timestamp': '2022-01-05',
            'symbol': '000001.SZ',
            'action': 'BUY',
            'price': 10.0,
            'quantity': 100,
            'total_cost': 1000.0,
            'commission': 0.3,
            'slippage': 1.0
        },
        {
            'timestamp': '2022-01-10',
            'symbol': '000001.SZ',
            'action': 'SELL',
            'price': 11.0,
            'quantity': 100,
            'total_cost': -1100.0,  # 注意：SELL的total_cost应该是负数
            'commission': 0.33,
            'slippage': 1.1
        },
        {
            'timestamp': '2022-02-05',
            'symbol': '000001.SZ',
            'action': 'BUY',
            'price': 12.0,
            'quantity': 100,
            'total_cost': 1200.0,
            'commission': 0.36,
            'slippage': 1.2
        },
        {
            'timestamp': '2022-02-15',
            'symbol': '000001.SZ',
            'action': 'SELL',
            'price': 11.5,
            'quantity': 100,
            'total_cost': -1150.0,
            'commission': 0.345,
            'slippage': 1.15
        }
    ]

    print("1. 测试完整配对的交易（2买2卖）:")
    print(f"   交易记录数: {len(mock_trade_log)}\n")

    trade_analysis = TradeAnalysis()
    stats = trade_analysis.calculate_all_metrics(mock_trade_log)

    print("   统计结果:")
    print(f"   - 总交易对数: {stats.get('total_trades', 0)}")
    print(f"   - 胜率: {stats.get('win_rate_pct', 0):.1f}%")
    print(f"   - 盈利因子: {stats.get('profit_factor', 0):.2f}")
    print(f"   - 平均盈利: ¥{stats.get('avg_win', 0):,.2f}")
    print(f"   - 平均亏损: ¥{stats.get('avg_loss', 0):,.2f}")
    print()

    # 测试只有BUY的情况
    print("2. 测试只有BUY没有SELL的情况:")
    only_buy = [
        {
            'timestamp': '2022-01-05',
            'symbol': '000001.SZ',
            'action': 'BUY',
            'price': 10.0,
            'quantity': 100,
            'total_cost': 1000.0,
            'commission': 0.3,
            'slippage': 1.0
        },
        {
            'timestamp': '2022-02-05',
            'symbol': '000001.SZ',
            'action': 'BUY',
            'price': 12.0,
            'quantity': 100,
            'total_cost': 1200.0,
            'commission': 0.36,
            'slippage': 1.2
        }
    ]

    stats2 = trade_analysis.calculate_all_metrics(only_buy)
    print(f"   交易记录数: {len(only_buy)}")
    print(f"   统计结果: 总交易对数 = {stats2.get('total_trades', 0)}")
    print(f"   （预期：0，因为没有配对）\n")

    # 测试total_cost符号问题
    print("3. 测试total_cost符号错误的情况:")
    wrong_sign = [
        {
            'timestamp': '2022-01-05',
            'symbol': '000001.SZ',
            'action': 'BUY',
            'price': 10.0,
            'quantity': 100,
            'total_cost': 1000.0,
            'commission': 0.3,
            'slippage': 1.0
        },
        {
            'timestamp': '2022-01-10',
            'symbol': '000001.SZ',
            'action': 'SELL',
            'price': 11.0,
            'quantity': 100,
            'total_cost': 1100.0,  # 错误：应该是负数！
            'commission': 0.33,
            'slippage': 1.1
        }
    ]

    stats3 = trade_analysis.calculate_all_metrics(wrong_sign)
    print(f"   如果SELL的total_cost是正数（错误）:")
    print(f"   统计结果: 总交易对数 = {stats3.get('total_trades', 0)}")
    print(f"   盈利因子 = {stats3.get('profit_factor', 0):.2f}")
    print()

    print("="*80)
    print("结论：")
    print("- 如果你的回测显示有4次或8次交易，但统计全是0")
    print("- 最可能的原因是：")
    print("  1. 只有BUY操作，没有SELL操作（未平仓）")
    print("  2. Portfolio在SELL时total_cost的符号错误")
    print("  3. action字段值不是标准的'BUY'/'SELL'")
    print("="*80)

if __name__ == '__main__':
    debug_trade_matching()
