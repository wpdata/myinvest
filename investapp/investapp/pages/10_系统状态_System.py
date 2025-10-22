"""系统状态与监控页面 (T081).

显示系统健康状态、API 状态、数据库指标和调度器健康状况。
MyInvest V0.2 所有组件的实时监控。
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add library paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-data'))

st.set_page_config(page_title="系统状态 System", page_icon="🖥️", layout="wide")

st.title("🖥️ 系统状态与监控")

st.markdown("""
MyInvest 系统组件、数据源和自动化健康状况的实时监控。
""")

# Database path
DB_PATH = "/Users/pw/ai/myinvest/data/myinvest.db"

# === Section 1: Overall System Health ===
st.header("🏥 系统健康总览")

col1, col2, col3, col4 = st.columns(4)

# Check database connectivity
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    conn.close()
    db_status = "🟢 已连接"
    db_healthy = True
except Exception as e:
    db_status = f"🔴 错误: {str(e)}"
    table_count = 0
    db_healthy = False

with col1:
    st.metric("数据库", db_status)
    st.caption(f"{table_count} 个表")

# Check data APIs
try:
    from investlib_data.market_api import MarketDataFetcher

    fetcher = MarketDataFetcher()
    # Quick test fetch (will use cache if available)
    test_result = fetcher.fetch_with_fallback(
        "600519.SH",
        (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d')
    )
    api_status = "🟢 可用"
    api_source = test_result['metadata']['api_source']
    api_healthy = True
except Exception as e:
    api_status = "🔴 错误"
    api_source = str(e)[:30]
    api_healthy = False

with col2:
    st.metric("市场数据 API", api_status)
    st.caption(api_source)

# Check scheduler status
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT execution_time, status
        FROM scheduler_log
        ORDER BY execution_time DESC
        LIMIT 1
    """)
    last_run = cursor.fetchone()
    conn.close()

    if last_run:
        last_time = pd.to_datetime(last_run[0])
        hours_ago = (datetime.now() - last_time).total_seconds() / 3600

        if hours_ago < 24:
            scheduler_status = "🟢 运行中"
            scheduler_healthy = True
        else:
            scheduler_status = f"🟡 过期 ({hours_ago:.0f}小时)"
            scheduler_healthy = False
    else:
        scheduler_status = "⚪ 未启动"
        scheduler_healthy = False
except:
    scheduler_status = "🔴 错误"
    scheduler_healthy = False

with col3:
    st.metric("调度器", scheduler_status)
    if last_run:
        st.caption(f"上次: {last_run[1]}")

# Overall system health
overall_health = "🟢 健康" if (db_healthy and api_healthy) else \
                 "🟡 降级" if db_healthy else "🔴 严重"

with col4:
    st.metric("总体状态", overall_health)
    healthy_components = sum([db_healthy, api_healthy, scheduler_healthy])
    st.caption(f"{healthy_components}/3 组件正常")

# === Section 2: Database Statistics ===
st.divider()
st.header("💾 数据库统计")

if db_healthy:
    conn = sqlite3.connect(DB_PATH)

    col1, col2, col3 = st.columns(3)

    # Count recommendations
    try:
        rec_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM investment_recommendations",
            conn
        ).iloc[0]['count']
    except:
        rec_count = 0

    with col1:
        st.metric("投资推荐总数", f"{rec_count:,}")

    # Count backtest results
    try:
        backtest_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM backtest_results",
            conn
        ).iloc[0]['count']
    except:
        backtest_count = 0

    with col2:
        st.metric("回测结果", backtest_count)

    # Count approved strategies
    try:
        approved_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM strategy_approval WHERE status='APPROVED'",
            conn
        ).iloc[0]['count']
    except:
        approved_count = 0

    with col3:
        st.metric("已批准策略", approved_count)

    # Table sizes
    with st.expander("📊 表详情"):
        try:
            tables = [
                'investment_recommendations',
                'investment_records',
                'market_data',
                'backtest_results',
                'strategy_approval',
                'scheduler_log',
                'strategy_config'
            ]

            table_stats = []
            for table in tables:
                try:
                    count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
                    table_stats.append({'表名': table, '行数': count})
                except:
                    table_stats.append({'表名': table, '行数': 'N/A'})

            st.dataframe(pd.DataFrame(table_stats), hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"加载表统计信息出错: {e}")

    conn.close()

# === Section 3: API Status ===
st.divider()
st.header("🌐 市场数据 API 状态")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Efinance API (主要)")
    try:
        from investlib_data.market_api import EfinanceClient

        client = EfinanceClient()
        # Test connection - Efinance uses different date format
        test_data = client.fetch_daily_data("600519", "20241201", "20241210")

        if test_data is not None and not test_data.empty:
            st.success("✅ Efinance API 运行正常")
            st.metric("测试查询结果", f"{len(test_data)} 条记录")
        else:
            st.warning("⚠️ Efinance 返回空数据")
    except Exception as e:
        st.error(f"❌ Efinance API 错误: {str(e)[:100]}")

with col2:
    st.subheader("AKShare API (备用)")
    try:
        from investlib_data.market_api import AKShareClient

        client = AKShareClient()
        test_data = client.fetch_daily_data("600519", "20241201", "20241210")

        if test_data is not None and not test_data.empty:
            st.success("✅ AKShare API 运行正常")
            st.metric("测试查询结果", f"{len(test_data)} 条记录")
        else:
            st.warning("⚠️ AKShare 返回空数据")
    except Exception as e:
        st.error(f"❌ AKShare API 错误: {str(e)[:100]}")

# === Section 4: Strategy Status ===
st.divider()
st.header("🎯 策略状态")

# 从策略注册中心获取所有策略
try:
    from investlib_quant.strategies import StrategyRegistry
    all_strategies = StrategyRegistry.list_all()

    # 动态创建列
    if len(all_strategies) > 0:
        cols = st.columns(min(len(all_strategies), 3))

        for idx, strategy_info in enumerate(all_strategies[:3]):
            with cols[idx]:
                st.subheader(strategy_info.display_name)
                try:
                    strategy = StrategyRegistry.create(strategy_info.name)
                    st.success("✅ 加载成功")
                    st.caption(f"代码: {strategy_info.name}")
                    st.caption(f"风险: {strategy_info.risk_level}")
                except Exception as e:
                    st.error(f"❌ 错误: {str(e)[:50]}")
    else:
        st.warning("未找到已注册的策略")

except Exception as e:
    st.error(f"❌ 策略注册中心错误: {str(e)}")

# === Section 5: Recent Activity ===
st.divider()
st.header("📊 最近活动（最近 7 天）")

if db_healthy:
    conn = sqlite3.connect(DB_PATH)

    try:
        # Recent recommendations
        recent_recs = pd.read_sql_query("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM investment_recommendations
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, conn)

        if not recent_recs.empty:
            st.subheader("生成的推荐")
            st.bar_chart(recent_recs.set_index('date'))
        else:
            st.info("过去 7 天内没有生成推荐")

    except Exception as e:
        st.warning(f"无法加载最近活动: {e}")

    try:
        # Scheduler execution history
        scheduler_history = pd.read_sql_query("""
            SELECT
                DATE(execution_time) as date,
                status,
                COUNT(*) as count
            FROM scheduler_log
            WHERE execution_time >= datetime('now', '-7 days')
            GROUP BY DATE(execution_time), status
            ORDER BY date DESC
        """, conn)

        if not scheduler_history.empty:
            st.subheader("调度器执行")
            pivot_table = scheduler_history.pivot(index='date', columns='status', values='count').fillna(0)
            st.bar_chart(pivot_table)
        else:
            st.info("过去 7 天内没有调度器执行记录")

    except Exception as e:
        pass  # Table may not exist yet

    conn.close()

# === Section 6: System Configuration ===
with st.expander("⚙️ 系统配置"):
    st.markdown("""
    ### 环境
    - **数据库:** SQLite (myinvest.db)
    - **缓存:** Redis (如已配置)
    - **调度器:** APScheduler (每日 08:30)

    ### 策略配置
    - **Livermore 权重:** 60%
    - **Kroll 权重:** 40%
    - **佣金率:** 0.03%
    - **滑点率:** 0.1%

    ### API 配置
    - **主要:** Efinance (免费，无需 token)
    - **备用:** AKShare
    - **重试次数:** 3
    - **缓存有效期:** 7 天
    """)

# Auto-refresh option
st.divider()
if st.checkbox("🔄 自动刷新（每 30 秒）"):
    import time
    time.sleep(30)
    st.rerun()
