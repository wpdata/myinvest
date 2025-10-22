"""Data Source Badge Component (US5 - T016)

Displays data source and freshness information as a styled badge.
Shows API source, retrieval timestamp, and freshness indicator with color coding.
"""

import streamlit as st
from datetime import datetime
from typing import Optional


def render_data_source_badge(
    data_source: str,
    data_timestamp: str,
    data_freshness: str
) -> None:
    """Render data source badge with freshness indicator.

    Args:
        data_source: API source (e.g., "Efinance v latest" or "AKShare v1.17.66")
        data_timestamp: ISO timestamp of data retrieval
        data_freshness: One of: "realtime", "delayed", "historical"

    Returns:
        None (renders Streamlit component)
    """
    # Parse timestamp for display
    try:
        if isinstance(data_timestamp, str):
            # Handle both ISO format with/without timezone
            ts = data_timestamp.replace('Z', '+00:00')
            dt = datetime.fromisoformat(ts)
            timestamp_display = dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_display = str(data_timestamp)
    except Exception:
        timestamp_display = str(data_timestamp)

    # Choose color and icon based on freshness
    if data_freshness == "realtime":
        color = "#28a745"  # Green
        icon = "✓"
        freshness_label = "实时"
    elif data_freshness == "delayed":
        color = "#ffc107"  # Yellow
        icon = "⚠"
        freshness_label = "延迟"
    else:  # historical
        color = "#6c757d"  # Gray
        icon = "📅"
        freshness_label = "历史"

    # Render badge using HTML/CSS
    badge_html = f"""
    <div style="
        display: inline-block;
        padding: 6px 12px;
        background-color: {color};
        color: white;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 500;
        margin: 4px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <span style="margin-right: 6px;">{icon}</span>
        <span style="font-weight: 600;">{data_source}</span>
        <span style="margin: 0 8px;">|</span>
        <span>获取时间: {timestamp_display}</span>
        <span style="margin: 0 8px;">|</span>
        <span>数据: {freshness_label}</span>
    </div>
    """

    st.markdown(badge_html, unsafe_allow_html=True)


def render_compact_data_source_badge(
    data_source: str,
    data_freshness: str
) -> None:
    """Render compact version of data source badge (source + freshness only).

    Useful for displaying in tables or compact spaces.

    Args:
        data_source: API source
        data_freshness: One of: "realtime", "delayed", "historical"

    Returns:
        None (renders Streamlit component)
    """
    # Choose color based on freshness
    if data_freshness == "realtime":
        color = "#28a745"  # Green
        icon = "✓"
    elif data_freshness == "delayed":
        color = "#ffc107"  # Yellow
        icon = "⚠"
    else:  # historical
        color = "#6c757d"  # Gray
        icon = "📅"

    # Render compact badge
    badge_html = f"""
    <div style="
        display: inline-block;
        padding: 3px 8px;
        background-color: {color};
        color: white;
        border-radius: 3px;
        font-size: 12px;
        font-weight: 500;
        margin: 2px 0;
    ">
        <span style="margin-right: 4px;">{icon}</span>
        <span>{data_source}</span>
    </div>
    """

    st.markdown(badge_html, unsafe_allow_html=True)


def render_data_source_tooltip(
    data_source: str,
    data_timestamp: str,
    data_freshness: str,
    data_points: Optional[int] = None
) -> str:
    """Generate tooltip text with complete data metadata.

    Args:
        data_source: API source
        data_timestamp: ISO timestamp
        data_freshness: freshness level
        data_points: Number of data points (optional)

    Returns:
        Formatted tooltip text
    """
    lines = [
        f"数据来源: {data_source}",
        f"获取时间: {data_timestamp}",
        f"数据新鲜度: {data_freshness}",
    ]

    if data_points:
        lines.append(f"数据点数: {data_points} 条")

    # Add explanation based on freshness
    if data_freshness == "realtime":
        lines.append("✓ 实时数据（<5秒）")
    elif data_freshness == "delayed":
        lines.append("⚠ 延迟数据（5秒-15分钟）")
    else:
        lines.append("📅 历史数据（>15分钟）")

    return "\n".join(lines)
