#!/usr/bin/env python
"""测试回测交易统计。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_backtest.engine.backtest_runner import BacktestRunner
from investlib_backtest.metrics.trade_analysis import TradeAnalysis
from investlib_quant.strategies import StrategyRegistry

def test_trade_stats():
    """运行回测并检查trade_log。"""

    print("测试回测交易统计...\n")

    # 创建一个简单的策略用于测试
    from investlib_quant.strategies.ma_crossover import MACrossoverStrategy

    strategy = MACrossoverStrategy(
        short_window=5,
        long_window=20
    )
    print(f"使用策略: MA Crossover (5/20)\n")

    # 运行回测
    runner = BacktestRunner(initial_capital=100000)

    results = runner.run_backtest(
        strategy=strategy,
        symbol='000001.SZ',  # 平安银行
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    print(f"回测完成!")
    print(f"最终资金: ¥{results['final_capital']:,.2f}")
    print(f"总交易数: {results.get('total_trades', 0)}\n")

    # 检查trade_log
    trade_log = results.get('trade_log', [])
    print(f"Trade Log 记录数: {len(trade_log)}\n")

    if trade_log:
        print("前5条交易记录:")
        for i, trade in enumerate(trade_log[:5], 1):
            print(f"{i}. {trade.get('timestamp')} - "
                  f"{trade.get('action')} {trade.get('quantity')} "
                  f"{trade.get('symbol')} @ ¥{trade.get('price'):.2f}")
        print()

        # 统计BUY和SELL
        buy_count = sum(1 for t in trade_log if t.get('action') == 'BUY')
        sell_count = sum(1 for t in trade_log if t.get('action') == 'SELL')
        print(f"BUY数量: {buy_count}")
        print(f"SELL数量: {sell_count}\n")

    else:
        print("⚠️ Trade Log 为空！\n")
        print("可能的原因:")
        print("1. 策略没有生成任何交易信号")
        print("2. 信号生成了但没有执行交易")
        print("3. Portfolio没有正确记录交易\n")

    # 测试TradeAnalysis
    print("测试TradeAnalysis...")
    trade_analysis = TradeAnalysis()
    trade_stats = trade_analysis.calculate_all_metrics(trade_log)

    print(f"交易统计:")
    print(f"  胜率: {trade_stats.get('win_rate_pct', 0):.1f}%")
    print(f"  盈利因子: {trade_stats.get('profit_factor', 0):.2f}")
    print(f"  平均盈利: ¥{trade_stats.get('avg_win', 0):,.2f}")
    print(f"  平均亏损: ¥{trade_stats.get('avg_loss', 0):,.2f}")
    print(f"  总交易: {trade_stats.get('total_trades', 0)}")

if __name__ == '__main__':
    test_trade_stats()
