"""Recommendation Card Component for displaying investment recommendations."""

import streamlit as st
from typing import Dict, Any


def render_recommendation_card(recommendation: Dict[str, Any]) -> None:
    """Render a recommendation card in Streamlit.

    Args:
        recommendation: Recommendation dictionary from LivermoreAdvisor
    """
    symbol = recommendation.get('symbol', 'N/A')
    action = recommendation.get('action', 'HOLD')
    confidence = recommendation.get('confidence', 'MEDIUM')

    # Card container
    with st.container():
        # Header with symbol and action
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.subheader(f"📈 {symbol}")

        with col2:
            # Action badge
            action_color = {
                'BUY': '🟢',
                'STRONG_BUY': '🟢',
                'SELL': '🔴',
                'STRONG_SELL': '🔴',
                'HOLD': '🟡'
            }.get(action, '⚪')
            st.markdown(f"### {action_color} {action}")

        with col3:
            st.markdown(f"**{confidence}**")

        st.divider()

        # Price levels
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("入场价", f"¥{recommendation['entry_price']:.2f}")

        with col2:
            st.metric("止损价", f"¥{recommendation['stop_loss']:.2f}")

        with col3:
            st.metric("止盈价", f"¥{recommendation['take_profit']:.2f}")

        # Risk metrics
        col1, col2 = st.columns(2)

        with col1:
            st.metric("建议仓位", f"{recommendation['position_size_pct']:.1f}%")

        with col2:
            # Max loss in RED
            st.markdown(
                f"<div style='background-color: #ffebee; padding: 10px; border-radius: 5px;'>"
                f"<strong style='color: #d32f2f;'>最大损失: ¥{recommendation['max_loss']:.0f}</strong>"
                f"</div>",
                unsafe_allow_html=True
            )

        # Reasoning in expander
        with st.expander("📊 查看详细说明"):
            st.write("**策略分析：**")
            st.write(recommendation.get('reasoning', '暂无说明'))

            if 'key_factors' in recommendation and recommendation['key_factors']:
                st.write("**关键因素：**")
                for factor in recommendation['key_factors']:
                    st.write(f"- {factor}")

            # Metadata
            st.caption(
                f"顾问: {recommendation.get('advisor_name', 'Unknown')} "
                f"{recommendation.get('advisor_version', '')}"
            )
            st.caption(f"策略: {recommendation.get('strategy_name', 'Unknown')}")

        # Action button with confirmation dialog
        if st.button(f"确认执行 - {symbol}", key=f"execute_{symbol}", type="primary"):
            # Import here to avoid circular dependency
            from investapp.investapp.components.confirmation_dialog import show_confirmation_dialog
            from investapp.investapp.components.position_validator import PositionValidator
            from investlib_data.operation_logger import OperationLogger
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            import os

            # Validate position
            validator = PositionValidator()
            # Placeholder: current_holdings and capital should come from session/DB
            current_holdings = {}
            total_capital = 100000.0

            validation = validator.validate_position(
                recommendation, current_holdings, total_capital
            )

            if not validation.valid:
                st.error("⚠️ 仓位验证失败：")
                for error in validation.errors:
                    st.error(f"- {error}")
            else:
                # Show warnings if any
                for warning in validation.warnings:
                    st.warning(warning)

                # Show confirmation dialog
                result = show_confirmation_dialog(recommendation)

                if result and result['action'] == 'CONFIRM':
                    # Log operation
                    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/myinvest.db")
                    engine = create_engine(DATABASE_URL)
                    Session = sessionmaker(bind=engine)
                    session = Session()

                    try:
                        logger = OperationLogger(session)
                        op_id = logger.log_operation(
                            user_id="default_user",
                            operation_type="BUY" if recommendation['action'] in ['BUY', 'STRONG_BUY'] else "SELL",
                            symbol=symbol,
                            recommendation=recommendation,
                            modification=result.get('modifications'),
                            status="EXECUTED",
                            notes="模拟交易执行"
                        )

                        st.success(f"✅ 操作已记录 (ID: {op_id[:8]}...)")
                        st.info('请前往"操作日志"页面查看详情')

                    finally:
                        session.close()

        st.divider()


def render_recommendation_list(recommendations: list) -> None:
    """Render multiple recommendation cards.

    Args:
        recommendations: List of recommendation dictionaries
    """
    if not recommendations:
        st.info("暂无推荐，请点击'生成推荐'按钮")
        return

    st.subheader(f"📋 今日推荐 ({len(recommendations)})")

    for i, rec in enumerate(recommendations[:3]):  # Limit to 3
        render_recommendation_card(rec)
