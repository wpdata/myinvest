"""
Indicator Selector Component (T066)

Reusable UI component for selecting technical indicators.
"""

import streamlit as st
from typing import List, Dict


def render_indicator_selector(
    key_prefix: str = "indicator",
    default_indicators: List[str] = None
) -> Dict[str, bool]:
    """Render indicator selection checkboxes.

    Args:
        key_prefix: Unique key prefix for session state
        default_indicators: List of indicators enabled by default

    Returns:
        Dict of {indicator_name: enabled_bool}

    Example:
        >>> selected = render_indicator_selector(key_prefix="strategy1")
        >>> if selected['MACD']:
        ...     # Use MACD indicator
    """
    if default_indicators is None:
        default_indicators = ['MACD', 'KDJ']

    st.subheader("📊 技术指标选择")

    # Create columns for checkboxes
    col1, col2 = st.columns(2)

    with col1:
        macd = st.checkbox(
            "MACD (平滑异同移动平均线)",
            value='MACD' in default_indicators,
            key=f"{key_prefix}_macd",
            help="趋势跟踪指标，通过快慢均线差值识别买卖点"
        )

        kdj = st.checkbox(
            "KDJ (随机指标)",
            value='KDJ' in default_indicators,
            key=f"{key_prefix}_kdj",
            help="超买超卖指标，K线上穿D线为买入信号"
        )

    with col2:
        bollinger = st.checkbox(
            "布林带 (Bollinger Bands)",
            value='布林带' in default_indicators,
            key=f"{key_prefix}_bb",
            help="波动率指标，价格触及下轨为超卖，触及上轨为超买"
        )

        volume = st.checkbox(
            "成交量分析 (Volume Analysis)",
            value='成交量' in default_indicators,
            key=f"{key_prefix}_vol",
            help="成交量确认指标，放量突破增强信号可信度"
        )

    # Summary
    selected_indicators = []
    if macd:
        selected_indicators.append('MACD')
    if kdj:
        selected_indicators.append('KDJ')
    if bollinger:
        selected_indicators.append('布林带')
    if volume:
        selected_indicators.append('成交量')

    if selected_indicators:
        st.info(f"✅ 已选择 {len(selected_indicators)} 个指标: {', '.join(selected_indicators)}")
    else:
        st.warning("⚠️ 请至少选择一个技术指标")

    return {
        'MACD': macd,
        'KDJ': kdj,
        '布林带': bollinger,
        '成交量': volume
    }


def render_indicator_config(indicator_name: str, key_prefix: str = "config"):
    """Render configuration for specific indicator.

    Args:
        indicator_name: Name of indicator
        key_prefix: Unique key prefix

    Returns:
        Dict of indicator parameters
    """
    st.subheader(f"⚙️ {indicator_name} 参数配置")

    if indicator_name == 'MACD':
        col1, col2, col3 = st.columns(3)
        with col1:
            fast = st.number_input("快线周期", value=12, min_value=5, max_value=50, key=f"{key_prefix}_macd_fast")
        with col2:
            slow = st.number_input("慢线周期", value=26, min_value=10, max_value=100, key=f"{key_prefix}_macd_slow")
        with col3:
            signal = st.number_input("信号线周期", value=9, min_value=3, max_value=30, key=f"{key_prefix}_macd_signal")

        return {'fast': fast, 'slow': slow, 'signal': signal}

    elif indicator_name == 'KDJ':
        col1, col2, col3 = st.columns(3)
        with col1:
            period = st.number_input("周期", value=9, min_value=5, max_value=30, key=f"{key_prefix}_kdj_period")
        with col2:
            oversold = st.number_input("超卖阈值", value=20, min_value=10, max_value=30, key=f"{key_prefix}_kdj_oversold")
        with col3:
            overbought = st.number_input("超买阈值", value=80, min_value=70, max_value=90, key=f"{key_prefix}_kdj_overbought")

        return {'period': period, 'oversold': oversold, 'overbought': overbought}

    elif indicator_name == '布林带':
        col1, col2 = st.columns(2)
        with col1:
            period = st.number_input("周期", value=20, min_value=10, max_value=50, key=f"{key_prefix}_bb_period")
        with col2:
            std_dev = st.number_input("标准差倍数", value=2.0, min_value=1.0, max_value=3.0, step=0.1, key=f"{key_prefix}_bb_std")

        return {'period': period, 'std_dev': std_dev}

    elif indicator_name == '成交量':
        period = st.number_input("均线周期", value=20, min_value=5, max_value=60, key=f"{key_prefix}_vol_period")
        threshold = st.number_input("放量阈值", value=1.5, min_value=1.0, max_value=3.0, step=0.1, key=f"{key_prefix}_vol_threshold")

        return {'period': period, 'threshold': threshold}

    return {}


# Example usage
if __name__ == '__main__':
    st.title("指标选择器组件测试")

    # Render selector
    selected = render_indicator_selector(
        key_prefix="test",
        default_indicators=['MACD', 'KDJ']
    )

    st.divider()

    # Show selected indicators
    for indicator, enabled in selected.items():
        if enabled:
            st.subheader(f"配置 {indicator}")
            config = render_indicator_config(indicator, key_prefix="test")
            st.json(config)

    # Display summary
    st.divider()
    st.subheader("选择结果")
    st.json(selected)
