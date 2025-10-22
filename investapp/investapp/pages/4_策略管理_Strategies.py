"""策略管理页面 - 查看和管理所有投资策略。"""

import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from investlib_quant.strategies import StrategyRegistry

st.set_page_config(page_title="策略管理 Strategies", page_icon="🎯", layout="wide")

st.title("🎯 投资策略管理中心")

# 侧边栏筛选
with st.sidebar:
    st.header("筛选选项")

    # 获取所有策略
    all_strategies = StrategyRegistry.list_all()

    # 收集所有标签
    all_tags = set()
    for strategy in all_strategies:
        all_tags.update(strategy.tags)

    # 标签筛选
    selected_tags = st.multiselect(
        "按标签筛选",
        options=sorted(all_tags),
        default=[]
    )

    # 风险等级筛选
    risk_levels = st.multiselect(
        "按风险等级筛选",
        options=["LOW", "MEDIUM", "HIGH"],
        default=[]
    )

    # 交易频率筛选
    trade_frequencies = st.multiselect(
        "按交易频率筛选",
        options=["LOW", "MEDIUM", "HIGH"],
        default=[]
    )

# 应用筛选
filtered_strategies = all_strategies

if selected_tags:
    filtered_strategies = [
        s for s in filtered_strategies
        if any(tag in s.tags for tag in selected_tags)
    ]

if risk_levels:
    filtered_strategies = [
        s for s in filtered_strategies
        if s.risk_level in risk_levels
    ]

if trade_frequencies:
    filtered_strategies = [
        s for s in filtered_strategies
        if s.trade_frequency in trade_frequencies
    ]

# 显示策略统计
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("总策略数", len(all_strategies))

with col2:
    st.metric("筛选结果", len(filtered_strategies))

with col3:
    low_risk_count = len([s for s in all_strategies if s.risk_level == "LOW"])
    st.metric("低风险策略", low_risk_count)

with col4:
    rotation_count = len([s for s in all_strategies if "轮动" in s.tags])
    st.metric("轮动策略", rotation_count)

st.divider()

# 策略列表
if not filtered_strategies:
    st.warning("没有找到符合条件的策略")
else:
    st.subheader(f"策略列表 ({len(filtered_strategies)}个)")

    for i, strategy in enumerate(filtered_strategies, 1):
        with st.expander(f"{i}. {strategy.display_name} ({strategy.name})", expanded=(i == 1)):
            # 基本信息
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**📝 描述**: {strategy.description}")
                st.markdown(f"**🎯 核心逻辑**: {strategy.logic}")

            with col2:
                # 风险等级标记
                risk_color = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🔴"
                }
                st.markdown(f"**风险等级**: {risk_color.get(strategy.risk_level, '⚪')} {strategy.risk_level}")
                st.markdown(f"**持仓周期**: {strategy.typical_holding_period}")
                st.markdown(f"**交易频率**: {strategy.trade_frequency}")

            # 标签
            st.markdown("**🏷️ 标签**: " + " • ".join([f"`{tag}`" for tag in strategy.tags]))

            # 适用场景
            st.markdown("**✅ 适用于**: " + " | ".join(strategy.suitable_for))

            st.divider()

            # 参数说明
            if strategy.parameters:
                st.markdown("#### ⚙️ 参数配置")
                param_data = []
                for param_name, param_info in strategy.parameters.items():
                    if isinstance(param_info, dict):
                        param_data.append({
                            "参数名": param_name,
                            "默认值": param_info.get('default', 'N/A'),
                            "说明": param_info.get('description', '')
                        })
                    else:
                        param_data.append({
                            "参数名": param_name,
                            "默认值": param_info,
                            "说明": ""
                        })

                st.table(param_data)

            # 使用示例
            if strategy.example_code:
                st.markdown("#### 💻 使用示例")
                st.code(strategy.example_code, language="python")

            # 快速操作按钮
            st.markdown("#### 🚀 快速操作")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📊 查看回测结果", key=f"backtest_{strategy.name}"):
                    st.info("回测功能正在开发中...")

            with col2:
                if st.button("🎮 策略模拟器", key=f"simulate_{strategy.name}"):
                    st.info("策略模拟器正在开发中...")

            with col3:
                if st.button("📖 详细文档", key=f"docs_{strategy.name}"):
                    st.info("请查看 STRATEGY_GUIDE.md 文档")

# 策略对比功能
st.divider()
st.subheader("📊 策略对比")

if len(filtered_strategies) >= 2:
    col1, col2 = st.columns(2)

    with col1:
        strategy1 = st.selectbox(
            "选择策略 1",
            options=[s.name for s in filtered_strategies],
            format_func=lambda x: next((s.display_name for s in filtered_strategies if s.name == x), x)
        )

    with col2:
        strategy2 = st.selectbox(
            "选择策略 2",
            options=[s.name for s in filtered_strategies if s.name != strategy1],
            format_func=lambda x: next((s.display_name for s in filtered_strategies if s.name == x), x)
        )

    if st.button("开始对比", type="primary"):
        s1 = StrategyRegistry.get(strategy1)
        s2 = StrategyRegistry.get(strategy2)

        if s1 and s2:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"### {s1.display_name}")
                st.markdown(f"**描述**: {s1.description}")
                st.markdown(f"**逻辑**: {s1.logic}")
                st.markdown(f"**风险**: {s1.risk_level}")
                st.markdown(f"**持仓周期**: {s1.typical_holding_period}")
                st.markdown(f"**交易频率**: {s1.trade_frequency}")
                st.markdown(f"**标签**: {', '.join(s1.tags)}")

            with col2:
                st.markdown(f"### {s2.display_name}")
                st.markdown(f"**描述**: {s2.description}")
                st.markdown(f"**逻辑**: {s2.logic}")
                st.markdown(f"**风险**: {s2.risk_level}")
                st.markdown(f"**持仓周期**: {s2.typical_holding_period}")
                st.markdown(f"**交易频率**: {s2.trade_frequency}")
                st.markdown(f"**标签**: {', '.join(s2.tags)}")
else:
    st.info("需要至少2个策略才能进行对比")

# 页脚说明
st.divider()
st.markdown("""
### 📚 使用说明

1. **查看策略**: 点击策略名称展开查看详细信息
2. **筛选策略**: 使用左侧边栏按标签、风险等级或交易频率筛选
3. **对比策略**: 使用页面底部的策略对比工具
4. **详细文档**: 查看项目根目录下的 `STRATEGY_GUIDE.md` 文件

**提示**: 新增的"市场轮动策略"是一个多品种轮动策略，可以在市场恐慌时自动切换到进攻性资产。
""")
