"""Streamlit page for market data visualization."""

import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from investlib_data.market_api import MarketDataFetcher
from investlib_data.symbol_validator import validate_symbol, get_symbol_info
from investapp.components.chart_renderer import render_kline_chart
from investapp.components.data_freshness import render_freshness_indicator
from investapp.utils.symbol_selector import render_symbol_selector_compact
import pandas as pd

st.set_page_config(page_title="市场数据 Market", page_icon="📈", layout="wide")

st.title("📈 市场数据查询")

# Symbol input section
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    symbol = render_symbol_selector_compact(
        default_value="600519.SH",
        key="market_symbol"
    )

with col2:
    timeframe = st.selectbox(
        "时间周期",
        ["daily", "weekly", "monthly"],
        format_func=lambda x: {"daily": "日线", "weekly": "周线", "monthly": "月线"}[x]
    )

with col3:
    fetch_button = st.button("🔍 查询数据", type="primary", use_container_width=True)

# Fetch data when button clicked or if data exists in session state for current symbol
if fetch_button or (f'market_data_{symbol}' in st.session_state):
    if fetch_button:
        # 验证股票代码
        is_valid, error_msg = validate_symbol(symbol)

        if not is_valid:
            st.error(error_msg)

            # 显示股票代码信息
            try:
                info = get_symbol_info(symbol)
                st.info(f"""
                **股票代码信息：**
                - 代码：{info['code']}
                - 交易所：{info['exchange_name']} ({info['exchange']})
                - 类型：{info['type_name']}
                - 是否支持：{'✅ 是' if info['supported'] else '❌ 否'}
                """)
            except:
                pass

            # 提供帮助信息
            with st.expander("📚 支持的代码类型"):
                st.markdown("""
                **当前支持的类型：**

                **股票：**
                - ✅ 上海A股：600xxx.SH（如 600519.SH - 贵州茅台）
                - ✅ 深圳主板：000xxx.SZ（如 000001.SZ - 平安银行）
                - ✅ 深圳中小板：002xxx.SZ（如 002415.SZ - 海康威视）
                - ✅ 创业板：300xxx.SZ（如 300750.SZ - 宁德时代）

                **ETF 基金：**
                - ✅ 上海ETF：50/51xxx.SH（如 510300.SH - 沪深300ETF, 510760.SH - 上证综指ETF）
                - ✅ 深圳ETF：15/16xxx.SZ（如 159915.SZ - 创业板ETF）

                **指数：**
                - ✅ 上海指数：000xxx.SH（如 000001.SH - 上证指数）
                - ✅ 深圳指数：399xxx.SZ（如 399001.SZ - 深证成指）

                **暂不支持：**
                - ❌ 港股、美股
                """)

            st.stop()

        with st.spinner(f"正在获取 {symbol} 的市场数据..."):
            try:
                # Initialize fetcher
                fetcher = MarketDataFetcher()

                # Fetch data (default: last 365 days)
                result = fetcher.fetch_with_fallback(symbol)

                # Store in session state
                st.session_state[f'market_data_{symbol}'] = result
                st.session_state['last_symbol'] = symbol

                st.success(f"✅ 成功获取 {len(result['data'])} 条数据记录")

            except Exception as e:
                st.error(f"❌ 数据获取失败: {str(e)}")
                st.info("💡 提示：请检查股票代码是否正确，或稍后重试")
                st.stop()

    # Load data from session state
    if f'market_data_{symbol}' in st.session_state:
        result = st.session_state[f'market_data_{symbol}']
        market_data = result['data']
        metadata = result['metadata']

        # Display freshness indicator
        st.markdown("---")
        render_freshness_indicator(
            metadata['data_freshness'],
            metadata['retrieval_timestamp'],
            metadata.get('api_source', 'Unknown')
        )

        # Display warning if using historical/cached data
        if metadata['data_freshness'] == 'historical':
            st.warning(
                f"⚠️ 当前使用历史缓存数据，更新于 {metadata['retrieval_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}。"
                "市场数据可能不是最新的。",
                icon="⚠️"
            )

        # Display K-line chart
        st.subheader(f"📊 {symbol} K线图")
        fig = render_kline_chart(market_data, timeframe)
        st.plotly_chart(fig, use_container_width=True)

        # Display data table in expander
        with st.expander("📋 查看原始数据"):
            # Show basic stats
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("最新价", f"¥{market_data['close'].iloc[-1]:.2f}")

            with col2:
                price_change = market_data['close'].iloc[-1] - market_data['close'].iloc[0]
                price_change_pct = (price_change / market_data['close'].iloc[0]) * 100
                st.metric(
                    "期间涨跌",
                    f"¥{price_change:.2f}",
                    f"{price_change_pct:.2f}%"
                )

            with col3:
                st.metric("最高价", f"¥{market_data['high'].max():.2f}")

            with col4:
                st.metric("最低价", f"¥{market_data['low'].min():.2f}")

            # Display data table
            st.dataframe(
                market_data[['timestamp', 'open', 'high', 'low', 'close', 'volume']].sort_values('timestamp', ascending=False),
                use_container_width=True,
                height=400
            )

            # Display metadata
            st.markdown("**数据元信息：**")
            st.json({
                'api_source': metadata.get('api_source', 'Unknown'),
                'data_freshness': metadata['data_freshness'],
                'retrieval_timestamp': metadata['retrieval_timestamp'].isoformat(),
                'total_records': len(market_data),
                'date_range': {
                    'start': str(market_data['timestamp'].min()),
                    'end': str(market_data['timestamp'].max())
                }
            })

else:
    # Initial state - show instructions
    st.info('👆 请在上方输入股票代码并点击"查询数据"按钮')

    st.markdown("### 📌 使用说明")
    st.markdown("""
    1. **股票代码格式**：
       - 上海证券交易所：`600519.SH` (茅台)
       - 深圳证券交易所：`000001.SZ` (平安银行)

    2. **时间周期**：
       - **日线**：每日K线数据
       - **周线**：按周汇总的K线数据
       - **月线**：按月汇总的K线数据

    3. **数据新鲜度**：
       - 🟢 **实时**：数据延迟小于5秒
       - 🟡 **延迟15分钟**：数据延迟5秒-15分钟
       - ⚪ **历史数据**：超过15分钟的缓存数据

    4. **数据来源**：
       - 优先使用 Efinance API（免费，无需token）
       - 失败时自动切换到 AKShare API
       - 所有数据会缓存7天以提高可靠性
    """)

    st.markdown("### 📊 功能特性")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **K线图功能**：
        - 标准OHLC蜡烛图
        - 120日移动平均线
        - 成交量柱状图
        - 交互式缩放和悬停
        """)

    with col2:
        st.markdown("""
        **数据质量保障**：
        - API失败自动重试（3次）
        - 多数据源容错机制
        - 7天本地缓存
        - 数据新鲜度指示
        """)
