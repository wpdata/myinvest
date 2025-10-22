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
    st.header("📈 历史触发记录")

    st.info("此功能正在开发中，将展示历史上满足触发条件的日期和后续表现")

    # 可以添加历史回测结果的展示

# Tab 3: 策略模拟
with tab3:
    st.header("🎮 策略模拟器")

    st.markdown("""
    ### 模拟回测

    选择回测时间范围，查看策略的历史表现。
    """)

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=365)
        )

    with col2:
        end_date = st.date_input(
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
        st.info("""
        回测功能正在开发中...

        完成后将展示:
        - 净值曲线
        - 品种切换记录
        - 收益率统计
        - 最大回撤
        - 夏普比率

        可以运行命令行示例:
        ```bash
        python examples/rotation_strategy_example.py
        ```
        """)

# 页脚
st.divider()
st.markdown("""
### 📚 相关资源

- 📖 [策略详细文档](../STRATEGY_GUIDE.md)
- 💻 [示例代码](../examples/rotation_strategy_example.py)
- 🔧 [策略管理页面](./9_strategies.py)

**免责声明**: 本策略仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
""")
