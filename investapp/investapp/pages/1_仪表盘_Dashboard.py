"""Streamlit page for the main dashboard."""

import streamlit as st
import sys
import os
import pandas as pd
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investapp.components.dashboard_backend import get_dashboard_data
from investapp.components.chart_renderer import render_profit_loss_curve, render_asset_distribution
from investapp.components.recommendation_card import render_recommendation_list
from investapp.components.fusion_card import render_fusion_card
import os

st.set_page_config(page_title="仪表盘 Dashboard", page_icon="📊", layout="wide")

# Database connection
# 使用绝对路径确保无论从哪个目录启动都能找到正确的数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////Users/pw/ai/myinvest/data/myinvest.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

st.title("📊 投资仪表盘")

# Add holdings price refresh button
col_title, col_refresh = st.columns([4, 1])
with col_refresh:
    if st.button("🔄 刷新持仓价格", use_container_width=True, type="secondary"):
        with st.spinner("正在更新持仓价格..."):
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from investapp.utils.holdings_updater import HoldingsUpdater

                session = Session()
                updater = HoldingsUpdater()
                results = updater.update_all_holdings(session)
                session.close()

                if results['updated'] > 0:
                    st.success(
                        f"✅ 成功更新 {results['updated']}/{results['total_holdings']} 个持仓价格！"
                    )
                    if results['failed'] > 0:
                        st.warning(f"⚠️ {results['failed']} 个持仓更新失败")
                    st.rerun()  # Refresh the page to show updated data
                elif results['total_holdings'] == 0:
                    st.info("暂无持仓需要更新")
                else:
                    st.error("❌ 所有持仓更新失败")
                    for error in results['errors']:
                        st.error(f"{error['symbol']}: {error['error']}")

            except Exception as e:
                st.error(f"❌ 更新失败: {str(e)}")

# Load data
session = Session()
dashboard_data = get_dashboard_data(session)
session.close()

if not dashboard_data["holdings"]:
    st.info('还没有投资记录，请先到"投资记录管理"页面导入或添加记录。')
else:
    # --- Metrics Section ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="总资产 (CNY)", value=f"{dashboard_data['total_assets']:.2f}")
    with col2:
        st.metric(label="持仓市值 (CNY)", value=f"{dashboard_data['total_holdings_value']:.2f}")
    with col3:
        st.metric(label="可用资金 (CNY)", value=f"{dashboard_data['total_cash']:.2f}")

    # --- Charts Section ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("累计收益")
        timeframe = st.selectbox("选择时间范围", ["daily", "weekly", "monthly"], key="pnl_timeframe")
        fig_profit = render_profit_loss_curve(dashboard_data["profit_loss_history"], timeframe)
        st.plotly_chart(fig_profit, use_container_width=True)

    with col2:
        st.subheader("资产分布")
        fig_dist = render_asset_distribution(dashboard_data["holdings"])
        st.plotly_chart(fig_dist, use_container_width=True)

    # --- Holdings Section ---
    st.subheader("当前持仓")

    # Display holdings grouped by asset type
    from investlib_data.models import AssetType

    asset_type_names = {
        AssetType.STOCK: "股票",
        AssetType.ETF: "ETF基金",
        AssetType.FUND: "场外基金",
        AssetType.FUTURES: "期货",
        AssetType.OPTION: "期权",
        AssetType.BOND: "债券",
        AssetType.CONVERTIBLE_BOND: "可转债",
        AssetType.OTHER: "其他"
    }

    for asset_type, holdings_list in dashboard_data["holdings_by_type"].items():
        st.markdown(f"### {asset_type_names.get(asset_type, asset_type.value)}")

        # Convert holdings to DataFrame
        holdings_df = pd.DataFrame([h.__dict__ for h in holdings_list])
        holdings_df = holdings_df.drop(columns=['_sa_instance_state', 'holding_id', 'created_at', 'updated_at', 'last_update_timestamp'], errors='ignore')

        # Convert enum to string
        if 'asset_type' in holdings_df.columns:
            holdings_df['asset_type'] = holdings_df['asset_type'].apply(lambda x: x.value if hasattr(x, 'value') else x)

        # Rename columns for better display
        holdings_df = holdings_df.rename(columns={
            'symbol': '代码',
            'asset_type': '类型',
            'quantity': '数量',
            'purchase_price': '成本价',
            'current_price': '当前价',
            'profit_loss_amount': '盈亏金额',
            'profit_loss_pct': '盈亏比例(%)',
            'purchase_date': '买入日期'
        })

        # Calculate market value
        if '数量' in holdings_df.columns and '当前价' in holdings_df.columns:
            holdings_df['市值'] = holdings_df['数量'] * holdings_df['当前价']

        st.dataframe(holdings_df, use_container_width=True)

        # Show account balance for this type if exists
        if asset_type in dashboard_data["balances_by_type"]:
            balance = dashboard_data["balances_by_type"][asset_type]
            st.caption(f"可用资金: {balance:.2f} CNY")

        st.divider()

    # Show account types with only cash (no holdings)
    for asset_type, balance in dashboard_data["balances_by_type"].items():
        if asset_type not in dashboard_data["holdings_by_type"] and balance > 0:
            st.markdown(f"### {asset_type_names.get(asset_type, asset_type.value)}")
            st.info(f"暂无持仓")
            st.caption(f"账户权益: {balance:.2f} CNY")
            st.divider()

# --- Recommendations Section (V0.2 Real Implementation) ---
st.divider()
st.header("💡 今日推荐")

# Get watchlist symbols (could be from user config or holdings)
def get_watchlist_symbols():
    """Get watchlist symbols from holdings or default list."""
    if dashboard_data["holdings"]:
        # Use first few holdings as watchlist
        symbols = list(set([h.symbol for holdings_list in dashboard_data["holdings_by_type"].values()
                           for h in holdings_list]))[:3]
        return symbols
    else:
        # Default watchlist
        return ["600519.SH", "000001.SZ"]

watchlist = get_watchlist_symbols()

# Tabs for different strategies
tab_fusion, tab_livermore, tab_kroll, tab_history = st.tabs(
    ["🎯 融合推荐", "📈 120日均线突破策略", "🛡️ Kroll风险控制策略", "📜 历史记录"]
)

with tab_fusion:
    st.markdown("""
    **融合策略**结合了 Livermore (趋势跟随) 和 Kroll (风险控制) 两个策略的优势。
    默认权重：Livermore 60% + Kroll 40%
    """)

    # Symbol selector
    selected_symbol = st.selectbox("选择股票", watchlist, key="fusion_symbol_select")

    if st.button("🔮 生成融合推荐", type="primary", key="gen_fusion"):
        with st.spinner(f"正在为 {selected_symbol} 生成融合推荐..."):
            try:
                # Add library paths
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-data'))

                # 注意：Fusion策略尚未迁移到策略注册中心，暂时保持原有导入方式
                # TODO: 将Fusion策略添加到策略注册中心后，使用 StrategyRegistry.create('fusion_strategy')
                from investlib_quant.fusion_strategy import FusionStrategy

                # Generate fusion recommendation (analyze method fetches data internally)
                fusion_strategy = FusionStrategy(livermore_weight=0.6, kroll_weight=0.4)
                recommendation = fusion_strategy.analyze(selected_symbol)

                # Store in session state
                st.session_state['fusion_rec'] = recommendation
                st.session_state['fusion_rec_symbol'] = selected_symbol

                st.success(f"✅ 已生成 {selected_symbol} 的融合推荐")

            except Exception as e:
                st.error(f"❌ 生成推荐失败: {str(e)}")
                st.exception(e)

    # Display fusion recommendation if exists
    if 'fusion_rec' in st.session_state and st.session_state.get('fusion_rec_symbol') == selected_symbol:
        st.divider()
        render_fusion_card(
            st.session_state['fusion_rec'],
            st.session_state['fusion_rec'].get('kroll_signal'),
            st.session_state['fusion_rec'].get('livermore_signal')
        )

with tab_livermore:
    st.markdown("""
    **120日均线突破策略**：经典趋势跟随策略，捕捉中长期趋势。
    - 120日均线趋势判断
    - 突破信号识别+成交量确认
    - 动态止损止盈（-3.5% / +7%）
    """)

    selected_symbol_liv = st.selectbox("选择股票", watchlist, key="liv_symbol_select")

    if st.button("📈 生成推荐 (120日均线突破策略)", key="gen_liv"):
        with st.spinner(f"正在为 {selected_symbol_liv} 生成推荐..."):
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))

                # 使用策略注册中心获取策略
                from investlib_quant.strategies import StrategyRegistry

                strategy = StrategyRegistry.create('ma_breakout_120')
                recommendation = strategy.analyze(selected_symbol_liv)

                st.session_state['liv_rec'] = recommendation
                st.session_state['liv_rec_symbol'] = selected_symbol_liv
                st.success(f"✅ 已生成推荐")

            except Exception as e:
                st.error(f"❌ 生成推荐失败: {str(e)}")

    if 'liv_rec' in st.session_state and st.session_state.get('liv_rec_symbol') == selected_symbol_liv:
        st.divider()
        rec = st.session_state['liv_rec']

        col1, col2, col3 = st.columns(3)
        with col1:
            action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(rec['action'], '⚪')
            st.metric("操作", f"{action_emoji} {rec['action']}")
        with col2:
            st.metric("置信度", rec['confidence'])
        with col3:
            st.metric("仓位", f"{rec['position_size_pct']:.1f}%")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("入场价", f"¥{rec['entry_price']:.2f}")
        with col2:
            st.metric("止损", f"¥{rec['stop_loss']:.2f}")
        with col3:
            st.metric("止盈", f"¥{rec['take_profit']:.2f}")

        with st.expander("📋 关键因素"):
            for factor in rec.get('key_factors', []):
                st.markdown(f"• {factor}")

with tab_kroll:
    st.markdown("""
    **Kroll风险控制策略**：风险优先的稳健策略，注重资金保护。
    - 60日均线+RSI超买超卖判断
    - ATR波动率动态调整仓位
    - 严格止损 (2.5%)
    - 高波动降低仓位（12% → 8%）
    """)

    selected_symbol_kroll = st.selectbox("选择股票", watchlist, key="kroll_symbol_select")

    if st.button("🛡️ 生成推荐 (Kroll风险控制策略)", key="gen_kroll"):
        with st.spinner(f"正在为 {selected_symbol_kroll} 生成推荐..."):
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))

                # 使用策略注册中心获取策略
                from investlib_quant.strategies import StrategyRegistry

                strategy = StrategyRegistry.create('ma60_rsi_volatility')
                recommendation = strategy.analyze(selected_symbol_kroll)

                st.session_state['kroll_rec'] = recommendation
                st.session_state['kroll_rec_symbol'] = selected_symbol_kroll
                st.success(f"✅ 已生成推荐")

            except Exception as e:
                st.error(f"❌ 生成推荐失败: {str(e)}")

    if 'kroll_rec' in st.session_state and st.session_state.get('kroll_rec_symbol') == selected_symbol_kroll:
        st.divider()
        rec = st.session_state['kroll_rec']

        col1, col2, col3 = st.columns(3)
        with col1:
            action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(rec['action'], '⚪')
            st.metric("操作", f"{action_emoji} {rec['action']}")
        with col2:
            st.metric("置信度", rec['confidence'])
        with col3:
            st.metric("风险等级", rec.get('risk_level', 'MEDIUM'))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("入场价", f"¥{rec['entry_price']:.2f}")
        with col2:
            st.metric("止损", f"¥{rec['stop_loss']:.2f}")
        with col3:
            st.metric("止盈", f"¥{rec['take_profit']:.2f}")

        with st.expander("📋 关键因素"):
            for factor in rec.get('key_factors', []):
                st.markdown(f"• {factor}")

with tab_history:
    st.markdown("### 📜 推荐历史记录")

    # Filters in sidebar
    with st.expander("🔍 筛选选项", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            auto_filter = st.selectbox(
                "生成方式",
                ["全部", "自动生成", "手动生成"],
                key="rec_auto_filter"
            )

        with col_f2:
            strategy_filter = st.selectbox(
                "策略类型",
                ["全部", "Livermore", "Kroll", "Fusion", "AutoScheduler"],
                key="rec_strategy_filter"
            )

        with col_f3:
            action_filter = st.selectbox(
                "操作类型",
                ["全部", "BUY", "SELL", "HOLD"],
                key="rec_action_filter"
            )

        limit_filter = st.slider(
            "显示数量",
            min_value=10,
            max_value=100,
            value=30,
            step=10,
            key="rec_limit_filter"
        )

    try:
        # Extract DB path from DATABASE_URL (format: sqlite:////path/to/db)
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)

        # Build query with filters
        query = """
        SELECT
            recommendation_id,
            symbol,
            strategy_name,
            action,
            confidence,
            entry_price,
            stop_loss,
            take_profit,
            position_size_pct,
            max_loss_amount,
            expected_return_pct,
            advisor_name,
            reasoning,
            key_factors,
            data_source,
            data_freshness,
            market_data_timestamp,
            created_timestamp,
            is_automated
        FROM investment_recommendations
        WHERE 1=1
        """

        # Apply filters
        if auto_filter == "自动生成":
            query += " AND is_automated = 1"
        elif auto_filter == "手动生成":
            query += " AND (is_automated = 0 OR is_automated IS NULL)"

        if strategy_filter != "全部":
            query += f" AND strategy_name = '{strategy_filter}'"

        if action_filter != "全部":
            query += f" AND action = '{action_filter}'"

        query += f" ORDER BY created_timestamp DESC LIMIT {limit_filter}"

        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            # Display statistics
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

            with col_stat1:
                st.metric("总推荐数", len(df))

            with col_stat2:
                auto_count = df['is_automated'].sum() if 'is_automated' in df.columns else 0
                st.metric("自动生成", int(auto_count))

            with col_stat3:
                buy_count = len(df[df['action'] == 'BUY'])
                st.metric("买入信号", buy_count)

            with col_stat4:
                sell_count = len(df[df['action'] == 'SELL'])
                st.metric("卖出信号", sell_count)

            st.divider()

            # Display recommendations as expandable cards
            for idx, row in df.iterrows():
                # Card header
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(row['action'], '⚪')
                auto_badge = "🤖 自动" if row.get('is_automated') else "👤 手动"

                header = f"{action_emoji} **{row['symbol']}** - {row['strategy_name']} | {auto_badge} | {row['created_timestamp']}"

                with st.expander(header, expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("#### 📊 交易参数")
                        st.markdown(f"**操作:** {row['action']}")
                        st.markdown(f"**置信度:** {row['confidence']}")
                        st.markdown(f"**入场价:** ¥{row['entry_price']:.2f}")
                        st.markdown(f"**止损:** ¥{row['stop_loss']:.2f}")
                        st.markdown(f"**止盈:** ¥{row['take_profit']:.2f}")

                    with col2:
                        st.markdown("#### 💰 风险收益")
                        st.markdown(f"**仓位:** {row['position_size_pct']:.1f}%")
                        st.markdown(f"**最大亏损:** ¥{row['max_loss_amount']:.2f}")
                        st.markdown(f"**预期收益:** {row['expected_return_pct']:.2f}%")

                        # Calculate risk-reward ratio
                        risk_amount = abs(row['entry_price'] - row['stop_loss'])
                        reward_amount = abs(row['take_profit'] - row['entry_price'])
                        if risk_amount > 0:
                            risk_reward = reward_amount / risk_amount
                            st.markdown(f"**风险收益比:** 1:{risk_reward:.2f}")

                    with col3:
                        st.markdown("#### ℹ️ 数据来源")
                        st.markdown(f"**策略:** {row['advisor_name']}")
                        st.markdown(f"**数据源:** {row['data_source']}")
                        st.markdown(f"**数据新鲜度:** {row['data_freshness']}")
                        st.markdown(f"**生成时间:** {row['created_timestamp']}")

                    # Reasoning
                    if row['reasoning']:
                        st.markdown("#### 💡 推荐理由")
                        st.info(row['reasoning'])

                    # Key factors
                    if row['key_factors']:
                        st.markdown("#### 🔑 关键因素")
                        factors = row['key_factors'].split('; ') if isinstance(row['key_factors'], str) else []
                        for factor in factors:
                            if factor.strip():
                                st.markdown(f"• {factor}")

            st.caption(f"显示最近 {len(df)} 条推荐记录")

        else:
            st.info("暂无符合条件的推荐记录。尝试调整筛选条件或点击上方按钮生成新推荐。")

    except Exception as e:
        st.warning(f"无法加载历史记录: {e}")
        st.info("数据库表可能尚未初始化。生成第一个推荐后，历史记录将显示在这里。")
