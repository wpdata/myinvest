"""
策略推荐 (Strategy Recommendations) - T060

Multi-timeframe strategy analysis with timeframe selector.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from investlib_data.resample import resample_to_weekly, align_timeframes
from investlib_quant.indicators.weekly_indicators import (
    calculate_weekly_ma,
    detect_weekly_trend
)
from investlib_quant.strategies.multi_timeframe import MultiTimeframeStrategy

# Import symbol selector
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.symbol_selector import render_symbol_selector_compact

# Page config
st.set_page_config(
    page_title="策略推荐",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 多时间框架策略分析")
st.caption("周线趋势确认 + 日线精确入场 = 高质量交易信号")

# 添加策略说明
with st.expander("📖 策略说明", expanded=False):
    st.markdown("""
### 核心理念
多时间框架策略结合**周线趋势**和**日线信号**，过滤虚假突破，提高交易胜率。

### 信号逻辑
- **周线分析**：判断主趋势（上升/下降/横盘）
- **日线分析**：寻找精确入场点（MA5上穿MA20）
- **信号融合**：只在趋势一致时发出交易信号

### 优势
- ✅ 避免在下降趋势中抄底
- ✅ 避免在上升趋势中过早卖出
- ✅ 提高信号可靠性
- ✅ 减少频繁交易

### 使用建议
1. 在"策略回测"页面可以进行历史验证
2. 可调整MA参数适应不同市场
3. 建议结合其他策略综合判断
    """)

# Sidebar info
st.sidebar.info("""
💡 **提示**
此页面是多时间框架策略的**分析仪表盘**。

想要回测验证？
→ 前往"策略回测"页面
→ 选择"多时间框架策略"
""")

st.sidebar.divider()

# Sidebar: Timeframe selector
st.sidebar.header("⏰ 时间框架选择")

timeframe_option = st.sidebar.radio(
    "分析周期",
    options=["日线 (Daily)", "周线 (Weekly)", "日线+周线组合 (Multi-TF)"],
    index=2,
    help="选择分析时间框架"
)

st.sidebar.divider()

# Sidebar: Symbol input
st.sidebar.header("📊 标的选择")
symbol_input = render_symbol_selector_compact(
    default_value="600519.SH",
    key="recommendations_symbol"
)

analyze_button = st.sidebar.button("🔍 分析", type="primary", use_container_width=True)

st.sidebar.divider()

# Main content
if analyze_button:
    with st.spinner(f"正在分析 {symbol_input}..."):
        # Generate sample data (in production, fetch from database)
        # For demo purposes, create synthetic data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)  # 2 years
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        np.random.seed(42)
        trend = np.linspace(1800, 2000, len(dates))
        noise = np.random.normal(0, 25, len(dates))
        close_prices = trend + noise

        daily_data = pd.DataFrame({
            'timestamp': dates,
            'open': close_prices + np.random.normal(0, 5, len(dates)),
            'high': close_prices + np.abs(np.random.normal(12, 5, len(dates))),
            'low': close_prices - np.abs(np.random.normal(12, 5, len(dates))),
            'close': close_prices,
            'volume': np.random.randint(100000, 500000, len(dates))
        })

        # Resample to weekly
        weekly_data = resample_to_weekly(daily_data)

        # Display timeframe information
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("数据区间", f"{(end_date - start_date).days} 天")
        with col2:
            st.metric("日线数据", f"{len(daily_data)} 条")
        with col3:
            st.metric("周线数据", f"{len(weekly_data)} 条")

        st.divider()

        # Analyze based on selected timeframe
        if "日线" in timeframe_option and "组合" not in timeframe_option:
            # Daily only analysis
            st.header("📅 日线分析")

            latest_price = daily_data.iloc[-1]['close']
            ma5 = daily_data['close'].rolling(5).mean().iloc[-1]
            ma20 = daily_data['close'].rolling(20).mean().iloc[-1]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("当前价格", f"¥{latest_price:.2f}")
            with col2:
                ma5_trend = "🟢 向上" if ma5 > ma20 else "🔴 向下"
                st.metric("5日均线", f"¥{ma5:.2f}", delta=ma5_trend)
            with col3:
                st.metric("20日均线", f"¥{ma20:.2f}")

            # Daily signal
            if ma5 > ma20 and latest_price > ma5:
                st.success("✅ **日线信号: 买入 (BUY)**")
                st.info("📝 推理: 5日均线在20日均线上方，且价格在5日均线上方，趋势向上")
            elif ma5 < ma20 and latest_price < ma5:
                st.warning("⚠️ **日线信号: 卖出 (SELL)**")
                st.info("📝 推理: 5日均线在20日均线下方，且价格在5日均线下方，趋势向下")
            else:
                st.info("⏸️ **日线信号: 观望 (HOLD)**")

        elif "周线" in timeframe_option and "组合" not in timeframe_option:
            # Weekly only analysis
            st.header("📊 周线分析")

            weekly_trend = detect_weekly_trend(weekly_data, ma_short=10, ma_long=20)
            latest_weekly_price = weekly_data.iloc[-1]['close']
            weekly_ma10 = calculate_weekly_ma(weekly_data, 10).iloc[-1]
            weekly_ma20 = calculate_weekly_ma(weekly_data, 20).iloc[-1]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("周线收盘", f"¥{latest_weekly_price:.2f}")
            with col2:
                st.metric("10周均线", f"¥{weekly_ma10:.2f}")
            with col3:
                st.metric("20周均线", f"¥{weekly_ma20:.2f}")

            # Weekly trend card
            if weekly_trend == 'up':
                st.success("📈 **周线趋势: ↑ 上升趋势 (Uptrend)**")
                st.info("📝 推理: 10周均线 > 20周均线，且价格在10周均线上方")
            elif weekly_trend == 'down':
                st.error("📉 **周线趋势: ↓ 下降趋势 (Downtrend)**")
                st.info("📝 推理: 10周均线 < 20周均线，且价格在10周均线下方")
            else:
                st.warning("📊 **周线趋势: → 横盘整理 (Sideways)**")
                st.info("📝 推理: 均线交织，趋势不明确")

        else:
            # Multi-timeframe analysis
            st.header("🔀 多时间框架组合分析")

            # Align timeframes
            aligned_data = align_timeframes(weekly_data, daily_data)

            # Weekly trend analysis
            st.subheader("📊 周线趋势分析")

            weekly_trend = detect_weekly_trend(weekly_data, ma_short=10, ma_long=20)

            col1, col2, col3 = st.columns(3)

            with col1:
                trend_emoji = {
                    'up': '📈 ↑',
                    'down': '📉 ↓',
                    'sideways': '📊 →'
                }[weekly_trend]
                trend_text = {
                    'up': '上升趋势',
                    'down': '下降趋势',
                    'sideways': '横盘整理'
                }[weekly_trend]
                st.metric("周线趋势", f"{trend_emoji} {trend_text}")

            with col2:
                latest_weekly = weekly_data.iloc[-1]['close']
                st.metric("周线收盘", f"¥{latest_weekly:.2f}")

            with col3:
                weekly_ma10 = calculate_weekly_ma(weekly_data, 10).iloc[-1]
                st.metric("10周均线", f"¥{weekly_ma10:.2f}")

            st.divider()

            # Multi-timeframe signal
            st.subheader("🎯 综合交易信号")

            strategy = MultiTimeframeStrategy(
                name="日线+周线组合",
                weekly_ma_short=10,
                weekly_ma_long=20,
                daily_ma_fast=5,
                daily_ma_slow=20
            )

            signal = strategy.generate_signal(aligned_data)

            if signal:
                action = signal['action']
                confidence = signal['confidence']

                if action == 'BUY':
                    st.success(f"✅ **交易信号: 买入 (BUY)** | 信心: {confidence}")
                elif action == 'SELL':
                    st.error(f"⚠️ **交易信号: 卖出 (SELL)** | 信心: {confidence}")

                # Signal details
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("入场价", f"¥{signal['entry_price']:.2f}")
                with col2:
                    st.metric("止损", f"¥{signal['stop_loss']:.2f}")
                with col3:
                    st.metric("止盈", f"¥{signal['take_profit']:.2f}")
                with col4:
                    st.metric("建议仓位", f"{signal['position_size_pct']*100:.0f}%")

                # Reasoning
                st.info("📝 **信号推理:**")
                reasoning = signal.get('reasoning', {})
                for key, value in reasoning.items():
                    st.write(f"- **{key}**: {value}")

            else:
                st.info("⏸️ **交易信号: 观望 (HOLD)**")
                st.write("📝 周线趋势与日线信号未对齐，或无明确日线信号")

                # Show misalignment info
                st.write(f"- 周线趋势: {weekly_trend}")
                st.write("- 日线信号: 无明确突破信号")

else:
    # Initial state
    st.info("👈 请在左侧选择时间框架和股票代码，然后点击'分析'按钮")

    # Feature introduction
    st.markdown("""
    ### 🎯 功能说明

    **多时间框架分析** 帮助您从不同时间维度分析市场趋势：

    1. **日线 (Daily)**: 适合短期交易，捕捉日内波动
       - 使用5日、20日均线
       - 快速响应市场变化

    2. **周线 (Weekly)**: 适合中长期投资，把握主趋势
       - 使用10周、20周均线
       - 过滤日线噪音，识别主趋势

    3. **日线+周线组合 (Multi-TF)**: 最佳实践
       - 周线确认主趋势
       - 日线寻找入场时机
       - 只在两者一致时交易
       - 提高胜率，降低假信号

    ### 📊 分析指标

    - ✅ 移动均线趋势
    - ✅ 均线金叉/死叉
    - ✅ 价格相对位置
    - ✅ 多周期共振确认

    ### 🎓 使用建议

    1. **新手**: 建议使用"日线+周线组合"，减少假信号
    2. **短线交易**: 使用"日线"分析，快速进出
    3. **长线投资**: 使用"周线"分析，把握大趋势
    """)

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
