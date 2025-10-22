"""策略审批工作流页面 (T092).

显示待审批的策略，允许用户审批/拒绝策略。
只有已审批的策略才能用于实盘推荐生成。
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="策略审批 Approval", page_icon="✅", layout="wide")

st.title("✅ 策略审批工作流")

st.markdown("""
在回测策略用于生成**实盘推荐**之前，审查并批准它们。
只有已审批的策略会被自动调度器使用。
""")

# Connect to database
DB_PATH = "/Users/pw/ai/myinvest/data/myinvest.db"

def get_pending_approvals():
    """获取所有待审批的策略。"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        sa.id as approval_id,
        sa.backtest_id,
        sa.status,
        sa.notes,
        br.strategy_name,
        br.strategy_version,
        br.symbols,
        br.start_date,
        br.end_date,
        br.total_return,
        br.max_drawdown,
        br.sharpe_ratio,
        br.win_rate,
        br.total_trades,
        br.created_at as backtest_date
    FROM strategy_approval sa
    JOIN backtest_results br ON sa.backtest_id = br.id
    WHERE sa.status = 'PENDING_APPROVAL'
    ORDER BY br.created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_approved_strategies():
    """获取所有已审批的策略。"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        sa.id as approval_id,
        sa.backtest_id,
        sa.status,
        sa.approver_id,
        sa.approval_time,
        sa.notes,
        br.strategy_name,
        br.strategy_version,
        br.total_return,
        br.sharpe_ratio
    FROM strategy_approval sa
    JOIN backtest_results br ON sa.backtest_id = br.id
    WHERE sa.status = 'APPROVED'
    ORDER BY sa.approval_time DESC
    LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def approve_strategy(approval_id: str, notes: str):
    """审批策略。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE strategy_approval
        SET status = 'APPROVED',
            approver_id = 'default_user',
            approval_time = ?,
            notes = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), notes, approval_id))
    conn.commit()
    conn.close()

def reject_strategy(approval_id: str, reason: str):
    """拒绝策略。"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE strategy_approval
        SET status = 'REJECTED',
            approver_id = 'default_user',
            approval_time = ?,
            rejection_reason = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), reason, approval_id))
    conn.commit()
    conn.close()

# Tabs for different views
tab1, tab2 = st.tabs(["📋 待审批", "✅ 已审批策略"])

with tab1:
    st.header("待审批策略")

    pending = get_pending_approvals()

    if pending.empty:
        st.info("🎉 没有待审批项。所有策略都已审查！")
    else:
        st.markdown(f"**{len(pending)} 个策略**等待审批")

        # Display each pending approval
        for idx, row in pending.iterrows():
            with st.expander(
                f"🔍 {row['strategy_name']} v{row['strategy_version']} - "
                f"{row['symbols']} ({row['start_date']} 至 {row['end_date']})",
                expanded=(idx == 0)  # Expand first one
            ):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    return_pct = row['total_return'] * 100
                    st.metric("总收益", f"{return_pct:.2f}%")

                with col2:
                    dd_pct = row['max_drawdown'] * 100
                    st.metric("最大回撤", f"{dd_pct:.2f}%")

                with col3:
                    st.metric("Sharpe 比率", f"{row['sharpe_ratio']:.2f}")

                with col4:
                    win_rate_pct = row['win_rate'] * 100 if row['win_rate'] else 0
                    st.metric("胜率", f"{win_rate_pct:.1f}%")

                # Risk assessment
                st.divider()
                st.markdown("### 风险评估")

                # Determine risk level
                if row['sharpe_ratio'] > 1.5 and row['max_drawdown'] < 0.15:
                    risk_badge = "🟢 **低风险**"
                    recommendation = "✅ **建议审批**"
                elif row['sharpe_ratio'] > 1.0 and row['max_drawdown'] < 0.25:
                    risk_badge = "🟡 **中等风险**"
                    recommendation = "⚠️ **谨慎可接受**"
                else:
                    risk_badge = "🔴 **高风险**"
                    recommendation = "❌ **不建议审批**"

                st.markdown(f"{risk_badge} | {recommendation}")

                st.markdown(f"""
                **性能摘要:**
                - 收益: {return_pct:.2f}% 在 {row['total_trades']} 次交易中
                - Sharpe: {row['sharpe_ratio']:.2f} {'✓ 良好' if row['sharpe_ratio'] > 1.0 else '⚠️ 偏弱'}
                - 回撤: {dd_pct:.2f}% {'✓ 可接受' if row['max_drawdown'] < 0.20 else '⚠️ 偏高'}
                - 胜率: {win_rate_pct:.1f}% {'✓ 强劲' if win_rate_pct > 50 else '⚠️ 偏弱'}
                """)

                # Approval form
                st.divider()
                st.markdown("### 审批决策")

                col_approve, col_reject = st.columns(2)

                with col_approve:
                    approval_notes = st.text_area(
                        "审批备注",
                        key=f"notes_{row['approval_id']}",
                        placeholder="添加任何意见或条件...",
                        height=100
                    )

                    if st.button(
                        "✅ 审批策略",
                        key=f"approve_{row['approval_id']}",
                        type="primary",
                        use_container_width=True
                    ):
                        approve_strategy(row['approval_id'], approval_notes)
                        st.success(f"✅ {row['strategy_name']} 已审批！")
                        st.rerun()

                with col_reject:
                    rejection_reason = st.text_area(
                        "拒绝原因",
                        key=f"reason_{row['approval_id']}",
                        placeholder="为什么拒绝这个策略？",
                        height=100
                    )

                    if st.button(
                        "❌ 拒绝策略",
                        key=f"reject_{row['approval_id']}",
                        use_container_width=True
                    ):
                        if not rejection_reason:
                            st.error("请提供拒绝原因")
                        else:
                            reject_strategy(row['approval_id'], rejection_reason)
                            st.warning(f"❌ {row['strategy_name']} 已拒绝")
                            st.rerun()

with tab2:
    st.header("已审批策略")

    approved = get_approved_strategies()

    if approved.empty:
        st.info("还没有已审批的策略。审批一些回测以开始使用！")
    else:
        st.markdown(f"**{len(approved)} 个策略**目前已审批用于实盘")

        # Display as table
        display_df = approved[[
            'strategy_name', 'strategy_version', 'total_return',
            'sharpe_ratio', 'approval_time', 'approver_id', 'notes'
        ]].copy()

        display_df['total_return'] = (display_df['total_return'] * 100).round(2).astype(str) + '%'
        display_df['sharpe_ratio'] = display_df['sharpe_ratio'].round(2)

        display_df.columns = [
            '策略', '版本', '收益率', 'Sharpe',
            '审批时间', '审批人', '备注'
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

# Sidebar: Approval Guidelines
with st.sidebar:
    st.header("📋 审批指南")

    st.markdown("""
    ### 建议标准

    **✅ 审批条件:**
    - Sharpe 比率 > 1.0
    - 最大回撤 < 30%
    - 胜率 > 45%
    - 回测周期 ≥ 3 年
    - 测试覆盖不同市场条件

    **❌ 拒绝条件:**
    - Sharpe 比率 < 0.5
    - 最大回撤 > 40%
    - 胜率 < 30%
    - 回测周期不足
    - 疑似过拟合

    **⚠️ 仔细审查:**
    - 高波动性策略
    - 交易次数少的策略（<20次）
    - 仅在单一股票上测试的策略
    """)

    st.divider()

    st.markdown("""
    ### 审批影响

    审批后，策略将被用于:
    - ✅ 自动化每日调度器
    - ✅ 实盘推荐生成
    - ✅ 仪表盘显示

    未审批策略仍可:
    - 📊 手动回测
    - 🔍 研究分析
    - 🚫 但不能用于实盘推荐
    """)
