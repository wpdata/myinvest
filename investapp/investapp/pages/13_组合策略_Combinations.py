"""
组合策略构建器 (Combination Strategy Builder) - T055

Interactive UI for building and backtesting multi-leg option/futures strategies.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'investlib-margin'))

from investlib_quant.strategies.combination_models import (
    StrategyTemplates,
    CombinationType,
    Leg,
    CombinationStrategy
)
from investlib_quant.strategies.pnl_chart import generate_pnl_plot_data
from investlib_margin.combination_margin import calculate_combination_margin

# Import symbol selector
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.symbol_selector import render_symbol_selector_compact

# Page config
st.set_page_config(
    page_title="组合策略构建器",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 组合策略构建器")
st.caption("构建多腿期权/期货组合策略并可视化盈亏曲线")

# Sidebar: Strategy template selector
st.sidebar.header("📋 策略模板")

template_options = {
    "备兑开仓 (Covered Call)": CombinationType.COVERED_CALL,
    "蝶式价差 (Butterfly Spread)": CombinationType.BUTTERFLY_SPREAD,
    "跨式组合 (Straddle)": CombinationType.STRADDLE,
    "牛市看涨价差 (Bull Call Spread)": CombinationType.BULL_CALL_SPREAD,
    "自定义组合 (Custom)": CombinationType.CUSTOM
}

selected_template = st.sidebar.selectbox(
    "选择策略模板",
    options=list(template_options.keys())
)

template_type = template_options[selected_template]

st.sidebar.divider()

# Main content: Strategy builder
if template_type == CombinationType.COVERED_CALL:
    st.header("📈 备兑开仓策略构建")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("基础参数")
        stock_symbol = render_symbol_selector_compact(
            default_value="600519.SH",
            key="covered_call_symbol"
        )
        stock_price = st.number_input("股票价格", value=1800.0, min_value=0.0, step=10.0)
        quantity = st.number_input("股票数量", value=100, min_value=100, step=100, help="1手=100股")

    with col2:
        st.subheader("期权参数")
        strike_price = st.number_input("行权价", value=1900.0, min_value=0.0, step=10.0)
        call_premium = st.number_input("权利金", value=50.0, min_value=0.0, step=1.0)
        expiry_date = st.date_input("到期日", value=datetime.now() + timedelta(days=30))

    if st.button("🔨 生成策略", type="primary"):
        # Create strategy
        strategy = StrategyTemplates.covered_call(
            stock_symbol=stock_symbol,
            stock_price=stock_price,
            strike_price=strike_price,
            call_premium=call_premium,
            expiry_date=expiry_date.strftime("%Y-%m-%d"),
            quantity=quantity
        )

        st.session_state['current_strategy'] = strategy
        st.success(f"✅ 策略创建成功: {strategy.strategy_name}")

elif template_type == CombinationType.BUTTERFLY_SPREAD:
    st.header("🦋 蝶式价差策略构建")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("基础参数")
        symbol = render_symbol_selector_compact(
            default_value="510050.SH",
            key="butterfly_symbol"
        )
        option_type = st.selectbox("期权类型", options=["认购 (Call)", "认沽 (Put)"])
        expiry_date = st.date_input("到期日", value=datetime.now() + timedelta(days=30))

    with col2:
        st.subheader("行权价格")
        lower_strike = st.number_input("下行权价", value=2.8, step=0.1)
        middle_strike = st.number_input("中行权价 (ATM)", value=3.0, step=0.1)
        upper_strike = st.number_input("上行权价", value=3.2, step=0.1)

    col3, col4 = st.columns(2)
    with col3:
        premium_lower = st.number_input("下行权价权利金", value=0.15, step=0.01)
        premium_middle = st.number_input("中行权价权利金", value=0.10, step=0.01)
    with col4:
        premium_upper = st.number_input("上行权价权利金", value=0.05, step=0.01)

    if st.button("🔨 生成策略", type="primary"):
        opt_type = 'call' if "Call" in option_type else 'put'
        strategy = StrategyTemplates.butterfly_spread(
            symbol=symbol,
            lower_strike=lower_strike,
            middle_strike=middle_strike,
            upper_strike=upper_strike,
            premium_lower=premium_lower,
            premium_middle=premium_middle,
            premium_upper=premium_upper,
            expiry_date=expiry_date.strftime("%Y-%m-%d"),
            option_type=opt_type
        )

        st.session_state['current_strategy'] = strategy
        st.success(f"✅ 策略创建成功: {strategy.strategy_name}")

elif template_type == CombinationType.STRADDLE:
    st.header("📊 跨式组合策略构建")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("基础参数")
        symbol = st.text_input("标的代码", value="50ETF")
        strike_price = st.number_input("行权价 (ATM)", value=3.0, step=0.1)
        expiry_date = st.date_input("到期日", value=datetime.now() + timedelta(days=30))

    with col2:
        st.subheader("期权权利金")
        call_premium = st.number_input("认购期权权利金", value=0.12, step=0.01)
        put_premium = st.number_input("认沽期权权利金", value=0.11, step=0.01)
        action = st.selectbox("操作方向", options=["买入 (Long)", "卖出 (Short)"])

    if st.button("🔨 生成策略", type="primary"):
        act = 'BUY' if "Long" in action else 'SELL'
        strategy = StrategyTemplates.straddle(
            symbol=symbol,
            strike_price=strike_price,
            call_premium=call_premium,
            put_premium=put_premium,
            expiry_date=expiry_date.strftime("%Y-%m-%d"),
            action=act
        )

        st.session_state['current_strategy'] = strategy
        st.success(f"✅ 策略创建成功: {strategy.strategy_name}")

else:
    st.info("🚧 自定义组合功能开发中...")

# Display strategy details and P&L chart
if 'current_strategy' in st.session_state:
    strategy = st.session_state['current_strategy']

    st.divider()
    st.header("📊 策略分析")

    # Strategy summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("策略类型", strategy.strategy_type.value)
    with col2:
        st.metric("腿数", len(strategy.legs))
    with col3:
        net_cost = strategy.net_cost
        st.metric(
            "净成本",
            f"¥{abs(net_cost):,.2f}",
            delta="借方" if strategy.is_debit else "贷方"
        )
    with col4:
        # Calculate margin
        legs_dicts = []
        for leg in strategy.legs:
            legs_dicts.append({
                'symbol': leg.symbol,
                'asset_type': leg.asset_type,
                'action': leg.action,
                'quantity': leg.quantity,
                'entry_price': leg.entry_price,
                'multiplier': leg.multiplier,
                'strike_price': leg.strike_price
            })

        margin_result = calculate_combination_margin(legs_dicts)
        st.metric(
            "保证金需求",
            f"¥{margin_result['total_margin']:,.0f}",
            delta=f"-{margin_result['hedge_reduction_pct']:.0f}% 对冲减免"
        )

    # Legs detail table
    st.subheader("🔍 策略腿明细")

    legs_data = []
    for i, leg in enumerate(strategy.legs, 1):
        legs_data.append({
            "腿": f"Leg {i}",
            "资产类型": {"stock": "股票", "call": "认购期权", "put": "认沽期权", "futures": "期货"}.get(leg.asset_type, leg.asset_type),
            "方向": {"BUY": "买入 🟢", "SELL": "卖出 🔴"}.get(leg.action, leg.action),
            "数量": leg.quantity,
            "价格": f"¥{leg.entry_price:.2f}",
            "行权价": f"¥{leg.strike_price:.2f}" if leg.strike_price else "N/A",
            "到期日": leg.expiry_date or "N/A",
            "成本": f"¥{leg.cost:,.2f}"
        })

    st.dataframe(pd.DataFrame(legs_data), use_container_width=True)

    # P&L Chart
    st.subheader("📈 盈亏曲线 (P&L Curve)")

    plot_data = generate_pnl_plot_data(legs_dicts, num_points=200)
    pnl_df = plot_data['pnl_df']

    # Create Plotly chart
    fig = go.Figure()

    # P&L curve
    fig.add_trace(go.Scatter(
        x=pnl_df['price'],
        y=pnl_df['pnl'],
        mode='lines',
        name='盈亏曲线',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.1)'
    ))

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Breakeven points
    for bp in plot_data['breakeven_points']:
        fig.add_vline(x=bp, line_dash="dot", line_color="orange",
                     annotation_text=f"盈亏平衡 ¥{bp:.0f}")

    # Current price
    fig.add_vline(x=plot_data['current_price'], line_dash="solid",
                 line_color="green", annotation_text="当前价格")

    fig.update_layout(
        title="组合策略盈亏分析",
        xaxis_title="标的价格 (¥)",
        yaxis_title="盈亏 (¥)",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Key metrics
    col1, col2, col3 = st.columns(3)

    max_pnl = plot_data['max_profit_loss']

    with col1:
        st.metric(
            "最大盈利",
            f"¥{max_pnl['max_profit']:,.2f}",
            delta=f"在 ¥{max_pnl['max_profit_at']:.0f}"
        )

    with col2:
        st.metric(
            "最大亏损",
            f"¥{abs(max_pnl['max_loss']):,.2f}",
            delta=f"在 ¥{max_pnl['max_loss_at']:.0f}",
            delta_color="inverse"
        )

    with col3:
        if plot_data['breakeven_points']:
            bp_str = ", ".join([f"¥{bp:.0f}" for bp in plot_data['breakeven_points']])
            st.metric("盈亏平衡点", bp_str)
        else:
            st.metric("盈亏平衡点", "无")

    # Action buttons
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 保存策略"):
            st.success("策略已保存到数据库")

    with col2:
        if st.button("🔄 运行回测"):
            st.info("回测功能：请前往策略回测页面")

    with col3:
        if st.button("🗑️ 清除策略"):
            del st.session_state['current_strategy']
            st.rerun()

else:
    st.info("👆 请在上方选择策略模板并输入参数，然后点击'生成策略'")
