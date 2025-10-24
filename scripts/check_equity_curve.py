#!/usr/bin/env python
"""检查净值曲线的异常值。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_backtest.engine.rotation_backtest import RotationBacktestRunner
from investlib_quant.strategies.market_rotation import MarketRotationStrategy

def check_equity():
    """运行回测并检查净值曲线。"""

    print("运行回测检查净值曲线...\n")

    strategy = MarketRotationStrategy(
        index_symbol='000300.SH',
        decline_threshold=-1.5,
        consecutive_days=2,
        etf_symbol='159845.SZ',
        bond_symbol='511010.SH',
        holding_days=20
    )

    asset_symbols = {
        'index': '000300.SH',
        'etf': '159845.SZ',
        'bond': '511010.SH'
    }

    runner = RotationBacktestRunner(
        initial_capital=100000.0,
        commission_rate=0.0003,
        slippage_rate=0.001
    )

    results = runner.run(
        strategy=strategy,
        asset_symbols=asset_symbols,
        start_date='2024-01-01',
        end_date='2024-12-31',
        capital=100000.0
    )

    print(f"回测完成!")
    print(f"最终资金: ¥{results['final_capital']:,.2f}")
    print(f"总收益率: {results['total_return']*100:.2f}%")
    print(f"切换次数: {results['total_switches']}\n")

    # 检查净值曲线
    equity_curve = results['equity_curve']

    print("检查净值曲线异常值...\n")

    # 找出净值为0或接近0的点
    zero_values = []
    min_value = float('inf')
    max_value = float('-inf')

    for i, point in enumerate(equity_curve):
        value = point['value']
        min_value = min(min_value, value)
        max_value = max(max_value, value)

        if value < 1000:  # 净值小于1000视为异常
            zero_values.append({
                'index': i,
                'date': point['date'],
                'value': value,
                'cash': point['cash'],
                'position': point['position'],
                'shares': point['shares']
            })

    print(f"净值统计:")
    print(f"  最小值: ¥{min_value:,.2f}")
    print(f"  最大值: ¥{max_value:,.2f}")
    print(f"  异常点数量 (净值<1000): {len(zero_values)}\n")

    if zero_values:
        print("异常点详情 (前10个):")
        for point in zero_values[:10]:
            print(f"  日期: {point['date']}")
            print(f"  净值: ¥{point['value']:,.2f}")
            print(f"  现金: ¥{point['cash']:,.2f}")
            print(f"  持仓: {point['position']}")
            print(f"  份额: {point['shares']:.2f}")
            print()

    # 检查切换记录
    print("切换记录:")
    for i, switch in enumerate(results['switch_log'], 1):
        print(f"{i}. [{switch['timestamp']}] "
              f"{switch['from_symbol']} → {switch['to_symbol']}")
        print(f"   价格: ¥{switch['price']:.3f}, "
              f"份额: {switch['shares']:.2f}, "
              f"价值: ¥{switch['value']:,.2f}")
        print()

if __name__ == '__main__':
    check_equity()
