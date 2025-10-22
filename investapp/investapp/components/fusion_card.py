"""Fusion Strategy Recommendation Card (T052).

Displays three recommendation cards side-by-side:
- Kroll (risk-focused)
- Livermore (trend-following)
- Fused (weighted combination)

Shows conflict warnings when advisors disagree.
"""

import streamlit as st
from typing import Dict, Any, Optional


def render_fusion_card(
    fused_recommendation: Dict[str, Any],
    kroll_recommendation: Optional[Dict[str, Any]] = None,
    livermore_recommendation: Optional[Dict[str, Any]] = None
) -> None:
    """渲染融合策略卡片及各个策略的独立卡片.

    Args:
        fused_recommendation: 融合策略推荐
        kroll_recommendation: Kroll 独立推荐（可选）
        livermore_recommendation: Livermore 独立推荐（可选）
    """
    # Extract fusion factors for conflict detection
    fusion_factors = fused_recommendation.get('fusion_factors', [])
    has_conflict = any('CONFLICT' in factor for factor in fusion_factors)

    # Display conflict warning if detected
    if has_conflict:
        render_conflict_warning(fused_recommendation)

    # Display three cards side-by-side
    col_kroll, col_fused, col_livermore = st.columns([1, 1.2, 1])

    with col_kroll:
        st.markdown("### 🛡️ Kroll (风险聚焦)")
        if kroll_recommendation:
            _render_individual_card(kroll_recommendation, strategy_name="Kroll", color="blue")
        else:
            st.info("Kroll 策略未运行")

    with col_fused:
        st.markdown("### ⚖️ **融合推荐**")
        _render_fused_card_content(fused_recommendation)

    with col_livermore:
        st.markdown("### 📈 Livermore (趋势跟随)")
        if livermore_recommendation:
            _render_individual_card(livermore_recommendation, strategy_name="Livermore", color="green")
        else:
            st.info("Livermore 策略未运行")


def _render_fused_card_content(recommendation: Dict[str, Any]) -> None:
    """Render the content of the fused recommendation card."""
    action = recommendation.get('action', 'HOLD')
    confidence = recommendation.get('confidence', 'LOW')
    entry_price = recommendation.get('entry_price', 0)
    stop_loss = recommendation.get('stop_loss', 0)
    take_profit = recommendation.get('take_profit', 0)
    position_size = recommendation.get('position_size_pct', 0)
    risk_level = recommendation.get('risk_level', 'MEDIUM')

    # Extract individual signals if available
    kroll_signal = recommendation.get('kroll_signal', {})
    livermore_signal = recommendation.get('livermore_signal', {})

    # Action badge
    action_color = {
        'STRONG_BUY': '🟢',
        'BUY': '🔵',
        'HOLD': '⚪',
        'SELL': '🟠',
        'STRONG_SELL': '🔴'
    }.get(action, '⚪')

    st.markdown(f"## {action_color} {action}")

    # Confidence and risk
    conf_badge_color = "green" if confidence == "HIGH" else "orange" if confidence == "MEDIUM" else "red"
    st.markdown(f"**置信度:** :{conf_badge_color}[{confidence}]")

    risk_badge_color = "green" if risk_level == "LOW" else "orange" if risk_level == "MEDIUM" else "red"
    st.markdown(f"**风险等级:** :{risk_badge_color}[{risk_level}]")

    # Key metrics
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("入场价", f"¥{entry_price:.2f}")
        if entry_price > 0:
            st.metric("止盈价", f"¥{take_profit:.2f}", delta=f"+{((take_profit/entry_price - 1)*100):.1f}%")
        else:
            st.metric("止盈价", f"¥{take_profit:.2f}")

    with col2:
        if entry_price > 0:
            st.metric("止损价", f"¥{stop_loss:.2f}", delta=f"{((stop_loss/entry_price - 1)*100):.1f}%", delta_color="inverse")
        else:
            st.metric("止损价", f"¥{stop_loss:.2f}")
        st.metric("仓位大小", f"{position_size:.1f}%")

    # Advisor weights
    if kroll_signal and livermore_signal:
        st.divider()
        st.markdown("**策略权重:**")

        kroll_weight = kroll_signal.get('weight', 0.5)
        livermore_weight = livermore_signal.get('weight', 0.5)

        st.progress(kroll_weight, text=f"Kroll: {kroll_weight*100:.0f}%")
        st.progress(livermore_weight, text=f"Livermore: {livermore_weight*100:.0f}%")

        # Individual actions
        st.markdown(f"- Kroll → **{kroll_signal.get('action', 'N/A')}** ({kroll_signal.get('confidence', 'N/A')})")
        st.markdown(f"- Livermore → **{livermore_signal.get('action', 'N/A')}** ({livermore_signal.get('confidence', 'N/A')})")

    # Fusion factors (explanation)
    fusion_factors = recommendation.get('fusion_factors', [])
    if fusion_factors:
        with st.expander("🔍 融合分析"):
            for factor in fusion_factors:
                # Color code factors
                if '✓' in factor or 'AGREEMENT' in factor:
                    st.markdown(f"✅ {factor}")
                elif '⚠' in factor or 'PARTIAL' in factor:
                    st.markdown(f"⚠️ {factor}")
                elif '✗' in factor or 'CONFLICT' in factor:
                    st.markdown(f"❌ {factor}")
                else:
                    st.markdown(f"• {factor}")

    # Data source badge
    from investapp.components.data_source_badge import render_data_source_badge
    data_source = recommendation.get('data_source', 'Unknown')
    data_timestamp = recommendation.get('data_timestamp', '')
    data_freshness = recommendation.get('data_freshness', 'historical')

    st.divider()
    render_data_source_badge(data_source, data_timestamp, data_freshness)


def _render_individual_card(
    recommendation: Dict[str, Any],
    strategy_name: str,
    color: str = "blue"
) -> None:
    """Render an individual strategy recommendation card (Kroll or Livermore)."""
    action = recommendation.get('action', 'HOLD')
    confidence = recommendation.get('confidence', 'LOW')
    entry_price = recommendation.get('entry_price', 0)
    stop_loss = recommendation.get('stop_loss', 0)
    take_profit = recommendation.get('take_profit', 0)
    position_size = recommendation.get('position_size_pct', 0)

    # Action emoji
    action_emoji = {
        'BUY': '🟢',
        'SELL': '🔴',
        'HOLD': '⚪'
    }.get(action, '⚪')

    st.markdown(f"**操作:** {action_emoji} {action}")
    st.markdown(f"**置信度:** {confidence}")

    st.metric("入场", f"¥{entry_price:.2f}", label_visibility="collapsed")

    if entry_price > 0:
        st.metric("止损", f"¥{stop_loss:.2f}", delta=f"{((stop_loss/entry_price - 1)*100):.1f}%", delta_color="inverse")
        st.metric("目标", f"¥{take_profit:.2f}", delta=f"+{((take_profit/entry_price - 1)*100):.1f}%")
    else:
        st.metric("止损", f"¥{stop_loss:.2f}")
        st.metric("目标", f"¥{take_profit:.2f}")

    st.metric("仓位", f"{position_size:.1f}%")

    # Key factors
    key_factors = recommendation.get('key_factors', [])
    if key_factors:
        with st.expander("📋 关键因素"):
            for factor in key_factors[:5]:  # Show first 5 factors
                st.markdown(f"• {factor}")


def render_conflict_warning(fused_recommendation: Dict[str, Any]) -> None:
    """Render conflict warning banner when advisors disagree (T053).

    Args:
        fused_recommendation: Fused recommendation with conflict info
    """
    fusion_factors = fused_recommendation.get('fusion_factors', [])

    # Extract conflict message
    conflict_msg = None
    for factor in fusion_factors:
        if 'CONFLICT' in factor:
            conflict_msg = factor
            break

    if conflict_msg:
        st.error(f"""
        ### ⚠️ 检测到策略冲突

        {conflict_msg}

        **建议:** 在采取行动前，请仔细审查两个策略的独立推荐。
        冲突信号可能表明市场不确定性或风险评估分歧。

        **已采取措施:** 系统出于安全考虑，默认为 HOLD（持有）。
        """, icon="⚠️")
    else:
        # Partial agreement warning
        partial_msg = None
        for factor in fusion_factors:
            if 'PARTIAL' in factor:
                partial_msg = factor
                break

        if partial_msg:
            st.warning(f"""
            ### ⚠️ 部分一致

            {partial_msg}

            一个策略谨慎，而另一个策略发出入场/出场信号。请以较低置信度谨慎操作。
            """, icon="⚠️")
