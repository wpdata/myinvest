#!/usr/bin/env python
"""测试轮动策略的触发条件。"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_data.market_api import MarketDataFetcher
from investlib_data.cache_manager import CacheManager
from investlib_data.database import SessionLocal
import pandas as pd

def test_triggers():
    """检查历史上是否有触发点。"""

    print("🔍 检查2023-2024年沪深300是否有连续2日跌幅≤-1.5%的情况...\n")

    session = SessionLocal()
    cache_manager = CacheManager(session=session)
    fetcher = MarketDataFetcher(cache_manager=cache_manager)

    # 获取沪深300数据
    result = fetcher.fetch_with_fallback(
        '000300.SH',
        '2023-01-01',
        '2024-12-31'
    )

    df = result['data']
    df['pct_change'] = df['close'].pct_change() * 100

    print(f"✓ 加载了 {len(df)} 天数据\n")

    # 统计信息
    decline_days = df[df['pct_change'] <= -1.5]
    print(f"📊 统计信息:")
    print(f"  - 跌幅≤-1.5%的天数: {len(decline_days)} 天")
    print(f"  - 最大单日跌幅: {df['pct_change'].min():.2f}%")
    print(f"  - 平均涨跌幅: {df['pct_change'].mean():.2f}%\n")

    # 查找连续2日跌幅≤-1.5%的情况
    triggers = []
    for i in range(2, len(df)):
        last_2_days = df.iloc[i-1:i+1]['pct_change']

        if all(last_2_days <= -1.5):
            trigger_date = df.iloc[i]['timestamp']
            triggers.append({
                'date': trigger_date,
                'day1_change': last_2_days.iloc[0],
                'day2_change': last_2_days.iloc[1]
            })

    print(f"🎯 触发点分析 (连续2日跌幅≤-1.5%):")
    print(f"  - 触发次数: {len(triggers)} 次\n")

    if triggers:
        print("触发详情:")
        for i, t in enumerate(triggers, 1):
            date_str = t['date'] if isinstance(t['date'], str) else t['date'].strftime('%Y-%m-%d')
            print(f"  {i}. {date_str}: "
                  f"第1日 {t['day1_change']:.2f}%, "
                  f"第2日 {t['day2_change']:.2f}%")
    else:
        print("❌ 2023-2024年期间，沪深300没有出现连续2日跌幅≤-1.5%的情况！")
        print("\n建议:")
        print("  1. 放宽跌幅阈值到 -1.0% 或 -0.8%")
        print("  2. 减少连续天数到 1 天")
        print("  3. 或者选择更早的时间段（如2020-2022）进行回测\n")

        # 显示最接近的情况
        print("最接近触发的日期（单日跌幅≤-1.5%）:")
        top_declines = df.nlargest(10, 'pct_change', keep='first').sort_values('timestamp')
        for _, row in df[df['pct_change'] <= -1.5].head(10).iterrows():
            print(f"  - {row['timestamp'].strftime('%Y-%m-%d')}: {row['pct_change']:.2f}%")

    session.close()

if __name__ == '__main__':
    test_triggers()
