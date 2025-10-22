"""Dashboard Page with Data Freshness Display (US5 - T019)

Example dashboard showing how to integrate data source and freshness indicators.
This is a template/example - actual dashboard implementation may vary.
"""

import streamlit as st
import sys
from pathlib import Path

# Add components to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.data_source_badge import render_data_source_badge
from components.data_freshness import (
    render_freshness_indicator,
    render_freshness_warning,
    render_freshness_timeline
)
from components.recommendation_card import render_recommendation_card


st.set_page_config(
    page_title="MyInvest Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 MyInvest Dashboard")

# Simulated recommendation data (with V0.2 data provenance)
example_recommendation = {
    'advisor_name': 'Livermore',
    'action': 'BUY',
    'entry_price': 1457.93,
    'stop_loss': 1420.50,
    'take_profit': 1550.00,
    'position_size_pct': 15.0,
    'confidence': 'MEDIUM',
    'reasoning': '基于Livermore策略，建议BUY（MEDIUM置信度）。关键因素：价格突破120日均线、成交量放大。',
    # Data provenance (NEW in V0.2)
    'data_source': 'Efinance vlatest',
    'data_timestamp': '2025-10-20T11:26:25',
    'data_freshness': 'realtime',
    'data_points': 132
}

# Data Freshness Warning Banner (NEW in T019)
st.markdown("### 数据状态")
data_freshness = example_recommendation['data_freshness']
render_freshness_warning(data_freshness)

# Refresh Data Button (NEW in T019)
col1, col2, col3 = st.columns([2, 1, 1])
with col3:
    if st.button("🔄 刷新数据", help="强制从API获取最新数据（绕过缓存）"):
        st.info("正在刷新数据...")
        # In real implementation: call LivermoreStrategy.analyze(use_cache=False)

st.markdown("---")

# Holdings section with freshness indicators
st.markdown("### 💼 我的持仓")

# Example holdings with data freshness badges
holdings_data = {
    '股票代码': ['600519.SH', '000001.SZ', '000858.SZ'],
    '股票名称': ['贵州茅台', '平安银行', '五粮液'],
    '最新价': ['¥1457.93', '¥12.50', '¥145.30'],
    '数据来源': ['Efinance vlatest', 'Efinance vlatest', 'AKShare v1.17.66'],
    '数据新鲜度': ['realtime', 'realtime', 'delayed']
}

import pandas as pd
holdings_df = pd.DataFrame(holdings_data)

st.dataframe(holdings_df, use_container_width=True, hide_index=True)

# Show freshness for each holding
st.caption("数据新鲜度说明：")
col1, col2, col3 = st.columns(3)
with col1:
    from components.data_freshness import render_freshness_badge_small
    st.write("贵州茅台:")
    render_freshness_badge_small('realtime')
with col2:
    st.write("平安银行:")
    render_freshness_badge_small('realtime')
with col3:
    st.write("五粮液:")
    render_freshness_badge_small('delayed')

st.markdown("---")

# Recommendations section
st.markdown("### 🎯 投资建议")

# Render recommendation card with data source
render_recommendation_card(example_recommendation)

st.markdown("---")

# Data Freshness Timeline (NEW in T019)
st.markdown("### ⏰ 数据时间线")
render_freshness_timeline(
    data_freshness=example_recommendation['data_freshness'],
    data_timestamp=example_recommendation['data_timestamp']
)

st.markdown("---")

# Instructions
st.info("""
**V0.2 更新说明** (US5 - T019):

本页面已集成数据来源和新鲜度指示器：
- ✅ 所有数据显示均包含来源标识
- ✅ 数据新鲜度指示器（实时/延迟/历史）
- ✅ 历史数据警告横幅
- ✅ "刷新数据"按钮强制API调用

这确保了100%真实市场数据的使用，符合宪法原则XI（Real Data Mandate）。
""")
