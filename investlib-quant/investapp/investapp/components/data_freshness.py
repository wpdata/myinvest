"""Data Freshness Indicator Component (US5 - T017)

Displays data freshness level with color-coded badges and tooltips.
Provides clear visual indication of data currency.
"""

import streamlit as st
from typing import Optional


def render_freshness_indicator(data_freshness: str) -> None:
    """Render data freshness indicator with color-coded badge.

    Args:
        data_freshness: One of: "realtime", "delayed", "historical"

    Returns:
        None (renders Streamlit component)
    """
    # Define freshness levels
    freshness_config = {
        "realtime": {
            "label": "实时数据",
            "color": "#28a745",  # Green
            "icon": "✓",
            "tooltip": "数据为实时获取（延迟<5秒），可用于即时决策"
        },
        "delayed": {
            "label": "延迟数据 (<15分钟)",
            "color": "#ffc107",  # Yellow
            "icon": "⚠",
            "tooltip": "数据略有延迟（5秒-15分钟），建议谨慎使用"
        },
        "historical": {
            "label": "历史数据",
            "color": "#6c757d",  # Gray
            "icon": "📅",
            "tooltip": "数据为历史记录（>15分钟），不反映当前市场状态"
        }
    }

    # Get config for current freshness level
    config = freshness_config.get(
        data_freshness.lower(),
        freshness_config["historical"]  # Default to historical if unknown
    )

    # Render badge with tooltip
    badge_html = f"""
    <div style="
        display: inline-block;
        padding: 8px 16px;
        background-color: {config['color']};
        color: white;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        margin: 4px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        cursor: help;
    " title="{config['tooltip']}">
        <span style="margin-right: 6px; font-size: 16px;">{config['icon']}</span>
        <span>{config['label']}</span>
    </div>
    """

    st.markdown(badge_html, unsafe_allow_html=True)


def render_freshness_warning(data_freshness: str) -> None:
    """Render warning banner if data is not realtime.

    Args:
        data_freshness: Data freshness level

    Returns:
        None (renders Streamlit warning if needed)
    """
    if data_freshness.lower() == "historical":
        st.warning(
            "⚠️ **注意**: 当前使用历史数据（>15分钟）。"
            "数据可能不反映最新市场状况，建议点击"刷新数据"获取最新信息。",
            icon="⚠️"
        )
    elif data_freshness.lower() == "delayed":
        st.info(
            "ℹ️ **提示**: 当前数据略有延迟（5秒-15分钟）。"
            "如需最新数据，可点击"刷新数据"按钮。",
            icon="ℹ️"
        )


def render_freshness_badge_small(data_freshness: str) -> None:
    """Render small freshness badge for compact display (e.g., in tables).

    Args:
        data_freshness: Data freshness level

    Returns:
        None (renders Streamlit component)
    """
    # Define colors and icons
    if data_freshness.lower() == "realtime":
        color = "#28a745"
        icon = "✓"
        label = "实时"
    elif data_freshness.lower() == "delayed":
        color = "#ffc107"
        icon = "⚠"
        label = "延迟"
    else:  # historical
        color = "#6c757d"
        icon = "📅"
        label = "历史"

    # Render small badge
    badge_html = f"""
    <span style="
        display: inline-block;
        padding: 2px 6px;
        background-color: {color};
        color: white;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 600;
        margin: 0 2px;
    ">
        {icon} {label}
    </span>
    """

    st.markdown(badge_html, unsafe_allow_html=True)


def get_freshness_color(data_freshness: str) -> str:
    """Get color code for given freshness level.

    Useful for custom styling.

    Args:
        data_freshness: Data freshness level

    Returns:
        Hex color code
    """
    colors = {
        "realtime": "#28a745",
        "delayed": "#ffc107",
        "historical": "#6c757d"
    }
    return colors.get(data_freshness.lower(), colors["historical"])


def get_freshness_icon(data_freshness: str) -> str:
    """Get icon for given freshness level.

    Args:
        data_freshness: Data freshness level

    Returns:
        Unicode icon character
    """
    icons = {
        "realtime": "✓",
        "delayed": "⚠",
        "historical": "📅"
    }
    return icons.get(data_freshness.lower(), icons["historical"])


def render_freshness_timeline(
    data_freshness: str,
    data_timestamp: str
) -> None:
    """Render freshness with timeline context.

    Shows when data was retrieved and how fresh it is.

    Args:
        data_freshness: Data freshness level
        data_timestamp: ISO timestamp of retrieval

    Returns:
        None (renders Streamlit component)
    """
    from datetime import datetime

    # Parse timestamp
    try:
        ts = data_timestamp.replace('Z', '+00:00')
        dt = datetime.fromisoformat(ts)
        timestamp_display = dt.strftime('%H:%M:%S')

        # Calculate time ago
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            time_ago = f"{int(seconds)}秒前"
        elif seconds < 3600:
            time_ago = f"{int(seconds/60)}分钟前"
        else:
            time_ago = f"{int(seconds/3600)}小时前"
    except Exception:
        timestamp_display = "未知"
        time_ago = ""

    # Get freshness config
    color = get_freshness_color(data_freshness)
    icon = get_freshness_icon(data_freshness)

    # Render timeline
    timeline_html = f"""
    <div style="
        padding: 12px;
        border-left: 4px solid {color};
        background-color: rgba(0,0,0,0.02);
        border-radius: 4px;
        margin: 8px 0;
    ">
        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
            数据获取时间: {timestamp_display} {time_ago}
        </div>
        <div style="font-size: 14px; font-weight: 600; color: {color};">
            {icon} 数据新鲜度: {data_freshness.upper()}
        </div>
    </div>
    """

    st.markdown(timeline_html, unsafe_allow_html=True)
