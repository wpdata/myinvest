"""Confirmation Dialog for trade execution."""

import streamlit as st
from typing import Dict, Any, Optional


@st.dialog("确认交易执行")
def show_confirmation_dialog(recommendation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Show confirmation dialog for trade execution.

    Returns:
        Dict with user action and modifications, or None if cancelled
    """
    symbol = recommendation.get('symbol', 'N/A')
    action = recommendation.get('action', 'UNKNOWN')

    st.warning("⚠️ 这是模拟交易，不会进行实际交易")

    st.subheader(f"确认执行：{symbol} - {action}")

    # Display all details
    col1, col2 = st.columns(2)

    with col1:
        st.metric("入场价", f"¥{recommendation['entry_price']:.2f}")
        st.metric("止损价", f"¥{recommendation['stop_loss']:.2f}")

    with col2:
        st.metric("止盈价", f"¥{recommendation['take_profit']:.2f}")
        st.metric("建议仓位", f"{recommendation['position_size_pct']:.1f}%")

    # Show max loss prominently
    st.markdown(
        f"<div style='background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 10px 0;'>"
        f"<h3 style='color: #d32f2f; margin: 0;'>最大可能损失: ¥{recommendation['max_loss']:.0f}</h3>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Allow modifications
    st.subheader("调整参数（可选）")

    modify_stop = st.checkbox("调整止损价")
    new_stop_loss = recommendation['stop_loss']
    if modify_stop:
        new_stop_loss = st.number_input(
            "新止损价",
            value=float(recommendation['stop_loss']),
            min_value=0.0,
            step=1.0
        )

    modify_position = st.checkbox("调整仓位")
    new_position_pct = recommendation['position_size_pct']
    if modify_position:
        new_position_pct = st.slider(
            "新仓位比例",
            min_value=0.0,
            max_value=20.0,
            value=float(recommendation['position_size_pct']),
            step=0.5
        )

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("取消", type="secondary", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("确认执行", type="primary", use_container_width=True):
            # Build modification record
            modifications = {}
            if modify_stop and new_stop_loss != recommendation['stop_loss']:
                modifications['stop_loss'] = {
                    'old': recommendation['stop_loss'],
                    'new': new_stop_loss
                }
            if modify_position and new_position_pct != recommendation['position_size_pct']:
                modifications['position_size_pct'] = {
                    'old': recommendation['position_size_pct'],
                    'new': new_position_pct
                }

            return {
                'action': 'CONFIRM',
                'modifications': modifications if modifications else None
            }

    return None
