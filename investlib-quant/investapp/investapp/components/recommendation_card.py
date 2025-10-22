"""Recommendation Card Component with Data Source Display (US5 - T018)

Displays investment recommendations with data provenance information.
Shows advisor, action, pricing, and data source metadata.
"""

import streamlit as st
from typing import Dict, Any
from .data_source_badge import render_data_source_badge, render_compact_data_source_badge
from .data_freshness import render_freshness_indicator


def render_recommendation_card(recommendation: Dict[str, Any]) -> None:
    """Render recommendation card with data source badge.

    Updated in V0.2 (T018) to display data provenance prominently.

    Args:
        recommendation: Dict containing recommendation fields:
            - advisor_name: str
            - action: str (BUY/SELL/HOLD)
            - entry_price: float
            - stop_loss: float
            - take_profit: float
            - position_size_pct: float
            - confidence: str
            - reasoning: str
            - data_source: str (NEW in V0.2)
            - data_timestamp: str (NEW in V0.2)
            - data_freshness: str (NEW in V0.2)

    Returns:
        None (renders Streamlit component)
    """
    # Extract fields
    advisor = recommendation.get('advisor_name', 'Unknown')
    action = recommendation.get('action', 'HOLD')
    entry = recommendation.get('entry_price', 0)
    stop = recommendation.get('stop_loss', 0)
    profit = recommendation.get('take_profit', 0)
    position = recommendation.get('position_size_pct', 0)
    confidence = recommendation.get('confidence', 'MEDIUM')
    reasoning = recommendation.get('reasoning', '')

    # Data provenance (NEW in V0.2)
    data_source = recommendation.get('data_source', 'Unknown')
    data_timestamp = recommendation.get('data_timestamp', '')
    data_freshness = recommendation.get('data_freshness', 'unknown')

    # Card header with action badge
    action_colors = {
        'BUY': '#28a745',
        'STRONG_BUY': '#218838',
        'SELL': '#dc3545',
        'STRONG_SELL': '#c82333',
        'HOLD': '#ffc107'
    }
    action_color = action_colors.get(action, '#6c757d')

    st.markdown(f"""
    <div style="
        border: 2px solid {action_color};
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        ">
            <h3 style="margin: 0; color: #333;">{advisor} 策略</h3>
            <span style="
                padding: 6px 14px;
                background-color: {action_color};
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
            ">{action}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Data Source Badge (PROMINENT at top - NEW in V0.2 T018)
    st.markdown("##### 📊 数据来源")
    render_data_source_badge(data_source, data_timestamp, data_freshness)

    st.markdown("---")

    # Recommendation details
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("入场价", f"¥{entry:.2f}")
        st.caption(f"止损: ¥{stop:.2f}")

    with col2:
        st.metric("目标价", f"¥{profit:.2f}")
        st.caption(f"仓位: {position:.1f}%")

    with col3:
        risk = abs(entry - stop)
        reward = abs(profit - entry)
        ratio = reward / risk if risk > 0 else 0
        st.metric("风险收益比", f"1:{ratio:.1f}")
        st.caption(f"置信度: {confidence}")

    # View Detailed Explanation (expandable)
    with st.expander("📝 查看详细说明"):
        st.write(reasoning)

        # Data metadata section (NEW in V0.2)
        st.markdown("##### 数据元信息")
        st.write(f"- **API来源**: {data_source}")
        st.write(f"- **获取时间**: {data_timestamp}")
        st.write(f"- **数据新鲜度**: {data_freshness}")

        if 'data_points' in recommendation:
            st.write(f"- **数据点数**: {recommendation['data_points']} 条")


def render_recommendation_summary(
    recommendations: list,
    show_data_source: bool = True
) -> None:
    """Render summary table of multiple recommendations.

    Args:
        recommendations: List of recommendation dicts
        show_data_source: Whether to show data source column (default True)

    Returns:
        None (renders Streamlit component)
    """
    import pandas as pd

    if not recommendations:
        st.info("暂无推荐")
        return

    # Build summary table
    summary_data = []
    for rec in recommendations:
        row = {
            '策略': rec.get('advisor_name', 'Unknown'),
            '操作': rec.get('action', 'HOLD'),
            '入场价': f"¥{rec.get('entry_price', 0):.2f}",
            '止损': f"¥{rec.get('stop_loss', 0):.2f}",
            '止盈': f"¥{rec.get('take_profit', 0):.2f}",
            '仓位': f"{rec.get('position_size_pct', 0):.1f}%",
            '置信度': rec.get('confidence', 'MEDIUM')
        }

        if show_data_source:
            row['数据来源'] = rec.get('data_source', 'Unknown')
            row['数据新鲜度'] = rec.get('data_freshness', 'unknown')

        summary_data.append(row)

    df = pd.DataFrame(summary_data)

    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
