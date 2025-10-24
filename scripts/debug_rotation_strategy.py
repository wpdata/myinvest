#!/usr/bin/env python
"""详细调试轮动策略。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_data.market_api import MarketDataFetcher
from investlib_data.cache_manager import CacheManager
from investlib_data.database import SessionLocal
from investlib_quant.strategies.market_rotation import MarketRotationStrategy
import pandas as pd

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def debug_strategy():
    """逐步调试策略逻辑。"""

    print("="*80)
    print("轮动策略详细调试")
    print("="*80 + "\n")

    # 1. 创建策略
    strategy = MarketRotationStrategy(
        index_symbol='000300.SH',
        decline_threshold=-1.5,
        consecutive_days=2,
        etf_symbol='159845.SZ',
        bond_symbol='511010.SH',
        holding_days=20
    )

    print("1. 策略配置:")
    print(f"   监控指数: {strategy.index_symbol}")
    print(f"   跌幅阈值: {strategy.decline_threshold}%")
    print(f"   连续天数: {strategy.consecutive_days}")
    print(f"   持有天数: {strategy.holding_days}\n")

    # 2. 获取数据
    session = SessionLocal()
    cache_manager = CacheManager(session=session)
    fetcher = MarketDataFetcher(cache_manager=cache_manager)

    print("2. 获取历史数据...")
    index_result = fetcher.fetch_with_fallback('000300.SH', '2024-01-01', '2024-12-31')
    index_data = index_result['data']

    etf_result = fetcher.fetch_with_fallback('159845.SZ', '2024-01-01', '2024-12-31')
    etf_data = etf_result['data']

    bond_result = fetcher.fetch_with_fallback('511010.SH', '2024-01-01', '2024-12-31')
    bond_data = bond_result['data']

    print(f"   ✓ 指数数据: {len(index_data)} 天")
    print(f"   ✓ ETF数据: {len(etf_data)} 天")
    print(f"   ✓ 国债数据: {len(bond_data)} 天\n")

    # 3. 计算涨跌幅
    index_data['pct_change'] = index_data['close'].pct_change() * 100

    # 4. 查找触发点
    print("3. 查找触发点 (2024年)...")
    triggers = []

    for i in range(strategy.consecutive_days, len(index_data)):
        recent_days = index_data.iloc[i-strategy.consecutive_days:i+1]
        last_n_changes = recent_days['pct_change'].iloc[-strategy.consecutive_days:]
        all_decline = all(last_n_changes <= strategy.decline_threshold)

        if all_decline:
            trigger_date = index_data.iloc[i]['timestamp']
            triggers.append({
                'date': trigger_date,
                'changes': last_n_changes.tolist(),
                'index': i
            })

    print(f"   找到 {len(triggers)} 个触发点\n")

    if triggers:
        print("触发点详情:")
        for j, t in enumerate(triggers, 1):
            date_str = t['date'] if isinstance(t['date'], str) else t['date'].strftime('%Y-%m-%d')
            print(f"   {j}. {date_str}")
            for k, chg in enumerate(t['changes'], 1):
                print(f"      第{k}日: {chg:.2f}%")

        # 5. 测试策略信号生成
        print("\n4. 测试策略信号生成...")

        # 选择第一个触发点进行测试
        test_trigger = triggers[0]
        test_idx = test_trigger['index']

        # 准备到触发点的历史数据
        historical_index = index_data.iloc[:test_idx+1].copy()
        historical_etf = etf_data[etf_data['timestamp'] <= test_trigger['date']].copy()
        historical_bond = bond_data[bond_data['timestamp'] <= test_trigger['date']].copy()

        # 移除 pct_change 列，让策略自己计算
        if 'pct_change' in historical_index.columns:
            historical_index = historical_index.drop(columns=['pct_change'])

        print(f"\n   测试触发点: {test_trigger['date']}")
        print(f"   历史数据长度: index={len(historical_index)}, etf={len(historical_etf)}, bond={len(historical_bond)}")
        print(f"   历史数据列: {historical_index.columns.tolist()}")

        # 手动检查策略内部逻辑
        print(f"\n   手动检查触发条件:")
        required_days = strategy.consecutive_days + 1
        print(f"   - 需要数据天数: {required_days}")
        print(f"   - 实际数据天数: {len(historical_index)}")

        recent = historical_index.tail(required_days).copy()
        recent['pct_change'] = recent['close'].pct_change() * 100
        last_n = recent['pct_change'].iloc[-strategy.consecutive_days:]

        print(f"   - 最后{strategy.consecutive_days}天涨跌幅: {last_n.tolist()}")
        print(f"   - 是否都≤{strategy.decline_threshold}%: {all(last_n <= strategy.decline_threshold)}")

        # 测试信号生成（初始持有国债）
        signal = strategy.generate_multi_asset_signal(
            index_data=historical_index,
            etf_data=historical_etf,
            bond_data=historical_bond,
            current_position='511010.SH',  # 当前持有国债
            position_entry_date=None
        )

        print(f"\n   策略返回的信号:")
        print(f"   - action: {signal.get('action')}")
        print(f"   - reason: {signal.get('reason')}")
        print(f"   - target_symbol: {signal.get('target_symbol')}")
        print(f"   - from_symbol: {signal.get('from_symbol')}")
        if 'reasoning' in signal:
            print(f"   - trigger: {signal['reasoning'].get('trigger')}")
            print(f"   - avg_decline: {signal['reasoning'].get('avg_decline')}%")

        # 6. 测试平仓逻辑
        print("\n5. 测试平仓逻辑...")

        # 假设在触发点买入了ETF
        entry_date = test_trigger['date']
        entry_idx = test_idx

        # 检查20个交易日后
        if entry_idx + 20 < len(index_data):
            exit_idx = entry_idx + 20
            exit_date = index_data.iloc[exit_idx]['timestamp']

            historical_index_exit = index_data.iloc[:exit_idx+1]
            historical_etf_exit = etf_data[etf_data['timestamp'] <= exit_date]
            historical_bond_exit = bond_data[bond_data['timestamp'] <= exit_date]

            exit_signal = strategy.generate_multi_asset_signal(
                index_data=historical_index_exit,
                etf_data=historical_etf_exit,
                bond_data=historical_bond_exit,
                current_position='159845.SZ',  # 当前持有ETF
                position_entry_date=entry_date
            )

            date_str = exit_date if isinstance(exit_date, str) else exit_date.strftime('%Y-%m-%d')
            print(f"\n   20个交易日后 ({date_str}):")
            print(f"   - action: {exit_signal.get('action')}")
            print(f"   - target_symbol: {exit_signal.get('target_symbol')}")
            if 'reasoning' in exit_signal:
                print(f"   - trigger: {exit_signal['reasoning'].get('trigger')}")
                print(f"   - holding_days: {exit_signal['reasoning'].get('holding_days')}")

    else:
        print("   ❌ 2024年未找到触发点")
        print("\n   分析：")
        print("   查找2024年跌幅最大的几天:")
        top_declines = index_data.nsmallest(10, 'pct_change')[['timestamp', 'pct_change']]
        for _, row in top_declines.iterrows():
            date_str = row['timestamp'] if isinstance(row['timestamp'], str) else row['timestamp'].strftime('%Y-%m-%d')
            print(f"   {date_str}: {row['pct_change']:.2f}%")

    session.close()

    print("\n" + "="*80)
    print("调试完成")
    print("="*80)

if __name__ == '__main__':
    debug_strategy()
