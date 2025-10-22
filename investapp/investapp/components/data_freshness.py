"""Data freshness indicator component for displaying market data status."""

import streamlit as st
from datetime import datetime


def render_freshness_indicator(data_freshness: str, retrieval_timestamp: datetime, api_source: str = None) -> None:
    """Render data freshness indicator badge.

    Args:
        data_freshness: One of 'realtime', 'delayed', 'historical'
        retrieval_timestamp: When the data was retrieved
        api_source: Optional API source name
    """
    # Configure badge colors and labels
    freshness_config = {
        'realtime': {
            'emoji': '🟢',
            'label': '实时',
            'color': '#4caf50',
            'bg_color': '#e8f5e9'
        },
        'delayed': {
            'emoji': '🟡',
            'label': '延迟 15 分钟',
            'color': '#ff9800',
            'bg_color': '#fff3e0'
        },
        'historical': {
            'emoji': '⚪',
            'label': '历史数据',
            'color': '#9e9e9e',
            'bg_color': '#f5f5f5'
        }
    }

    config = freshness_config.get(data_freshness, freshness_config['historical'])

    # Format timestamp
    if isinstance(retrieval_timestamp, str):
        try:
            retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)
        except:
            pass

    time_str = retrieval_timestamp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(retrieval_timestamp, datetime) else str(retrieval_timestamp)

    # Render badge
    st.markdown(
        f"""
        <div style='
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            background-color: {config['bg_color']};
            border: 1px solid {config['color']};
            margin-bottom: 10px;
        '>
            <span style='color: {config['color']}; font-weight: bold;'>
                {config['emoji']} {config['label']}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display metadata below
    st.caption(f"数据时间: {time_str}")
    if api_source:
        st.caption(f"数据来源: {api_source}")
