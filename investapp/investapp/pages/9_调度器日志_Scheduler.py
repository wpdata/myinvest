"""调度器日志页面 - 监控自动任务执行 (T086).

显示自动化每日调度器的执行历史。
显示成功/失败状态、处理的股票代码和错误详情。
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add scheduler module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from investapp.scheduler.daily_tasks import DailyScheduler

st.set_page_config(page_title="调度器日志 Scheduler", page_icon="📅", layout="wide")

st.title("📅 自动调度器日志")

st.markdown("""
监控自动化每日推荐生成的执行历史。
调度器在每个交易日的 **北京时间 08:30** 运行。
""")

# Database connection - use environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////Users/pw/ai/myinvest/data/myinvest.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "")

def get_scheduler_logs(days: int = 30, status_filter: str = None):
    """获取调度器执行日志。"""
    conn = sqlite3.connect(DB_PATH)

    where_clause = f"WHERE execution_time >= datetime('now', '-{days} days')"
    if status_filter and status_filter != "全部":
        status_map = {"成功": "SUCCESS", "失败": "FAILURE", "部分成功": "PARTIAL"}
        db_status = status_map.get(status_filter, status_filter)
        where_clause += f" AND status = '{db_status}'"

    query = f"""
    SELECT
        id,
        execution_time,
        status,
        symbols_processed,
        recommendations_generated,
        data_source,
        error_message,
        duration_seconds,
        created_at
    FROM scheduler_log
    {where_clause}
    ORDER BY execution_time DESC
    LIMIT 100
    """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        df = pd.DataFrame()  # Empty if table doesn't exist yet
    finally:
        conn.close()

    return df

# Sidebar: Filters
st.sidebar.header("🔍 筛选")

days_filter = st.sidebar.selectbox(
    "时间段",
    [7, 14, 30, 60, 90],
    index=2,
    format_func=lambda x: f"最近 {x} 天"
)

status_filter = st.sidebar.selectbox(
    "状态",
    ["全部", "成功", "失败", "部分成功"]
)

# Manual trigger button
st.sidebar.divider()
st.sidebar.header("🔧 手动控制")

if st.sidebar.button("▶️ 触发手动运行", type="primary", use_container_width=True):
    with st.spinner("正在执行调度任务..."):
        try:
            # Initialize scheduler
            scheduler = DailyScheduler(db_path=DB_PATH)

            # Show start message
            st.sidebar.info("🚀 调度任务已启动...")

            # Run the daily tasks
            scheduler.run_daily_tasks()

            # Success message
            st.sidebar.success("✅ 调度任务执行完成！页面将自动刷新以显示最新结果。")

            # Trigger page rerun to show new logs
            st.rerun()

        except Exception as e:
            st.sidebar.error(f"❌ 调度任务执行失败: {str(e)}")
            st.sidebar.exception(e)

# Get logs
logs = get_scheduler_logs(days_filter, status_filter)

# Display summary metrics
if not logs.empty:
    col1, col2, col3, col4 = st.columns(4)

    total_runs = len(logs)
    successful_runs = len(logs[logs['status'] == 'SUCCESS'])
    failed_runs = len(logs[logs['status'] == 'FAILURE'])
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

    with col1:
        st.metric("总执行次数", total_runs)

    with col2:
        st.metric(
            "成功率",
            f"{success_rate:.1f}%",
            delta=f"{successful_runs}/{total_runs}"
        )

    with col3:
        st.metric(
            "失败次数",
            failed_runs,
            delta_color="inverse"
        )

    with col4:
        avg_duration = logs['duration_seconds'].mean() if 'duration_seconds' in logs.columns else 0
        st.metric("平均耗时", f"{avg_duration:.1f}秒")

    st.divider()

# Display log table
st.header("📋 执行历史")

if logs.empty:
    st.info(f"最近 {days_filter} 天内没有找到调度器执行记录。")
    st.markdown("""
    **可能的原因:**
    - 调度器尚未启用
    - 所选时间段内没有执行记录
    - 数据库表未初始化

    **启用调度器:** 在 `.env` 文件中设置 `SCHEDULER_ENABLED=true`
    """)
else:
    # Format for display
    display_df = logs.copy()

    # Add status badges
    def status_badge(status):
        if status == 'SUCCESS':
            return '🟢 成功'
        elif status == 'FAILURE':
            return '🔴 失败'
        elif status == 'PARTIAL':
            return '🟡 部分成功'
        return status

    display_df['状态'] = display_df['status'].apply(status_badge)

    # Format columns
    display_cols = {
        'execution_time': '执行时间',
        '状态': '状态',
        'symbols_processed': '股票数',
        'recommendations_generated': '推荐数',
        'data_source': '数据源',
        'duration_seconds': '耗时 (秒)'
    }

    st.dataframe(
        display_df[list(display_cols.keys())].rename(columns=display_cols),
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Detailed view for each execution
    st.divider()
    st.header("🔍 执行详情")

    selected_idx = st.selectbox(
        "选择要查看详情的执行:",
        range(len(logs)),
        format_func=lambda i: f"{logs.iloc[i]['execution_time']} - {status_badge(logs.iloc[i]['status'])}"
    )

    if selected_idx is not None:
        selected_log = logs.iloc[selected_idx]

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 执行摘要")
            st.markdown(f"""
            - **执行时间:** {selected_log['execution_time']}
            - **状态:** {status_badge(selected_log['status'])}
            - **耗时:** {selected_log['duration_seconds']:.2f} 秒
            - **数据源:** {selected_log['data_source']}
            - **处理股票数:** {selected_log['symbols_processed']}
            - **生成推荐数:** {selected_log['recommendations_generated']}
            """)

            # Error details if any
            if pd.notna(selected_log['error_message']) and selected_log['error_message']:
                st.error(f"""
                **错误信息:**
                ```
                {selected_log['error_message']}
                ```
                """)

        with col2:
            st.markdown("### 快速统计")

            # Calculate efficiency
            if selected_log['symbols_processed'] > 0:
                recs_per_symbol = selected_log['recommendations_generated'] / selected_log['symbols_processed']
                st.metric("推荐/股票", f"{recs_per_symbol:.1f}")

            if selected_log['duration_seconds'] > 0:
                symbols_per_sec = selected_log['symbols_processed'] / selected_log['duration_seconds']
                st.metric("股票/秒", f"{symbols_per_sec:.2f}")

# Health check section
st.divider()
st.header("🏥 调度器健康状况")

if not logs.empty:
    # Check last execution time
    latest_execution = pd.to_datetime(logs.iloc[0]['execution_time'])
    time_since_last = datetime.now() - latest_execution
    hours_since = time_since_last.total_seconds() / 3600

    if hours_since < 24:
        st.success(f"✅ 调度器健康。上次执行在 {hours_since:.1f} 小时前。")
    elif hours_since < 48:
        st.warning(f"⚠️ 调度器可能过期。上次执行在 {hours_since:.1f} 小时前（>24小时）。")
    else:
        st.error(f"❌ 调度器似乎已停止。上次执行在 {hours_since:.1f} 小时前。")

    # Success rate trend
    if len(logs) >= 5:
        recent_5 = logs.head(5)
        recent_success_rate = len(recent_5[recent_5['status'] == 'SUCCESS']) / len(recent_5) * 100

        if recent_success_rate >= 80:
            st.success(f"✅ 最近成功率: {recent_success_rate:.0f}% (最近 5 次)")
        elif recent_success_rate >= 60:
            st.warning(f"⚠️ 最近成功率: {recent_success_rate:.0f}% (最近 5 次)")
        else:
            st.error(f"❌ 最近成功率偏低: {recent_success_rate:.0f}% (最近 5 次)")
else:
    st.warning("⚠️ 没有执行历史记录。调度器可能未运行。")

# Sidebar: Scheduler Configuration
with st.sidebar:
    st.divider()
    st.header("⚙️ 配置")

    st.markdown("""
    **计划:** 每个交易日 08:30 运行

    **任务:**
    1. 获取监视列表股票的收盘数据
    2. 生成 Kroll 推荐
    3. 生成 Livermore 推荐
    4. 生成融合推荐
    5. 保存到数据库（标记为未读）

    **数据源:** Efinance（主要）→ AKShare（备用）

    **重试逻辑:** 指数退避重试 3 次
    """)
