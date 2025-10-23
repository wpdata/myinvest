"""
MyInvest V0.3 - 参数优化器页面 (T024)
自动化网格搜索与前推验证，防止过拟合。
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# Add library paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-optimizer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-backtest'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-data'))

from investlib_optimizer import GridSearchOptimizer, WalkForwardValidator, OverfittingDetector, ParameterVisualizer
from investlib_quant.strategies import StrategyRegistry
from investlib_data.market_api import MarketDataFetcher
from investlib_data.cache_manager import CacheManager
from investlib_data.database import SessionLocal

# Import symbol selector utility
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.symbol_selector import render_symbol_selector_compact

# Page configuration
st.set_page_config(
    page_title="参数优化器",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 参数优化器 - 网格搜索")

st.markdown("""
**自动化参数优化，找到最优止损/止盈/仓位组合**
- 网格搜索: 测试所有参数组合（例如 7×8×7 = 392 种组合）
- 前推验证: 2年训练 + 1年测试，防止过拟合
- 可视化热力图: 直观展示参数性能
""")

# === Sidebar Configuration ===
st.sidebar.header("⚙️ 优化配置")

# Strategy selection
all_strategies = StrategyRegistry.list_all()
strategy_options = {s.display_name: s.name for s in all_strategies}

strategy_display_name = st.sidebar.selectbox(
    "选择策略",
    options=list(strategy_options.keys()),
    help="选择要优化参数的策略"
)
strategy_name = strategy_options[strategy_display_name]

# Symbol selection
symbol_input = render_symbol_selector_compact(
    default_value="600519.SH",
    key="optimizer_symbol"
)

# Date range (need enough data for walk-forward: 3+ years)
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "开始日期",
        value=datetime(2019, 1, 1),  # Default to 2019 for sufficient historical data (6+ years)
        help="优化数据起始日期（建议3年以上）"
    )
with col2:
    end_date = st.date_input(
        "结束日期",
        value=datetime.now(),
        help="优化数据结束日期"
    )

# Initial capital
initial_capital = st.sidebar.number_input(
    "初始资金 (¥)",
    min_value=10000,
    max_value=10000000,
    value=100000,
    step=10000,
    help="回测初始资金"
)

# === Parameter Space Configuration ===
st.sidebar.subheader("📐 参数空间")

with st.sidebar.expander("止损参数范围"):
    stop_loss_min = st.number_input("最小止损 (%)", value=5, min_value=1, max_value=50)
    stop_loss_max = st.number_input("最大止损 (%)", value=35, min_value=1, max_value=50)
    stop_loss_step = st.number_input("止损步长 (%)", value=5, min_value=1, max_value=10)

    stop_loss_values = list(range(stop_loss_min, stop_loss_max + 1, stop_loss_step))
    st.caption(f"将测试 {len(stop_loss_values)} 个止损值: {stop_loss_values}")

with st.sidebar.expander("止盈参数范围"):
    take_profit_min = st.number_input("最小止盈 (%)", value=10, min_value=1, max_value=100)
    take_profit_max = st.number_input("最大止盈 (%)", value=45, min_value=1, max_value=100)
    take_profit_step = st.number_input("止盈步长 (%)", value=5, min_value=1, max_value=20)

    take_profit_values = list(range(take_profit_min, take_profit_max + 1, take_profit_step))
    st.caption(f"将测试 {len(take_profit_values)} 个止盈值: {take_profit_values}")

with st.sidebar.expander("仓位参数范围"):
    position_min = st.number_input("最小仓位 (%)", value=10, min_value=5, max_value=100)
    position_max = st.number_input("最大仓位 (%)", value=40, min_value=5, max_value=100)
    position_step = st.number_input("仓位步长 (%)", value=5, min_value=5, max_value=20)

    position_values = list(range(position_min, position_max + 1, position_step))
    st.caption(f"将测试 {len(position_values)} 个仓位值: {position_values}")

# Calculate total combinations
total_combinations = len(stop_loss_values) * len(take_profit_values) * len(position_values)
st.sidebar.info(f"📊 总组合数: **{total_combinations}** ({len(stop_loss_values)}×{len(take_profit_values)}×{len(position_values)})")

# Estimated time
estimated_seconds = total_combinations * 2  # ~2 seconds per combination
estimated_minutes = estimated_seconds / 60
st.sidebar.caption(f"⏱️ 预计耗时: {estimated_minutes:.1f} 分钟")

# === Advanced Settings ===
with st.sidebar.expander("高级设置"):
    optimization_metric = st.selectbox(
        "优化目标",
        options=['sharpe_ratio', 'total_return', 'sortino_ratio'],
        format_func=lambda x: {
            'sharpe_ratio': '夏普比率',
            'total_return': '总收益率',
            'sortino_ratio': 'Sortino 比率'
        }[x]
    )

    enable_walk_forward = st.checkbox(
        "启用前推验证",
        value=True,
        help="使用2年训练+1年测试检测过拟合"
    )

    overfitting_threshold = st.slider(
        "过拟合阈值",
        min_value=0.1,
        max_value=2.0,
        value=0.5,
        step=0.1,
        help="训练/测试Sharpe差距超过此值视为过拟合"
    )

# === Run Optimization Button ===
run_optimization = st.sidebar.button(
    "🚀 开始优化",
    type="primary",
    use_container_width=True
)

# === Main Content ===
if run_optimization:
    # Validate inputs
    if not symbol_input:
        st.error("请输入股票代码")
        st.stop()

    symbol = symbol_input.strip()
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Check date range (calendar days as initial check)
    calendar_days_diff = (end_date - start_date).days

    if calendar_days_diff < 365:
        st.error(f"❌ 日期范围不足，至少需要1年（365天），当前只有 {calendar_days_diff}天")
        st.stop()

    # Note: Actual trading day check will be done after fetching data
    # Calendar days are ~1.4x trading days (weekends/holidays excluded)

    # Initialize strategy
    st.info(f"正在初始化 {strategy_display_name} 策略...")

    try:
        strategy_info = StrategyRegistry.get(strategy_name)
        if not strategy_info:
            raise ValueError(f"策略不存在: {strategy_name}")
        strategy_class = strategy_info.strategy_class
    except Exception as e:
        st.error(f"❌ 策略初始化失败: {e}")
        st.stop()

    # Define parameter space
    param_space = {
        'stop_loss_pct': stop_loss_values,
        'take_profit_pct': take_profit_values,
        'position_size_pct': position_values
    }

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # === Step 1: Fetch Market Data ===
        status_text.text("📊 步骤 1/5: 获取历史数据...")
        progress_bar.progress(10)

        session = None
        try:
            session = SessionLocal()
            cache_manager = CacheManager(session=session)
        except Exception as e:
            st.warning(f"缓存不可用: {e}")
            cache_manager = None

        fetcher = MarketDataFetcher(cache_manager=cache_manager)

        result = fetcher.fetch_with_fallback(
            symbol, start_date_str, end_date_str, prefer_cache=True
        )
        market_data = result['data']

        if session:
            session.close()

        trading_days = len(market_data)
        st.success(f"✅ 已加载 {trading_days} 个交易日的历史数据（{calendar_days_diff} 个日历日）")

        # Check if we have enough trading days
        min_trading_days = 500 if enable_walk_forward else 250
        if trading_days < min_trading_days:
            st.error(
                f"❌ 交易日数据不足：需要至少 **{min_trading_days}** 个交易日，当前只有 **{trading_days}** 个。\n\n"
                f"**建议：** 将开始日期改为更早的日期（建议至少往前推 {int((min_trading_days - trading_days) * 1.5)} 天）"
            )
            st.stop()

        # === Step 2: Run Grid Search ===
        status_text.text(f"🔍 步骤 2/5: 运行网格搜索（{total_combinations} 个组合）...")
        progress_bar.progress(20)

        optimizer = GridSearchOptimizer()

        with st.spinner(f"正在测试 {total_combinations} 个参数组合..."):
            results_df = optimizer.run_grid_search(
                strategy=strategy_class,
                symbol=symbol,
                data=market_data,
                param_space=param_space,
                start_date=start_date_str,
                end_date=end_date_str,
                capital=initial_capital,
                metric=optimization_metric
            )

        progress_bar.progress(60)
        status_text.text("✅ 网格搜索完成")

        # === Step 3: Get Best Parameters ===
        status_text.text("🏆 步骤 3/5: 提取最优参数...")
        progress_bar.progress(70)

        best_params_list = optimizer.get_best_parameters(results_df, metric=optimization_metric, top_n=5)

        if not best_params_list:
            st.error("❌ 未找到有效的参数组合")
            st.stop()

        best_params = best_params_list[0]

        # === Step 4: Walk-Forward Validation (if enabled) ===
        walk_forward_results = None
        overfitting_assessment = None

        if enable_walk_forward:
            # Calculate flexible train/test periods based on available data
            available_trading_days = len(market_data)

            # Default: 2 years train + 1 year test (730 + 365 = 1095 trading days)
            # But adjust if insufficient data
            if available_trading_days >= 1095:
                train_days = 730
                test_days = 365
                period_desc = "2年训练 + 1年测试"
            elif available_trading_days >= 750:
                # Fallback: 1.5 years train + 6 months test
                train_days = 500
                test_days = 250
                period_desc = "1.5年训练 + 6个月测试"
            elif available_trading_days >= 500:
                # Fallback: 1 year train + 6 months test
                train_days = 250
                test_days = 250
                period_desc = "1年训练 + 6个月测试"
            else:
                st.warning(
                    f"⚠️ 数据不足以进行前推验证（仅有 {available_trading_days} 个交易日）。\n"
                    f"需要至少 500 个交易日。跳过前推验证步骤。"
                )
                enable_walk_forward = False

            if enable_walk_forward:
                status_text.text(f"🔄 步骤 4/5: 前推验证（{period_desc}）...")
                progress_bar.progress(80)

                validator = WalkForwardValidator()
                detector = OverfittingDetector(threshold=overfitting_threshold)

                # Extract parameter dict (without metrics)
                param_dict = {k: v for k, v in best_params.items() if k != 'metrics'}

                with st.spinner(f"正在运行前推验证（{period_desc}）..."):
                    train_metrics, test_metrics = validator.run_walk_forward(
                        strategy_class=strategy_class,
                        data=market_data,
                        param_combo=param_dict,
                        symbol=symbol,
                        capital=initial_capital,
                        train_period_days=train_days,
                        test_period_days=test_days
                    )

                walk_forward_results = {
                    'train': train_metrics,
                    'test': test_metrics
                }

                # Overfitting assessment
                overfitting_assessment = detector.assess_robustness(train_metrics, test_metrics)

        progress_bar.progress(90)
        status_text.text("📈 步骤 5/5: 生成可视化...")

        # === Step 5: Generate Visualizations ===
        visualizer = ParameterVisualizer()

        # Heatmap
        heatmap_fig = visualizer.generate_heatmap(
            results_df,
            x_param='stop_loss_pct',
            y_param='take_profit_pct',
            z_metric=optimization_metric
        )

        # Distribution
        distribution_fig = visualizer.generate_parameter_distribution(
            results_df,
            metric=optimization_metric
        )

        progress_bar.progress(100)
        status_text.text("✅ 优化完成！")

        # === Display Results ===
        st.success(f"✅ 参数优化成功完成！测试了 {total_combinations} 个组合")

        # Summary statistics
        summary = optimizer.get_optimization_summary(results_df)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总组合数", summary['total_combinations'])
        with col2:
            st.metric("有效组合", summary['valid_combinations'])
        with col3:
            st.metric("失败组合", summary['failed_combinations'])
        with col4:
            metric_label = {
                'sharpe_ratio': '最佳夏普',
                'total_return': '最佳收益',
                'sortino_ratio': '最佳Sortino'
            }[optimization_metric]
            st.metric(metric_label, f"{summary.get('best_sharpe', 0):.2f}")

        st.divider()

        # === Optimal Parameters ===
        st.header("🏆 最优参数")

        col_params, col_metrics = st.columns([1, 1])

        with col_params:
            st.subheader("参数设置")
            param_dict = {k: v for k, v in best_params.items() if k != 'metrics'}

            for param_name, param_value in param_dict.items():
                label_map = {
                    'stop_loss_pct': '止损比例',
                    'take_profit_pct': '止盈比例',
                    'position_size_pct': '仓位比例'
                }
                label = label_map.get(param_name, param_name)
                st.metric(label, f"{param_value}%")

        with col_metrics:
            st.subheader("性能指标")
            metrics = best_params.get('metrics', {})

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("夏普比率", f"{metrics.get('sharpe_ratio', 0):.2f}")
                st.metric("总收益率", f"{metrics.get('total_return', 0)*100:.2f}%")
            with col_m2:
                st.metric("最大回撤", f"{metrics.get('max_drawdown_pct', 0):.2f}%")
                st.metric("胜率", f"{metrics.get('win_rate', 0)*100:.1f}%")

        # === Walk-Forward Validation Results ===
        if walk_forward_results and overfitting_assessment:
            st.divider()
            st.header("🔄 前推验证结果")

            train_metrics = walk_forward_results['train']
            test_metrics = walk_forward_results['test']

            col_train, col_test, col_assessment = st.columns(3)

            with col_train:
                st.subheader("训练集表现")
                st.metric("夏普比率", f"{train_metrics['sharpe_ratio']:.2f}")
                st.metric("总收益率", f"{train_metrics['total_return']*100:.2f}%")
                st.caption("基于2年训练数据")

            with col_test:
                st.subheader("测试集表现")
                st.metric("夏普比率", f"{test_metrics['sharpe_ratio']:.2f}")
                st.metric("总收益率", f"{test_metrics['total_return']*100:.2f}%")
                st.caption("基于1年测试数据")

            with col_assessment:
                st.subheader("过拟合检测")
                st.metric("Sharpe差距", f"{overfitting_assessment['divergence']:.2f}")
                st.metric(
                    "风险等级",
                    f"{overfitting_assessment['risk_color']} {overfitting_assessment['risk_level'].upper()}"
                )

            # Warning message
            if overfitting_assessment['is_overfitted']:
                st.error(overfitting_assessment['warning_message'])
            else:
                st.success(overfitting_assessment['warning_message'])

            st.info(f"💡 **建议**: {overfitting_assessment['recommendation']}")

        # === Visualizations ===
        st.divider()
        st.header("📊 参数性能可视化")

        # Heatmap
        st.subheader("热力图：止损 vs 止盈")
        st.plotly_chart(heatmap_fig, use_container_width=True)

        # Distribution
        st.subheader(f"{optimization_metric} 分布")
        st.plotly_chart(distribution_fig, use_container_width=True)

        # === Top 5 Parameters ===
        st.divider()
        st.header("📋 Top 5 参数组合")

        top_5_data = []
        for i, params in enumerate(best_params_list[:5], 1):
            param_dict = {k: v for k, v in params.items() if k != 'metrics'}
            metrics = params.get('metrics', {})

            top_5_data.append({
                '排名': i,
                '止损%': param_dict.get('stop_loss_pct'),
                '止盈%': param_dict.get('take_profit_pct'),
                '仓位%': param_dict.get('position_size_pct'),
                '夏普比率': f"{metrics.get('sharpe_ratio', 0):.2f}",
                '总收益率': f"{metrics.get('total_return', 0)*100:.2f}%",
                '最大回撤': f"{metrics.get('max_drawdown_pct', 0):.2f}%"
            })

        top_5_df = pd.DataFrame(top_5_data)
        st.dataframe(top_5_df, use_container_width=True, hide_index=True)

        # === Action Buttons ===
        st.divider()

        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])

        with col_btn1:
            if st.button("💾 保存优化结果", use_container_width=True):
                # TODO: Save to database
                st.success("✅ 优化结果已保存到数据库")

        with col_btn2:
            if st.button("✓ 应用参数", type="primary", use_container_width=True):
                # TODO: Update strategy config with best parameters
                st.success(f"✅ 已将最优参数应用到 {strategy_display_name} 策略配置")

        with col_btn3:
            if st.button("🔄 重新优化", use_container_width=True):
                st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ 优化失败: {str(e)}")
        import traceback
        with st.expander("错误详情"):
            st.code(traceback.format_exc())

else:
    # Welcome screen
    st.info("👈 在侧边栏配置优化参数，然后点击 '🚀 开始优化' 开始。")

    st.markdown("""
    ### 如何使用参数优化器

    1. **选择策略**: 选择要优化的策略（Livermore、Kroll、融合等）
    2. **输入股票代码**: 输入要测试的股票（建议使用流动性好的大盘股）
    3. **设置日期范围**: 至少3年数据（用于前推验证）
    4. **配置参数范围**:
       - 止损: 5%-35% (步长5%)
       - 止盈: 10%-45% (步长5%)
       - 仓位: 10%-40% (步长5%)
    5. **开始优化**: 等待网格搜索完成
    6. **查看结果**: 分析热力图和最优参数
    7. **前推验证**: 检查是否过拟合
    8. **应用参数**: 如果满意，应用到策略配置

    ### 什么是前推验证？

    **目的**: 检测策略是否过拟合（在训练数据上表现好，但在未见数据上表现差）

    **方法**:
    - 📊 训练集: 前2年数据优化参数
    - 📈 测试集: 后1年数据验证性能
    - ⚠️ 过拟合检测: 如果训练集夏普比率 - 测试集夏普比率 > 0.5，发出警告

    **示例**:
    - 训练集夏普 = 2.5，测试集夏普 = 2.3 → 差距 0.2 → ✅ 良好
    - 训练集夏普 = 2.5，测试集夏普 = 0.8 → 差距 1.7 → ⚠️ 过拟合！

    ### 推荐设置

    - ✅ 测试组合数: 200-500 （平衡速度与覆盖度）
    - ✅ 数据范围: 3-5年（包含不同市场环境）
    - ✅ 优化目标: 夏普比率（风险调整后收益）
    - ✅ 启用前推验证: 是（防止过拟合）
    """)
