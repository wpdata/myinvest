"""市场轮动策略页面 - 监控大盘并提供轮动建议。"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from investlib_quant.strategies.market_rotation import MarketRotationStrategy
from investlib_data.market_api import MarketDataFetcher
from investlib_data.cache_manager import CacheManager
from investlib_data.database import SessionLocal

st.set_page_config(page_title="轮动策略 Rotation", page_icon="🔄", layout="wide")

st.title("🔄 市场轮动策略 - 大盘恐慌买入")

# 策略说明
with st.expander("💡 策略说明", expanded=True):
    st.markdown("""
    ### 策略核心逻辑

    1. **监控指标**: 实时监控沪深300指数的涨跌幅
    2. **买入触发**: 当大盘连续2个交易日跌幅 ≤ -1.5% 时触发
    3. **买入标的**: 全仓买入中证1000 ETF (159845.SZ)
    4. **持有周期**: 持有20个交易日后自动卖出
    5. **默认持仓**: 其余时间持有国债ETF (511010.SH)

    ### 策略优势

    - 🎯 **逆向投资**: 在市场恐慌时捕捉超卖机会
    - 📈 **高弹性**: 中证1000代表中小盘，反弹力度强
    - 🛡️ **防御性**: 平时持有国债，稳定收益
    - ⏰ **纪律性**: 固定持仓周期，避免情绪化操作

    ### 风险提示

    - ⚠️ 市场可能持续下跌，需要设置止损
    - ⚠️ 中证1000波动较大，需要控制仓位
    - ⚠️ 策略仅供参考，不构成投资建议
    """)

# 策略配置
st.sidebar.header("⚙️ 策略参数配置")

index_symbol = st.sidebar.selectbox(
    "监控指数",
    options=["000300.SH", "000001.SH", "000905.SH"],
    format_func=lambda x: {
        "000300.SH": "沪深300",
        "000001.SH": "上证指数",
        "000905.SH": "中证500"
    }.get(x, x),
    index=0
)

decline_threshold = st.sidebar.slider(
    "跌幅阈值 (%)",
    min_value=-3.0,
    max_value=-0.5,
    value=-1.5,
    step=0.1,
    help="单日跌幅达到此阈值才触发信号"
)

consecutive_days = st.sidebar.slider(
    "连续天数",
    min_value=1,
    max_value=5,
    value=2,
    help="连续多少天达到跌幅阈值"
)

holding_days = st.sidebar.slider(
    "持有天数",
    min_value=5,
    max_value=60,
    value=20,
    help="买入后持有多少个交易日"
)

stop_loss_pct = st.sidebar.slider(
    "止损百分比 (%)",
    min_value=0.0,
    max_value=10.0,
    value=5.0,
    step=0.5,
    help="可选止损，0表示不设止损"
)

# 创建策略实例
strategy = MarketRotationStrategy(
    index_symbol=index_symbol,
    decline_threshold=decline_threshold,
    consecutive_days=consecutive_days,
    etf_symbol="159845.SZ",
    bond_symbol="511010.SH",
    holding_days=holding_days,
    stop_loss_pct=stop_loss_pct if stop_loss_pct > 0 else None
)

st.sidebar.success("策略配置已更新")

# 主界面
tab1, tab2, tab3 = st.tabs(["📊 实时监控", "📈 历史分析", "🎮 策略模拟"])

# Tab 1: 实时监控
with tab1:
    st.header("📊 大盘实时监控")

    # 获取最近的大盘数据
    if st.button("🔄 刷新数据", type="primary"):
        with st.spinner("正在获取最新数据..."):
            try:
                session = SessionLocal()
                cache_manager = CacheManager(session=session)
                fetcher = MarketDataFetcher(cache_manager=cache_manager)

                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

                # 获取指数数据
                index_result = fetcher.fetch_with_fallback(
                    index_symbol,
                    start_date,
                    end_date
                )
                index_data = index_result['data']

                # 计算涨跌幅
                index_data['pct_change'] = index_data['close'].pct_change() * 100

                # 显示最近5天数据
                st.subheader(f"最近5个交易日 - {index_symbol}")
                recent_data = index_data.tail(5).copy()
                recent_data['日期'] = pd.to_datetime(recent_data['timestamp']).dt.strftime('%Y-%m-%d')
                recent_data['收盘价'] = recent_data['close'].round(2)
                recent_data['涨跌幅(%)'] = recent_data['pct_change'].round(2)

                display_df = recent_data[['日期', '收盘价', '涨跌幅(%)']].reset_index(drop=True)

                # 高亮显示跌幅超过阈值的行
                def highlight_decline(row):
                    if row['涨跌幅(%)'] <= decline_threshold:
                        return ['background-color: #ffcccc'] * len(row)
                    elif row['涨跌幅(%)'] < 0:
                        return ['background-color: #ffe6cc'] * len(row)
                    elif row['涨跌幅(%)'] > 0:
                        return ['background-color: #ccffcc'] * len(row)
                    return [''] * len(row)

                styled_df = display_df.style.apply(highlight_decline, axis=1)
                st.dataframe(styled_df, use_container_width=True)

                # 检查触发条件
                st.divider()
                st.subheader("🚨 信号检测")

                # 检查最近N天是否满足条件
                recent_n_days = index_data.tail(consecutive_days)
                decline_days = recent_n_days[recent_n_days['pct_change'] <= decline_threshold]

                col1, col2, col3 = st.columns(3)

                with col1:
                    latest_change = index_data.iloc[-1]['pct_change']
                    st.metric(
                        "今日涨跌幅",
                        f"{latest_change:.2f}%",
                        delta=None
                    )

                with col2:
                    st.metric(
                        f"近{consecutive_days}日下跌天数",
                        f"{len(decline_days)}天",
                        delta=None
                    )

                with col3:
                    trigger = len(decline_days) >= consecutive_days
                    if trigger:
                        st.success("✅ 触发买入信号！")
                    else:
                        st.info("⏳ 未触发信号")

                # 详细分析
                if trigger:
                    st.success(f"""
                    ### 🎯 买入信号已触发！

                    **触发条件**: 近{consecutive_days}个交易日连续下跌超过{decline_threshold}%

                    **建议操作**:
                    1. 卖出当前持有的国债ETF (511010.SH)
                    2. 全仓买入中证1000 ETF (159845.SZ)
                    3. 设置{holding_days}个交易日后自动提醒
                    4. 设置{stop_loss_pct}%止损（如果跌破立即卖出）

                    **预期持有**: {holding_days}个交易日（约{holding_days//5}周）
                    """)
                else:
                    st.info(f"""
                    ### 📊 当前状态

                    近{consecutive_days}天内有{len(decline_days)}天跌幅超过{decline_threshold}%，
                    需要{consecutive_days}天才能触发买入信号。

                    **建议操作**: 继续持有国债ETF (511010.SH)
                    """)

                session.close()

            except Exception as e:
                st.error(f"数据获取失败: {e}")
                import traceback
                st.code(traceback.format_exc())

# Tab 2: 历史分析
with tab2:
    st.header("📈 历史触发记录分析")

    st.markdown("""
    分析历史上满足触发条件的时点，以及买入后的表现。
    """)

    # 选择分析时间范围
    col1, col2 = st.columns(2)
    with col1:
        analysis_start = st.date_input(
            "分析开始日期",
            value=datetime.now() - timedelta(days=730),  # 默认2年
            key="analysis_start"
        )
    with col2:
        analysis_end = st.date_input(
            "分析结束日期",
            value=datetime.now(),
            key="analysis_end"
        )

    if st.button("🔍 开始分析", type="primary", key="analyze_triggers"):
        with st.spinner("正在分析历史触发点..."):
            try:
                session = SessionLocal()
                cache_manager = CacheManager(session=session)
                fetcher = MarketDataFetcher(cache_manager=cache_manager)

                # 获取指数历史数据
                index_result = fetcher.fetch_with_fallback(
                    index_symbol,
                    analysis_start.strftime('%Y-%m-%d'),
                    analysis_end.strftime('%Y-%m-%d')
                )
                index_data = index_result['data']
                index_data['pct_change'] = index_data['close'].pct_change() * 100

                # 获取ETF历史数据
                etf_result = fetcher.fetch_with_fallback(
                    strategy.etf_symbol,
                    analysis_start.strftime('%Y-%m-%d'),
                    analysis_end.strftime('%Y-%m-%d')
                )
                etf_data = etf_result['data']

                # 获取国债ETF历史数据（用于对比）
                bond_result = fetcher.fetch_with_fallback(
                    strategy.bond_symbol,
                    analysis_start.strftime('%Y-%m-%d'),
                    analysis_end.strftime('%Y-%m-%d')
                )
                bond_data = bond_result['data']

                session.close()

                # 寻找触发点
                trigger_dates = []
                for i in range(consecutive_days, len(index_data)):
                    # 检查最近连续N天是否都满足跌幅条件
                    # 需要N+1天数据来计算N天的涨跌幅
                    recent_days = index_data.iloc[i-consecutive_days:i+1]

                    # 取最后N天的涨跌幅
                    last_n_changes = recent_days['pct_change'].iloc[-consecutive_days:]

                    # 检查是否所有天都满足跌幅阈值（与策略逻辑一致）
                    all_decline = all(last_n_changes <= decline_threshold)

                    if all_decline:
                        trigger_date = index_data.iloc[i]['timestamp']

                        # 确保 trigger_date 是 datetime 类型
                        if isinstance(trigger_date, str):
                            trigger_date = pd.to_datetime(trigger_date)

                        # 避免重复触发（间隔至少holding_days天）
                        if not trigger_dates:
                            trigger_dates.append({
                                'date': trigger_date,
                                'index_close': index_data.iloc[i]['close'],
                                'decline_changes': last_n_changes.tolist()
                            })
                        else:
                            last_trigger_date = trigger_dates[-1]['date']
                            if isinstance(last_trigger_date, str):
                                last_trigger_date = pd.to_datetime(last_trigger_date)

                            if (trigger_date - last_trigger_date).days >= holding_days:
                                trigger_dates.append({
                                    'date': trigger_date,
                                    'index_close': index_data.iloc[i]['close'],
                                    'decline_changes': last_n_changes.tolist()
                                })

                st.success(f"✅ 找到 {len(trigger_dates)} 个触发点")

                if trigger_dates:
                    # 分析每个触发点的后续表现
                    st.subheader("📊 触发点详细分析")

                    analysis_results = []
                    for trigger in trigger_dates:
                        trigger_date = trigger['date']

                        # 确保 trigger_date 是 datetime 类型
                        if isinstance(trigger_date, str):
                            trigger_date = pd.to_datetime(trigger_date)

                        # 确保 etf_data 和 bond_data 的 timestamp 列也是 datetime 类型
                        if not pd.api.types.is_datetime64_any_dtype(etf_data['timestamp']):
                            etf_data['timestamp'] = pd.to_datetime(etf_data['timestamp'])
                        if not pd.api.types.is_datetime64_any_dtype(bond_data['timestamp']):
                            bond_data['timestamp'] = pd.to_datetime(bond_data['timestamp'])

                        # 找到触发日期在ETF数据中的位置
                        etf_trigger_idx = etf_data[etf_data['timestamp'] >= trigger_date].index
                        if len(etf_trigger_idx) == 0:
                            continue

                        etf_trigger_idx = etf_trigger_idx[0]

                        # 买入价格（下一个交易日开盘价近似）
                        if etf_trigger_idx + 1 < len(etf_data):
                            entry_price = etf_data.iloc[etf_trigger_idx + 1]['open']
                        else:
                            continue

                        # 持有期收益
                        exit_idx = min(etf_trigger_idx + holding_days, len(etf_data) - 1)
                        exit_price = etf_data.iloc[exit_idx]['close']
                        holding_return = (exit_price - entry_price) / entry_price * 100

                        # 最大回撤
                        holding_period = etf_data.iloc[etf_trigger_idx+1:exit_idx+1]
                        if len(holding_period) > 0:
                            max_price = holding_period['close'].max()
                            min_price = holding_period['close'].min()
                            max_drawdown = (min_price - entry_price) / entry_price * 100
                        else:
                            max_drawdown = 0

                        # 计算同期国债收益（对比基准）
                        bond_trigger_idx = bond_data[bond_data['timestamp'] >= trigger_date].index
                        if len(bond_trigger_idx) > 0:
                            bond_trigger_idx = bond_trigger_idx[0]
                            if bond_trigger_idx + 1 < len(bond_data):
                                bond_entry_price = bond_data.iloc[bond_trigger_idx + 1]['open']
                                bond_exit_idx = min(bond_trigger_idx + holding_days, len(bond_data) - 1)
                                bond_exit_price = bond_data.iloc[bond_exit_idx]['close']
                                bond_return = (bond_exit_price - bond_entry_price) / bond_entry_price * 100
                                excess_return = holding_return - bond_return  # 超额收益
                            else:
                                bond_return = 0
                                excess_return = holding_return
                        else:
                            bond_return = 0
                            excess_return = holding_return

                        # 格式化日期显示
                        if isinstance(trigger_date, pd.Timestamp):
                            date_str = trigger_date.strftime('%Y-%m-%d')
                        else:
                            date_str = str(trigger_date)

                        analysis_results.append({
                            '触发日期': date_str,
                            '指数收盘': f"{trigger['index_close']:.2f}",
                            '买入价': f"¥{entry_price:.3f}",
                            '卖出价': f"¥{exit_price:.3f}",
                            'ETF收益率': f"{holding_return:.2f}%",
                            '国债收益率': f"{bond_return:.2f}%",
                            '超额收益': f"{excess_return:.2f}%",
                            '最大回撤': f"{max_drawdown:.2f}%",
                            '持有天数': min(holding_days, exit_idx - etf_trigger_idx)
                        })

                    # 显示分析表格
                    results_df = pd.DataFrame(analysis_results)
                    st.dataframe(results_df, use_container_width=True)

                    # 统计摘要
                    st.subheader("📈 统计摘要")
                    col1, col2, col3, col4, col5 = st.columns(5)

                    etf_returns = [float(r['ETF收益率'].rstrip('%')) for r in analysis_results]
                    excess_returns = [float(r['超额收益'].rstrip('%')) for r in analysis_results]
                    win_count = sum(1 for r in etf_returns if r > 0)
                    win_rate = win_count / len(etf_returns) * 100 if etf_returns else 0

                    # 超额收益胜率（相对国债）
                    excess_win_count = sum(1 for r in excess_returns if r > 0)
                    excess_win_rate = excess_win_count / len(excess_returns) * 100 if excess_returns else 0

                    with col1:
                        st.metric("触发次数", len(trigger_dates))

                    with col2:
                        st.metric("绝对胜率", f"{win_rate:.1f}%",
                                 help="ETF收益率>0的比例")

                    with col3:
                        st.metric("相对胜率", f"{excess_win_rate:.1f}%",
                                 help="相对国债的超额收益>0的比例")

                    with col4:
                        avg_etf_return = sum(etf_returns) / len(etf_returns) if etf_returns else 0
                        st.metric("平均ETF收益", f"{avg_etf_return:.2f}%")

                    with col5:
                        avg_excess = sum(excess_returns) / len(excess_returns) if excess_returns else 0
                        st.metric("平均超额收益", f"{avg_excess:.2f}%",
                                 help="相对国债的平均超额收益")

                    # 收益分布图
                    import plotly.graph_objects as go
                    from plotly.subplots import make_subplots

                    fig = make_subplots(
                        rows=1, cols=2,
                        subplot_titles=("ETF收益率分布", "超额收益分布（vs 国债）")
                    )

                    # ETF收益率分布
                    fig.add_trace(
                        go.Histogram(
                            x=etf_returns,
                            nbinsx=20,
                            name='ETF收益',
                            marker_color='#2E86AB'
                        ),
                        row=1, col=1
                    )

                    # 超额收益分布
                    fig.add_trace(
                        go.Histogram(
                            x=excess_returns,
                            nbinsx=20,
                            name='超额收益',
                            marker_color='#06A77D'
                        ),
                        row=1, col=2
                    )

                    fig.update_xaxes(title_text="收益率 (%)", row=1, col=1)
                    fig.update_xaxes(title_text="超额收益 (%)", row=1, col=2)
                    fig.update_yaxes(title_text="频数", row=1, col=1)
                    fig.update_yaxes(title_text="频数", row=1, col=2)

                    fig.update_layout(
                        height=400,
                        showlegend=False
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # 下载分析结果
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 下载分析结果 (CSV)",
                        data=csv,
                        file_name=f"trigger_analysis_{analysis_start}_{analysis_end}.csv",
                        mime="text/csv"
                    )

                else:
                    st.info(f"在 {analysis_start} 至 {analysis_end} 期间未发现触发信号")

            except Exception as e:
                st.error(f"❌ 分析失败: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Tab 3: 策略模拟
with tab3:
    st.header("🎮 策略模拟器")

    st.markdown("""
    ### 模拟回测

    选择回测时间范围，查看策略的历史表现。
    """)

    col1, col2 = st.columns(2)

    with col1:
        start_date_input = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365)
        )

    with col2:
        end_date_input = st.date_input(
            "结束日期",
            value=datetime.now()
        )

    initial_capital = st.number_input(
        "初始资金 (元)",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=10000
    )

    if st.button("开始回测", type="primary"):
        with st.spinner("正在运行回测，请稍候..."):
            try:
                from investlib_backtest.engine.rotation_backtest import RotationBacktestRunner
                import plotly.graph_objects as go

                # 准备资产符号
                asset_symbols = {
                    'index': index_symbol,
                    'etf': strategy.etf_symbol,
                    'bond': strategy.bond_symbol
                }

                # 创建回测引擎
                runner = RotationBacktestRunner(
                    initial_capital=initial_capital,
                    commission_rate=0.0003,
                    slippage_rate=0.001
                )

                # 运行回测
                results = runner.run(
                    strategy=strategy,
                    asset_symbols=asset_symbols,
                    start_date=start_date_input.strftime('%Y-%m-%d'),
                    end_date=end_date_input.strftime('%Y-%m-%d'),
                    capital=initial_capital
                )

                # 显示回测结果
                st.success("✅ 回测完成！")

                # 调试信息
                with st.expander("🔍 调试信息", expanded=False):
                    st.write(f"**信号生成数量**: {results['signals_generated']}")
                    st.write(f"**切换执行数量**: {results['total_switches']}")
                    st.write(f"**数据源**: {results['data_sources']}")

                    if results['switch_log']:
                        st.write(f"**切换记录数**: {len(results['switch_log'])}")
                        st.write("**首次切换**:")
                        st.json(results['switch_log'][0] if results['switch_log'] else {})
                    else:
                        st.warning("⚠️ 未发生任何品种切换")
                        st.write("可能的原因：")
                        st.write("1. 回测期间大盘未满足连续下跌条件")
                        st.write("2. 触发条件设置过于严格")
                        st.write(f"3. 当前参数：连续{consecutive_days}日跌幅≤{decline_threshold}%")

                # 关键指标
                st.subheader("📊 关键指标")

                # 计算统计数据
                equity_curve = results['equity_curve']
                equity_df = pd.DataFrame(equity_curve) if equity_curve else pd.DataFrame()

                # 最大回撤
                max_drawdown = 0
                if not equity_df.empty:
                    peak = equity_df['value'].expanding(min_periods=1).max()
                    drawdown = (equity_df['value'] - peak) / peak
                    max_drawdown = drawdown.min() * 100

                # 年化收益率
                total_days = (pd.to_datetime(end_date_input) - pd.to_datetime(start_date_input)).days
                years = total_days / 365.0
                annual_return = (((results['final_capital'] / results['initial_capital']) ** (1 / years)) - 1) * 100 if years > 0 else 0

                # 夏普比率（简化版，假设无风险利率3%）
                sharpe_ratio = 0
                if not equity_df.empty and len(equity_df) > 1:
                    equity_df['daily_return'] = equity_df['value'].pct_change()
                    daily_returns = equity_df['daily_return'].dropna()
                    if len(daily_returns) > 0 and daily_returns.std() > 0:
                        risk_free_rate = 0.03 / 252  # 日无风险利率
                        excess_returns = daily_returns - risk_free_rate
                        sharpe_ratio = (excess_returns.mean() / daily_returns.std()) * (252 ** 0.5)

                # 胜率（基于切换）
                win_rate = 0
                if results['switch_log'] and len(results['switch_log']) > 1:
                    # 计算每次切换的盈亏
                    switches = results['switch_log']
                    wins = 0
                    total_trades = 0
                    for i in range(1, len(switches)):
                        if switches[i]['value'] > switches[i-1]['value']:
                            wins += 1
                        total_trades += 1
                    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

                # 第一行指标
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "总收益率",
                        f"{results['total_return']*100:.2f}%"
                    )

                with col2:
                    st.metric(
                        "年化收益率",
                        f"{annual_return:.2f}%"
                    )

                with col3:
                    st.metric(
                        "最大回撤",
                        f"{max_drawdown:.2f}%"
                    )

                with col4:
                    st.metric(
                        "夏普比率",
                        f"{sharpe_ratio:.2f}"
                    )

                # 第二行指标
                col5, col6, col7, col8 = st.columns(4)

                with col5:
                    st.metric(
                        "最终资金",
                        f"¥{results['final_capital']:,.2f}"
                    )

                with col6:
                    profit = results['final_capital'] - results['initial_capital']
                    st.metric(
                        "总盈亏",
                        f"¥{profit:,.2f}"
                    )

                with col7:
                    st.metric(
                        "切换次数",
                        f"{results['total_switches']}次"
                    )

                with col8:
                    st.metric(
                        "胜率",
                        f"{win_rate:.1f}%",
                        help="基于相邻切换之间的价值变化"
                    )

                # 净值曲线
                st.subheader("📈 净值曲线")
                if results['equity_curve']:
                    equity_df = pd.DataFrame(results['equity_curve'])
                    equity_df['date'] = pd.to_datetime(equity_df['date'])
                    equity_df['return_pct'] = (equity_df['value'] / initial_capital - 1) * 100

                    fig = go.Figure()

                    # 净值曲线
                    fig.add_trace(go.Scatter(
                        x=equity_df['date'],
                        y=equity_df['value'],
                        mode='lines',
                        name='组合净值',
                        line=dict(color='#2E86AB', width=2)
                    ))

                    # 初始资金参考线
                    fig.add_hline(
                        y=initial_capital,
                        line_dash="dash",
                        line_color="gray",
                        annotation_text="初始资金",
                        annotation_position="right"
                    )

                    fig.update_layout(
                        title="组合净值曲线",
                        xaxis_title="日期",
                        yaxis_title="净值 (元)",
                        hovermode='x unified',
                        height=400
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # 收益率曲线
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        x=equity_df['date'],
                        y=equity_df['return_pct'],
                        mode='lines',
                        name='累计收益率',
                        line=dict(color='#06A77D', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(6, 167, 125, 0.1)'
                    ))

                    fig2.update_layout(
                        title="累计收益率曲线",
                        xaxis_title="日期",
                        yaxis_title="收益率 (%)",
                        hovermode='x unified',
                        height=300
                    )

                    st.plotly_chart(fig2, use_container_width=True)

                # 品种切换记录
                st.subheader("🔄 品种切换记录")
                if results['switch_log']:
                    switch_df = pd.DataFrame(results['switch_log'])
                    switch_df['timestamp'] = pd.to_datetime(switch_df['timestamp'])

                    # 显示表格
                    display_df = switch_df[['timestamp', 'from_symbol', 'to_symbol', 'price', 'shares', 'value']].copy()
                    display_df.columns = ['日期', '从品种', '到品种', '价格', '份额', '价值']
                    display_df['价格'] = display_df['价格'].apply(lambda x: f"¥{x:.3f}")
                    display_df['份额'] = display_df['份额'].apply(lambda x: f"{x:.2f}")
                    display_df['价值'] = display_df['价值'].apply(lambda x: f"¥{x:,.2f}")

                    st.dataframe(display_df, use_container_width=True)

                    # 下载切换记录
                    csv = switch_df.to_csv(index=False)
                    st.download_button(
                        label="📥 下载切换记录 (CSV)",
                        data=csv,
                        file_name=f"rotation_switches_{start_date_input}_{end_date_input}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("回测期间未发生品种切换")

                # 持仓分布
                st.subheader("📊 持仓时间分布")
                if results['position_history']:
                    position_df = pd.DataFrame(results['position_history'])
                    position_counts = position_df['symbol'].value_counts()

                    fig3 = go.Figure(data=[go.Pie(
                        labels=position_counts.index,
                        values=position_counts.values,
                        hole=0.3
                    )])

                    fig3.update_layout(
                        title="各品种持仓天数占比",
                        height=400
                    )

                    st.plotly_chart(fig3, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 回测失败: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# 页脚
st.divider()
st.markdown("""
### 📚 相关资源

- 📖 [策略详细文档](../STRATEGY_GUIDE.md)
- 💻 [示例代码](../examples/rotation_strategy_example.py)
- 🔧 [策略管理页面](./9_strategies.py)

**免责声明**: 本策略仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
""")
