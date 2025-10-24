#!/usr/bin/env python
"""测试120均线策略的信号生成顺序。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_quant.strategies.livermore import LivermoreStrategy
from investlib_data.market_api import MarketDataFetcher
from datetime import datetime

def test_signal_sequence():
    """测试策略在整个回测期间的信号序列。"""

    print("="*80)
    print("测试120均线策略信号序列")
    print("="*80 + "\n")

    # 创建策略
    strategy = LivermoreStrategy()

    # 获取数据（假设测试贵州茅台）
    fetcher = MarketDataFetcher()
    result = fetcher.fetch_with_fallback('600519', '2022-01-01', '2025-10-24')
    market_data = result['data']

    print(f"数据范围: {market_data['timestamp'].min()} 到 {market_data['timestamp'].max()}")
    print(f"数据点数: {len(market_data)}\n")

    # 模拟回测，逐日生成信号
    buy_signals = []
    sell_signals = []

    for i in range(120, len(market_data)):  # 从有足够数据开始
        historical_data = market_data.iloc[:i+1]
        signal = strategy.generate_signal(historical_data)

        if signal.get('action') == 'BUY':
            buy_signals.append({
                'date': historical_data.iloc[-1]['timestamp'],
                'price': signal.get('entry_price'),
                'index': i
            })
        elif signal.get('action') == 'SELL':
            sell_signals.append({
                'date': historical_data.iloc[-1]['timestamp'],
                'price': signal.get('exit_price'),
                'index': i
            })

    print(f"BUY 信号数量: {len(buy_signals)}")
    print(f"SELL 信号数量: {len(sell_signals)}\n")

    print("BUY 信号:")
    for i, sig in enumerate(buy_signals, 1):
        print(f"  {i}. {sig['date']} @ ¥{sig['price']:.2f} (索引 {sig['index']})")

    print("\nSELL 信号:")
    for i, sig in enumerate(sell_signals, 1):
        print(f"  {i}. {sig['date']} @ ¥{sig['price']:.2f} (索引 {sig['index']})")

    print("\n信号顺序分析:")
    all_signals = []
    for sig in buy_signals:
        all_signals.append(('BUY', sig['index'], sig['date'], sig['price']))
    for sig in sell_signals:
        all_signals.append(('SELL', sig['index'], sig['date'], sig['price']))

    all_signals.sort(key=lambda x: x[1])  # 按索引排序

    for i, (action, idx, date, price) in enumerate(all_signals, 1):
        print(f"  {i}. {action:4s} | {date} | ¥{price:.2f} | 索引 {idx}")

    print("\n" + "="*80)
    print("结论:")
    print("如果SELL信号出现在第一个BUY之前，或者BUY后没有对应的SELL，")
    print("那么回测引擎会忽略这些信号，导致BUY/SELL数量不匹配。")
    print("="*80)

if __name__ == '__main__':
    test_signal_sequence()
