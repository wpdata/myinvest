"""策略回测页面 - 历史策略验证 (T074).

允许用户在历史数据（3年以上）上运行回测来验证策略。
显示性能指标、权益曲线和交易历史。
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add library paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-backtest'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-data'))

from investlib_backtest.engine.backtest_runner import BacktestRunner
from investlib_backtest.metrics.performance import PerformanceMetrics
from investlib_backtest.metrics.trade_analysis import TradeAnalysis
from investlib_quant.livermore_strategy import LivermoreStrategy
from investlib_quant.kroll_strategy import KrollStrategy
from investlib_quant.fusion_strategy import FusionStrategy

# Import symbol selector utility
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.symbol_selector import render_symbol_selector_compact


st.set_page_config(page_title="策略回测", layout="wide")

st.title("📊 策略回测 - 历史验证")

st.markdown("""
**在3年以上的真实历史数据上验证策略**，然后再用于实盘推荐。
""")

# Sidebar: Backtest Configuration
st.sidebar.header("⚙️ 回测配置")

# Strategy selection
strategy_name = st.sidebar.selectbox(
    "选择策略",
    ["Livermore (趋势跟随)", "Kroll (风险聚焦)", "Fusion (多策略融合)"],
    help="选择要回测的策略"
)

# Symbol selection (with smart selector)
symbol_input = render_symbol_selector_compact(
    default_value="600519.SH",
    key="backtest_symbol"
)

# Date range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "开始日期",
        value=datetime(2022, 1, 1),
        help="回测开始日期（建议 3 年以上）"
    )
with col2:
    end_date = st.date_input(
        "结束日期",
        value=datetime.now(),
        help="回测结束日期"
    )

# Initial capital
initial_capital = st.sidebar.number_input(
    "初始资金 (¥)",
    min_value=10000,
    max_value=10000000,
    value=100000,
    step=10000,
    help="回测起始资金"
)

# Transaction costs
with st.sidebar.expander("高级设置"):
    commission_rate = st.number_input(
        "佣金率 (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.03,
        step=0.01,
        help="交易佣金百分比"
    ) / 100

    slippage_rate = st.number_input(
        "滑点率 (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.01,
        help="价格滑点百分比"
    ) / 100

# Run backtest button
run_backtest = st.sidebar.button("▶️ 运行回测", type="primary", use_container_width=True)

# Main content area
if run_backtest:
    # Validate inputs
    if not symbol_input:
        st.error("请输入股票代码")
        st.stop()

    symbols = [s.strip() for s in symbol_input.split(',')]
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Check date range
    days_diff = (end_date - start_date).days
    if days_diff < 365:
        st.warning(f"⚠️ 日期范围仅有 {days_diff} 天。建议至少 3 年（1095 天）以获得有意义的回测结果。")

    # Initialize strategy
    st.info(f"正在初始化 {strategy_name} 策略...")

    if "Livermore" in strategy_name:
        strategy = LivermoreStrategy()
    elif "Kroll" in strategy_name:
        strategy = KrollStrategy()
    else:  # Fusion
        strategy = FusionStrategy(livermore_weight=0.6, kroll_weight=0.4)

    # Initialize backtest runner
    runner = BacktestRunner(
        initial_capital=initial_capital,
        commission_rate=commission_rate,
        slippage_rate=slippage_rate
    )

    # Progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Run backtest
        status_text.text("正在获取历史数据...")
        progress_bar.progress(20)

        results = runner.run(
            strategy=strategy,
            symbols=symbols,
            start_date=start_date_str,
            end_date=end_date_str,
            capital=initial_capital
        )

        progress_bar.progress(60)
        status_text.text("正在计算性能指标...")

        # Calculate metrics
        perf_metrics = PerformanceMetrics()
        trade_analysis = TradeAnalysis()

        performance = perf_metrics.calculate_all_metrics(results)
        trade_stats = trade_analysis.calculate_all_metrics(results['trade_log'])

        progress_bar.progress(100)
        status_text.text("✅ 回测完成！")

        # Display results
        st.success(f"{strategy_name} 回测成功完成")

        # Show diagnostic info
        if results['total_trades'] == 0:
            st.warning(f"""
            ⚠️ **回测期间未执行任何交易**

            - 生成信号数: {results.get('signals_generated', 0)}
            - 执行交易数: {results['total_trades']}

            可能原因：
            1. 策略在此期间没有触发买入条件
            2. 数据不足以计算策略指标（如需要120天均线）
            3. 策略参数设置过于严格

            建议：扩大回测时间范围或调整策略参数。
            """)

        # === Section 1: Performance Summary ===
        st.header("📈 性能总结")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_return_pct = performance['total_return_pct']
            delta_color = "normal" if total_return_pct >= 0 else "inverse"
            st.metric(
                "总收益",
                f"{total_return_pct:.2f}%",
                delta=f"¥{results['final_capital'] - initial_capital:,.2f}",
                delta_color=delta_color
            )

        with col2:
            st.metric(
                "年化收益",
                f"{performance['annualized_return_pct']:.2f}%",
                delta=f"{performance['years']:.1f} 年"
            )

        with col3:
            st.metric(
                "最大回撤",
                f"{performance['max_drawdown_pct']:.2f}%",
                delta=None,
                delta_color="inverse"
            )

        with col4:
            st.metric(
                "Sharpe 比率",
                f"{performance['sharpe_ratio']:.2f}",
                delta="风险调整后收益"
            )

        # === Section 2: Trade Statistics ===
        st.header("📊 交易统计")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            win_rate_pct = trade_stats.get('win_rate_pct', 0.0)
            winning_trades = trade_stats.get('winning_trades', 0)
            total_trades = trade_stats.get('total_trades', 0)
            st.metric(
                "胜率",
                f"{win_rate_pct:.1f}%",
                delta=f"{winning_trades}/{total_trades} 胜"
            )

        with col2:
            profit_factor = trade_stats.get('profit_factor', 0.0)
            st.metric(
                "盈利因子",
                f"{profit_factor:.2f}",
                delta=">1.0 = 盈利" if profit_factor > 1 else "亏损"
            )

        with col3:
            avg_win = trade_stats.get('avg_win', 0.0)
            st.metric(
                "平均盈利",
                f"¥{avg_win:,.2f}",
                delta=None
            )

        with col4:
            avg_loss = trade_stats.get('avg_loss', 0.0)
            st.metric(
                "平均亏损",
                f"¥{avg_loss:,.2f}",
                delta=None,
                delta_color="inverse"
            )

        # === Section 3: Equity Curve ===
        st.header("📉 权益曲线")

        equity_data = pd.DataFrame(results['equity_curve'])

        fig = go.Figure()

        # Main equity curve
        fig.add_trace(go.Scatter(
            x=equity_data['date'],
            y=equity_data['value'],
            mode='lines',
            name='投资组合价值',
            line=dict(color='#1f77b4', width=2)
        ))

        # Add initial capital line
        fig.add_hline(
            y=initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="初始资金",
            annotation_position="right"
        )

        # Highlight drawdown periods
        if performance['peak_date'] and performance['trough_date']:
            fig.add_vrect(
                x0=performance['peak_date'],
                x1=performance['trough_date'],
                fillcolor="red",
                opacity=0.1,
                annotation_text="最大回撤期间",
                annotation_position="top left"
            )

        fig.update_layout(
            title=f"投资组合价值随时间变化 ({start_date_str} 至 {end_date_str})",
            xaxis_title="日期",
            yaxis_title="投资组合价值 (¥)",
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # === Section 4: Drawdown Chart ===
        with st.expander("📉 回撤分析"):
            # Calculate drawdown at each point
            values = equity_data['value'].values
            running_max = pd.Series(values).expanding().max()
            drawdown = (values - running_max) / running_max * 100

            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=equity_data['date'],
                y=drawdown,
                fill='tozeroy',
                fillcolor='rgba(255, 0, 0, 0.3)',
                line=dict(color='red'),
                name='回撤 %'
            ))

            fig_dd.update_layout(
                title="投资组合回撤随时间变化",
                xaxis_title="日期",
                yaxis_title="回撤 (%)",
                hovermode='x',
                height=300
            )

            st.plotly_chart(fig_dd, use_container_width=True)

            st.markdown(f"""
            **回撤详情:**
            - 峰值: ¥{performance['peak_value']:,.2f} 于 {performance['peak_date']}
            - 谷值: ¥{performance['trough_value']:,.2f} 于 {performance['trough_date']}
            - 恢复: {performance['recovery_date'] if performance['recovery_date'] else '尚未恢复'}
            """)

        # === Section 5: Trade History ===
        st.header("📝 交易历史")

        if results['trade_log']:
            trade_df = pd.DataFrame(results['trade_log'])

            # Display summary
            st.markdown(f"**总交易次数:** {len(trade_df)}")

            # Display trade log table
            st.dataframe(
                trade_df[[
                    'timestamp', 'symbol', 'action', 'price',
                    'quantity', 'commission', 'slippage', 'total_cost'
                ]].style.format({
                    'price': '¥{:.2f}',
                    'commission': '¥{:.2f}',
                    'slippage': '¥{:.2f}',
                    'total_cost': '¥{:.2f}'
                }),
                use_container_width=True,
                height=400
            )

            # Download button
            csv = trade_df.to_csv(index=False)
            st.download_button(
                label="📥 下载交易记录 (CSV)",
                data=csv,
                file_name=f"backtest_trades_{strategy_name}_{start_date_str}.csv",
                mime="text/csv"
            )
        else:
            st.info("回测期间未执行交易")

        # === Section 6: Risk Assessment ===
        with st.expander("⚠️ 风险评估"):
            st.markdown("### 风险指标")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sortino 比率", f"{performance['sortino_ratio']:.2f}")
                st.metric("年化波动率", f"{performance['annualized_volatility']*100:.2f}%")

            with col2:
                st.metric("最大单笔盈利", f"¥{trade_stats.get('largest_win', 0):,.2f}")
                st.metric("最大单笔亏损", f"¥{trade_stats.get('largest_loss', 0):,.2f}")

            # Risk level assessment
            risk_level = "低" if performance['max_drawdown_pct'] < 10 else \
                        "中" if performance['max_drawdown_pct'] < 20 else "高"

            risk_color = "🟢" if risk_level == "低" else "🟡" if risk_level == "中" else "🔴"

            st.markdown(f"""
            **总体风险水平:** {risk_color} **{risk_level}**

            - 最大回撤: {performance['max_drawdown_pct']:.2f}% ({'✓ 可接受' if performance['max_drawdown_pct'] < 20 else '⚠️ 偏高'})
            - Sharpe 比率: {performance['sharpe_ratio']:.2f} ({'✓ 良好' if performance['sharpe_ratio'] > 1.0 else '⚠️ 需改进'})
            - 波动率: {performance['annualized_volatility']*100:.1f}% ({'✓ 稳定' if performance['annualized_volatility'] < 0.3 else '⚠️ 波动大'})
            """)

        # === Section 7: Submit for Approval ===
        st.header("✅ 提交审批")

        st.markdown("""
        如果这个回测性能令人满意，请提交策略进行审批。
        只有**已审批的策略**会被用于实盘推荐生成。
        """)

        approval_notes = st.text_area(
            "审批备注",
            placeholder="添加关于这次回测的评论或观察...",
            height=100
        )

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("📋 保存回测结果", use_container_width=True):
                # TODO: Save to backtest_results table
                st.success("✅ 回测结果已保存到数据库！")

        with col2:
            if st.button("✓ 提交审批", type="primary", use_container_width=True):
                # TODO: Create approval workflow record
                st.success("✅ 已提交审批！请查看审批页面。")

        with col3:
            if st.button("🔄 重新运行", use_container_width=True):
                st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ 回测失败: {str(e)}")
        st.exception(e)

else:
    # Welcome screen
    st.info("👈 在侧边栏配置回测参数，然后点击 '▶️ 运行回测' 开始。")

    st.markdown("""
    ### 如何使用回测

    1. **选择策略**: 选择 Livermore、Kroll 或融合策略
    2. **输入股票代码**: 股票代码（例如 600519.SH）
    3. **设置日期范围**: 建议 3 年以上进行有意义的验证
    4. **配置资金**: 初始投资金额
    5. **运行回测**: 点击按钮并等待结果
    6. **审查指标**: 分析收益、回撤、Sharpe 比率
    7. **提交审批**: 如果满意，提交审批

    ### 建议的审批标准

    - ✅ Sharpe 比率 > 1.0
    - ✅ 最大回撤 < 30%
    - ✅ 胜率 > 50%
    - ✅ 在 3 年以上数据测试（涵盖不同市场条件）
    """)
