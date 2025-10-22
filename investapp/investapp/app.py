"""Main entry point for the MyInvest Streamlit application."""

import streamlit as st

st.set_page_config(
    page_title="MyInvest - 智能投资分析系统",
    page_icon="💰",
    layout="wide"
)

st.sidebar.success("在上方选择一个页面导航")

st.title("💰 欢迎来到 MyInvest")

# Simulation mode banner (T060)
st.markdown(
    """
    <div style='background-color: #e8f5e9; padding: 15px; border-radius: 5px;
                border-left: 5px solid #4caf50; margin-bottom: 20px;'>
        <h3 style='color: #2e7d32; margin: 0;'>
            🟢 当前模式：模拟交易
        </h3>
        <p style='margin: 5px 0 0 0; color: #1b5e20;'>
            所有操作均为模拟，不会进行实际资金交易
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("--- ")
st.markdown("请从左侧的侧边栏中选择一个页面开始：")

st.markdown("### 📊 核心功能")
st.markdown("- **仪表盘**: 查看您的投资组合概览和 AI 建议")
st.markdown("- **投资记录管理**: 导入或手动管理您的交易历史")
st.markdown("- **市场数据**: 实时查询股票和ETF数据")
st.markdown("- **回测工具**: 测试策略的历史表现")

st.markdown("### 🎯 新功能 (v0.2)")
st.markdown("- **策略管理** ⭐: 查看和管理所有投资策略")
st.markdown("- **市场轮动策略** ⭐: 大盘恐慌时自动切换资产")

st.markdown("### 📚 帮助文档")
st.markdown("- 查看 `investapp/NEW_FEATURES.md` 了解新功能")
st.markdown("- 查看 `STRATEGY_GUIDE.md` 了解策略详情")
