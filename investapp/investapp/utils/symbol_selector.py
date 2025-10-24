"""股票代码选择器 - 提供友好的股票选择界面。

支持从已录入持仓中选择，或手动输入新代码。
"""

import streamlit as st
from typing import List, Optional
import sys
import os

# Add library paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-data'))

from investlib_data.database import SessionLocal
from investlib_data.models import CurrentHolding


def get_user_holdings_symbols() -> List[str]:
    """从数据库获取用户已录入的持仓股票代码。

    Returns:
        股票代码列表，例如 ['600519.SH', '000001.SZ']
    """
    try:
        session = SessionLocal()
        try:
            # 查询所有当前持仓股票，去重
            holdings = session.query(CurrentHolding.symbol).distinct().all()
            symbols = [h.symbol for h in holdings]
            return sorted(symbols)  # 按字母排序
        finally:
            session.close()
    except Exception as e:
        st.warning(f"无法获取持仓列表: {e}")
        return []


def get_watchlist_symbols() -> List[str]:
    """从监视列表获取股票代码。

    Returns:
        股票代码列表，例如 ['600519.SH', '000001.SZ']
    """
    try:
        # Import WatchlistDB
        import os
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////Users/pw/ai/myinvest/data/myinvest.db")
        DB_PATH = DATABASE_URL.replace("sqlite:///", "")

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-data'))
        from investlib_data.watchlist_db import WatchlistDB

        watchlist_db = WatchlistDB(DB_PATH)
        symbols_data = watchlist_db.get_all_symbols(status='active')
        symbols = [item['symbol'] for item in symbols_data]
        return sorted(symbols)
    except Exception as e:
        st.warning(f"无法获取监视列表: {e}")
        return []


def get_all_available_symbols() -> List[str]:
    """获取所有可用的股票代码（持仓 + 监视列表）。

    Returns:
        去重后的股票代码列表
    """
    holdings = get_user_holdings_symbols()
    watchlist = get_watchlist_symbols()

    # 合并并去重
    all_symbols = list(set(holdings + watchlist))
    return sorted(all_symbols)


def render_symbol_selector(
    label: str = "股票代码",
    default_value: str = "600519.SH",
    help_text: Optional[str] = None,
    key: Optional[str] = None,
    allow_multiple: bool = False
) -> str:
    """渲染一个友好的股票代码选择器。

    Args:
        label: 输入框标签
        default_value: 默认值
        help_text: 帮助文本
        key: Streamlit组件key
        allow_multiple: 是否允许选择多个股票（用逗号分隔）

    Returns:
        选中的股票代码（或多个代码，逗号分隔）
    """
    # 获取所有可用股票（持仓 + 监视列表）
    available_symbols = get_all_available_symbols()

    # 确定默认帮助文本
    if help_text is None:
        if allow_multiple:
            help_text = "从持仓/监视列表选择，或手动输入股票代码（多个代码用逗号分隔）"
        else:
            help_text = "从持仓/监视列表选择，或手动输入股票代码"

    # 创建两种输入方式
    input_mode = st.radio(
        "输入方式",
        ["从列表选择", "手动输入"],
        horizontal=True,
        key=f"{key}_mode" if key else None,
        help="从持仓或监视列表中选择，或手动输入新的股票代码"
    )

    if input_mode == "从列表选择":
        if available_symbols:
            # 显示股票来源统计
            holdings_count = len(get_user_holdings_symbols())
            watchlist_count = len(get_watchlist_symbols())
            st.caption(f"💼 持仓 {holdings_count} 只 | 📋 监视 {watchlist_count} 只 | 总计 {len(available_symbols)} 只")

            if allow_multiple:
                # 多选模式
                selected_symbols = st.multiselect(
                    label,
                    options=available_symbols,
                    default=[available_symbols[0]] if available_symbols else [],
                    help=help_text,
                    key=key
                )
                return ",".join(selected_symbols)
            else:
                # 单选模式
                # 检查 default_value 是否在列表中
                default_index = 0
                if default_value in available_symbols:
                    default_index = available_symbols.index(default_value)

                selected_symbol = st.selectbox(
                    label,
                    options=available_symbols,
                    index=default_index,
                    help=help_text,
                    key=key
                )
                return selected_symbol
        else:
            st.warning("⚠️ 暂无股票，请先在「持仓记录」或「监视列表」页面添加")
            st.info("💡 您也可以切换到「手动输入」模式直接输入股票代码")
            return default_value

    else:  # 手动输入模式
        # 显示示例
        example_text = "例如: 600519.SH, 000001.SZ" if allow_multiple else "例如: 600519.SH"
        st.caption(f"✏️ {example_text}")

        manual_input = st.text_input(
            label,
            value=default_value,
            help=help_text,
            key=key
        )
        return manual_input


def render_symbol_selector_compact(
    default_value: str = "600519.SH",
    key: Optional[str] = None
) -> str:
    """紧凑版股票代码选择器（占用更少空间）。

    适合放在侧边栏或空间有限的地方。

    Args:
        default_value: 默认值
        key: Streamlit组件key

    Returns:
        选中的股票代码
    """
    # 获取所有可用股票（持仓 + 监视列表）
    available_symbols = get_all_available_symbols()

    if available_symbols:
        # 创建选项：所有股票 + "手动输入"选项
        options = available_symbols + ["+ 手动输入新代码"]

        # 检查 default_value 是否在列表中
        if default_value in available_symbols:
            default_index = available_symbols.index(default_value)
        else:
            default_index = len(available_symbols)  # 默认选择"手动输入"

        # 统计数量
        holdings_count = len(get_user_holdings_symbols())
        watchlist_count = len(get_watchlist_symbols())

        selection = st.selectbox(
            "股票代码",
            options=options,
            index=default_index,
            help=f"持仓 {holdings_count} 只 + 监视 {watchlist_count} 只",
            key=key
        )

        # 如果选择了"手动输入"
        if selection == "+ 手动输入新代码":
            manual_input = st.text_input(
                "输入股票代码",
                value=default_value,
                placeholder="例如: 600519.SH",
                key=f"{key}_manual" if key else None
            )
            return manual_input
        else:
            return selection
    else:
        # 没有可用股票，直接显示输入框
        st.caption("⚠️ 暂无股票，请添加持仓或监视列表")
        return st.text_input(
            "股票代码",
            value=default_value,
            placeholder="例如: 600519.SH",
            key=key
        )
