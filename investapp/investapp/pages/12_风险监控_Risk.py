"""风险监控仪表盘 (Risk Monitoring Dashboard)

Real-time risk metrics with auto-refresh:
- VaR/CVaR
- Position heatmap
- Margin usage
- Liquidation warnings
- Option Greeks
- Correlation matrix
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 seconds
count = st_autorefresh(interval=5000, key="risk_refresh")

st.set_page_config(page_title="风险监控仪表盘", page_icon="⚠️", layout="wide")

st.title("⚠️ 风险监控仪表盘")
st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 自动刷新: 5秒")

# Initialize risk orchestrator
@st.cache_resource
def get_risk_orchestrator():
    from investlib_risk.dashboard import RiskDashboardOrchestrator
    return RiskDashboardOrchestrator(cache_ttl_seconds=5, auto_refresh_interval=5)

orchestrator = get_risk_orchestrator()


# Load portfolio data
@st.cache_data(ttl=5)
def load_portfolio_data():
    """Load current portfolio positions and account balance."""
    from investlib_data.database import SessionLocal
    from investlib_data.models import CurrentHolding

    session = SessionLocal()
    try:
        holdings = session.query(CurrentHolding).all()

        positions = []
        for holding in holdings:
            positions.append({
                'symbol': holding.symbol,
                'quantity': holding.quantity,
                'asset_type': holding.asset_type.value if hasattr(holding.asset_type, 'value') else str(holding.asset_type),
                'entry_price': holding.purchase_price,
                'value': holding.quantity * holding.purchase_price,
                'direction': holding.direction or 'long',
                'margin_used': holding.margin_used or 0.0,
                'greeks': {}  # TODO: Load from options positions table
            })

        # Calculate account balance (simplified)
        total_value = sum(p['value'] for p in positions)
        account_balance = total_value * 1.5  # Assume some cash reserve

        return {
            'positions': positions,
            'account_balance': account_balance
        }
    finally:
        session.close()


@st.cache_data(ttl=5)
def load_price_history():
    """Load recent price history for risk calculations."""
    from investlib_data.database import SessionLocal
    from investlib_data.models import MarketDataPoint

    session = SessionLocal()
    try:
        # Get last 90 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        records = session.query(MarketDataPoint).filter(
            MarketDataPoint.timestamp >= start_date
        ).all()

        if not records:
            return pd.DataFrame()

        data = []
        for record in records:
            data.append({
                'symbol': record.symbol,
                'timestamp': record.timestamp,
                'close': record.close_price
            })

        return pd.DataFrame(data)
    finally:
        session.close()


# Load data
try:
    portfolio = load_portfolio_data()
    price_history = load_price_history()

    if not portfolio['positions']:
        st.warning("📭 当前没有持仓，无法计算风险指标")
        st.stop()

    # Calculate all risk metrics
    metrics = orchestrator.calculate_all_metrics(
        portfolio=portfolio,
        price_history=price_history,
        industry_map=None  # TODO: Add industry classification
    )

except Exception as e:
    st.error(f"❌ 加载数据失败: {e}")
    st.stop()


# Layout: 3 columns for key metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="95% VaR (1日)",
        value=f"¥{abs(metrics['var_95'] * portfolio['account_balance']):,.0f}",
        delta=f"{metrics['var_95']*100:.2f}% of assets",
        delta_color="inverse"
    )

with col2:
    st.metric(
        label="95% CVaR (条件VaR)",
        value=f"¥{abs(metrics['cvar_95'] * portfolio['account_balance']):,.0f}",
        delta=f"{metrics['cvar_95']*100:.2f}% expected loss",
        delta_color="inverse"
    )

with col3:
    margin_pct = metrics['margin_usage_pct']
    safety_buffer = 100 - margin_pct
    st.metric(
        label="保证金使用率",
        value=f"{margin_pct:.1f}%",
        delta=f"安全缓冲: {safety_buffer:.1f}%",
        delta_color="normal" if margin_pct < 70 else "inverse"
    )

st.divider()

# Row 1: Position Heatmap + Liquidation Warnings
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 持仓热力图")

    if portfolio['positions']:
        # Prepare data for bubble chart
        positions_df = pd.DataFrame(portfolio['positions'])

        # Add asset type emoji
        asset_icons = {
            'stock': '📈',
            'futures': '📊',
            'option': '📉'
        }
        positions_df['icon'] = positions_df['asset_type'].map(asset_icons)
        positions_df['label'] = positions_df['icon'] + ' ' + positions_df['symbol']

        # Calculate P&L (simplified - using current price vs entry)
        # TODO: Get actual current prices
        positions_df['pnl_pct'] = np.random.uniform(-10, 15, len(positions_df))  # Placeholder

        # Create bubble chart
        fig = px.scatter(
            positions_df,
            x='symbol',
            y='pnl_pct',
            size='value',
            color='pnl_pct',
            color_continuous_scale=['red', 'yellow', 'green'],
            hover_data=['asset_type', 'quantity', 'value'],
            labels={'pnl_pct': '盈亏 (%)', 'symbol': '代码'}
        )

        fig.update_layout(
            height=400,
            xaxis_title="",
            yaxis_title="盈亏 (%)",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("无持仓数据")

with col_right:
    st.subheader("⚠️ 强制平仓预警")

    warnings = metrics['liquidation_warnings']

    if warnings:
        for warning in warnings:
            severity_color = "🔴" if warning['severity'] == 'critical' else "🟡"

            with st.container():
                st.markdown(f"{severity_color} **{warning['symbol']}**")
                st.caption(warning['message'])
                st.progress(max(0, min(100, int(warning['distance_pct'] * 10))) / 100)
                st.caption(
                    f"当前: ¥{warning['current_price']:.2f} | "
                    f"平仓价: ¥{warning['liquidation_price']:.2f}"
                )
                st.divider()
    else:
        st.success("✅ 暂无平仓风险")

st.divider()

# Row 2: Concentration + Greeks
col_conc, col_greeks = st.columns(2)

with col_conc:
    st.subheader("🎯 集中度风险")

    conc = metrics['concentration']

    if conc:
        st.metric("最大单一持仓", f"{conc['max_single_position_pct']:.1f}%")
        st.metric("前3持仓集中度", f"{conc['top3_concentration_pct']:.1f}%")
        st.metric("赫芬达尔指数 (HHI)", f"{conc['herfindahl_index']:.3f}")
        st.caption("HHI < 0.15 为分散，> 0.25 为集中")

        # Industry concentration
        industry_conc = metrics['industry_concentration']
        if industry_conc:
            st.write("**行业分布:**")
            industry_df = pd.DataFrame([
                {'行业': k, '占比%': v}
                for k, v in industry_conc.items()
            ])
            st.dataframe(industry_df, hide_index=True, use_container_width=True)

with col_greeks:
    st.subheader("🔢 期权Greeks汇总")

    greeks = metrics.get('greeks', {})

    if greeks and any(greeks.values()):
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.metric("总Delta", f"{greeks['total_delta']:,.0f}")
            st.metric("总Gamma", f"{greeks['total_gamma']:,.0f}")
            st.metric("总Vega", f"{greeks['total_vega']:,.0f}")

        with col_g2:
            st.metric("总Theta (每日)", f"{greeks['total_theta']:,.0f}")
            st.metric("总Rho", f"{greeks['total_rho']:,.0f}")

        st.caption("Delta: 价格敏感度 | Theta: 时间衰减 | Vega: 波动率敏感度")
    else:
        st.info("无期权持仓")

st.divider()

# Row 3: Correlation Heatmap
st.subheader("🔗 相关性矩阵 (60日滚动)")

corr_matrix = metrics['correlation_matrix']

if not corr_matrix.empty:
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdYlGn',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="相关系数")
    ))

    fig.update_layout(
        height=500,
        xaxis_title="",
        yaxis_title=""
    )

    st.plotly_chart(fig, use_container_width=True)

    # High correlation pairs
    high_corr_pairs = metrics['high_correlation_pairs']
    if high_corr_pairs:
        st.warning(f"⚠️ 发现 {len(high_corr_pairs)} 对高相关性持仓 (|相关系数| ≥ 0.7)")

        for symbol1, symbol2, corr_value in high_corr_pairs[:5]:
            st.caption(f"• {symbol1} vs {symbol2}: {corr_value:.2f}")
else:
    st.info("数据不足，无法计算相关性矩阵 (需要至少60天历史数据)")

# Footer
st.divider()
st.caption(
    "💡 **风险提示**: 本仪表盘基于历史数据模拟，不构成投资建议。"
    "实际风险可能因市场剧烈波动而超出预测范围。"
)
