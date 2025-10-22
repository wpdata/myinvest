#!/usr/bin/env python3
"""市场轮动策略示例。

演示如何使用市场轮动策略和多品种回测引擎。

策略逻辑：
1. 监控沪深300指数
2. 当连续2天跌幅≤-1.5%时，买入中证1000 ETF
3. 持有20个交易日后，切换回国债ETF
4. 其余时间持有国债ETF
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../investlib-quant/src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../investlib-backtest'))

from investlib_quant.strategies.market_rotation import MarketRotationStrategy
from investlib_backtest.engine.rotation_backtest import RotationBacktestRunner
import logging


def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*80)
    print("市场轮动策略示例 - 大盘恐慌买入")
    print("="*80 + "\n")

    # 1. 创建策略实例
    print("1. 创建策略实例...")
    strategy = MarketRotationStrategy(
        index_symbol='000300.SH',      # 监控沪深300
        decline_threshold=-1.5,         # 跌幅阈值
        consecutive_days=2,             # 连续2天
        etf_symbol='159845.SZ',         # 中证1000 ETF
        bond_symbol='511010.SH',        # 国债ETF
        holding_days=20,                # 持有20个交易日
        position_size_pct=100.0,        # 全仓
        stop_loss_pct=5.0               # 可选5%止损
    )
    print(f"   ✓ 策略: {strategy.name}")
    print(f"   ✓ 监控指数: {strategy.index_symbol}")
    print(f"   ✓ 进攻品种: {strategy.etf_symbol}")
    print(f"   ✓ 防御品种: {strategy.bond_symbol}\n")

    # 2. 配置资产符号
    print("2. 配置资产符号...")
    asset_symbols = {
        'index': '000300.SH',      # 沪深300（监控用）
        'etf': '159845.SZ',        # 中证1000 ETF
        'bond': '511010.SH'        # 国债ETF
    }
    for asset_type, symbol in asset_symbols.items():
        print(f"   • {asset_type}: {symbol}")
    print()

    # 3. 运行回测
    print("3. 运行回测...")
    print("   回测期间: 2023-01-01 至 2024-12-31")
    print("   初始资金: ¥100,000\n")

    runner = RotationBacktestRunner(
        initial_capital=100000.0,
        commission_rate=0.0003,
        slippage_rate=0.001
    )

    try:
        results = runner.run(
            strategy=strategy,
            asset_symbols=asset_symbols,
            start_date='2023-01-01',
            end_date='2024-12-31',
            capital=100000.0
        )

        # 4. 显示回测结果
        print("\n" + "="*80)
        print("回测结果")
        print("="*80 + "\n")

        print(f"策略名称: {results['strategy_name']}")
        print(f"回测时间: {results['start_date']} 至 {results['end_date']}")
        print(f"\n资金情况:")
        print(f"  初始资金: ¥{results['initial_capital']:,.2f}")
        print(f"  最终资金: ¥{results['final_capital']:,.2f}")
        print(f"  总收益率: {results['total_return']*100:.2f}%")

        print(f"\n交易统计:")
        print(f"  总信号数: {results['signals_generated']}")
        print(f"  切换次数: {results['total_switches']}")

        # 显示切换记录
        if results['switch_log']:
            print(f"\n品种切换记录 (前10条):")
            for i, switch in enumerate(results['switch_log'][:10], 1):
                print(
                    f"  {i}. [{switch['timestamp']}] "
                    f"{switch['from_symbol'] or 'None'} → {switch['to_symbol']} "
                    f"@ ¥{switch['price']:.2f}"
                )
                reasoning = switch.get('reasoning', {})
                if 'trigger' in reasoning:
                    print(f"     原因: {reasoning['trigger']}")

        # 显示净值曲线（最后10个交易日）
        if results['equity_curve']:
            print(f"\n净值曲线 (最后10个交易日):")
            for record in results['equity_curve'][-10:]:
                print(
                    f"  [{record['date']}] "
                    f"价值: ¥{record['value']:,.2f} | "
                    f"持仓: {record.get('position', 'None')}"
                )

        print("\n" + "="*80)
        print("回测完成")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
