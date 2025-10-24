#!/usr/bin/env python
"""对比历史分析和策略模拟的触发点差异。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_data.market_api import MarketDataFetcher
from investlib_data.cache_manager import CacheManager
from investlib_data.database import SessionLocal
from investlib_quant.strategies.market_rotation import MarketRotationStrategy
import pandas as pd

def find_triggers_historical_way(index_data, consecutive_days, decline_threshold, holding_days):
    """使用历史分析的方式查找触发点。"""
    trigger_dates = []

    for i in range(consecutive_days, len(index_data)):
        # 检查最近连续N天是否都满足跌幅条件
        recent_days = index_data.iloc[i-consecutive_days:i+1]
        last_n_changes = recent_days['pct_change'].iloc[-consecutive_days:]
        all_decline = all(last_n_changes <= decline_threshold)

        if all_decline:
            trigger_date = index_data.iloc[i]['timestamp']

            if isinstance(trigger_date, str):
                trigger_date = pd.to_datetime(trigger_date)

            # 避免重复触发（间隔至少holding_days天）
            if not trigger_dates:
                trigger_dates.append({
                    'date': trigger_date,
                    'index': i,
                    'changes': last_n_changes.tolist()
                })
            else:
                last_trigger_date = trigger_dates[-1]['date']
                if isinstance(last_trigger_date, str):
                    last_trigger_date = pd.to_datetime(last_trigger_date)

                # 注意：这里用的是自然日！
                if (trigger_date - last_trigger_date).days >= holding_days:
                    trigger_dates.append({
                        'date': trigger_date,
                        'index': i,
                        'changes': last_n_changes.tolist()
                    })

    return trigger_dates


def find_triggers_backtest_way(index_data, etf_data, bond_data, strategy):
    """使用策略模拟的方式查找触发点（模拟回测引擎）。"""
    trigger_dates = []

    current_position = '511010.SH'  # 初始持有国债
    position_entry_date = None

    for i in range(len(index_data)):
        current_date = index_data.iloc[i]['timestamp']

        # 准备历史数据（截止到当前日期）
        historical_index = index_data.iloc[:i+1].copy()
        historical_etf = etf_data[etf_data['timestamp'] <= current_date].copy()
        historical_bond = bond_data[bond_data['timestamp'] <= current_date].copy()

        # 移除pct_change列让策略自己计算
        if 'pct_change' in historical_index.columns:
            historical_index = historical_index.drop(columns=['pct_change'])

        # 生成信号
        signal = strategy.generate_multi_asset_signal(
            index_data=historical_index,
            etf_data=historical_etf,
            bond_data=historical_bond,
            current_position=current_position,
            position_entry_date=position_entry_date
        )

        # 检查是否触发切换
        if signal.get('action') == 'SWITCH':
            trigger_dates.append({
                'date': current_date,
                'index': i,
                'from': signal.get('from_symbol'),
                'to': signal.get('target_symbol'),
                'reasoning': signal.get('reasoning', {})
            })

            # 更新状态
            current_position = signal.get('target_symbol')
            position_entry_date = current_date

    return trigger_dates


def compare_triggers():
    """对比两种方式的触发点。"""
    print("="*80)
    print("触发点对比分析")
    print("="*80 + "\n")

    # 参数
    consecutive_days = 2
    decline_threshold = -1.5
    holding_days = 20

    # 获取数据
    session = SessionLocal()
    cache_manager = CacheManager(session=session)
    fetcher = MarketDataFetcher(cache_manager=cache_manager)

    print("1. 加载数据...")
    index_result = fetcher.fetch_with_fallback('000300.SH', '2023-10-25', '2025-10-24')
    index_data = index_result['data']
    index_data['pct_change'] = index_data['close'].pct_change() * 100

    etf_result = fetcher.fetch_with_fallback('159845.SZ', '2023-10-25', '2025-10-24')
    etf_data = etf_result['data']

    bond_result = fetcher.fetch_with_fallback('511010.SH', '2023-10-25', '2025-10-24')
    bond_data = bond_result['data']

    print(f"   ✓ 数据天数: {len(index_data)}\n")

    # 方法1：历史分析方式
    print("2. 历史分析方式查找触发点...")
    historical_triggers = find_triggers_historical_way(
        index_data, consecutive_days, decline_threshold, holding_days
    )
    print(f"   找到 {len(historical_triggers)} 个触发点")
    for i, t in enumerate(historical_triggers, 1):
        date_str = t['date'] if isinstance(t['date'], str) else t['date'].strftime('%Y-%m-%d')
        print(f"   {i}. {date_str} (索引{t['index']})")
    print()

    # 方法2：策略模拟方式
    print("3. 策略模拟方式查找触发点...")
    strategy = MarketRotationStrategy(
        index_symbol='000300.SH',
        decline_threshold=decline_threshold,
        consecutive_days=consecutive_days,
        etf_symbol='159845.SZ',
        bond_symbol='511010.SH',
        holding_days=holding_days
    )

    backtest_triggers = find_triggers_backtest_way(
        index_data, etf_data, bond_data, strategy
    )
    print(f"   找到 {len(backtest_triggers)} 个切换")
    for i, t in enumerate(backtest_triggers, 1):
        date_str = t['date'] if isinstance(t['date'], str) else t['date'].strftime('%Y-%m-%d')
        print(f"   {i}. {date_str} (索引{t['index']}): {t['from']} → {t['to']}")
        if 'trigger' in t['reasoning']:
            print(f"      原因: {t['reasoning']['trigger']}")
    print()

    # 对比
    print("4. 差异分析:")
    print(f"   历史分析: {len(historical_triggers)} 个触发点")
    print(f"   策略模拟: {len(backtest_triggers)} 个切换")
    print(f"   差异: {len(historical_triggers) - len(backtest_triggers)} 个\n")

    # 详细对比
    if len(historical_triggers) != len(backtest_triggers):
        print("   详细对比:")
        historical_dates = set(
            t['date'] if isinstance(t['date'], str) else t['date'].strftime('%Y-%m-%d')
            for t in historical_triggers
        )
        backtest_dates = set(
            t['date'] if isinstance(t['date'], str) else t['date'].strftime('%Y-%m-%d')
            for t in backtest_triggers
        )

        only_in_historical = historical_dates - backtest_dates
        only_in_backtest = backtest_dates - historical_dates

        if only_in_historical:
            print(f"\n   仅在历史分析中出现的日期 ({len(only_in_historical)}个):")
            for date in sorted(only_in_historical):
                print(f"   - {date}")

        if only_in_backtest:
            print(f"\n   仅在策略模拟中出现的日期 ({len(only_in_backtest)}个):")
            for date in sorted(only_in_backtest):
                print(f"   - {date}")

    session.close()
    print("\n" + "="*80)

if __name__ == '__main__':
    compare_triggers()
