"""
MyInvest V0.3 - Watchlist Management Page
Chinese-first UI for managing stock/futures/options watchlist.
"""

import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import Chinese localization
from investapp.locales import _

# Import watchlist database layer
from investlib_data.watchlist_db import WatchlistDB
from investlib_data.multi_asset_api import (
    detect_asset_type,
    get_asset_badge_emoji,
    get_asset_display_name
)

# Page configuration
st.set_page_config(
    page_title=_("watchlist.title"),
    page_icon="📋",
    layout="wide"
)

# Initialize database connection - use environment variable or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////Users/pw/ai/myinvest/data/myinvest.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "")
watchlist_db = WatchlistDB(DB_PATH)

# Page title
st.title(f"📋 {_('watchlist.title')}")

# ===== TAB LAYOUT =====
tab_manage, tab_import, tab_groups = st.tabs([
    "管理监视列表",
    "批量导入",
    "分组管理"
])

# ===== TAB 1: MANAGE WATCHLIST =====
with tab_manage:
    # Add symbol form
    st.subheader("➕ 添加品种到监视列表")

    # 添加市场代码帮助信息
    with st.expander("📖 品种代码格式说明", expanded=False):
        st.markdown("""
### 股票市场后缀

| 市场 | 后缀 | 示例 | 说明 |
|------|------|------|------|
| 上海A股 | `.SH` | 600519.SH | 贵州茅台 |
| 深圳A股 | `.SZ` | 000001.SZ | 平安银行 |
| 科创板 | `.SH` | 688981.SH | 中芯国际 |
| 创业板 | `.SZ` | 300750.SZ | 宁德时代 |

### 期货市场后缀

| 交易所 | 后缀 | 品种示例 | 说明 |
|--------|------|----------|------|
| 中金所 | `.CFFEX` | IF2506.CFFEX | 沪深300股指期货 |
| | | IC2506.CFFEX | 中证500股指期货 |
| | | IH2506.CFFEX | 上证50股指期货 |
| | | IM2506.CFFEX | 中证1000股指期货 |
| | | T2506.CFFEX | 10年期国债期货 |
| 上期所 | `.SHFE` | CU2505.SHFE | 沪铜 |
| | | AU2506.SHFE | 沪金 |
| | | AG2506.SHFE | 沪银 |
| | | RB2505.SHFE | 螺纹钢 |
| | | FU2505.SHFE | 燃料油 |
| 大商所 | `.DCE` | M2505.DCE | 豆粕 |
| | | C2505.DCE | 玉米 |
| | | I2505.DCE | 铁矿石 |
| | | P2505.DCE | 棕榈油 |
| 郑商所 | `.CZCE` | TA2505.CZCE | PTA（精对苯二甲酸） |
| | | MA2505.CZCE | 甲醇 |
| | | SR2505.CZCE | 白糖 |
| | | CF2505.CZCE | 棉花 |
| | | ZC2505.CZCE | 动力煤 |
| 上海能源 | `.INE` | SC2505.INE | 原油 |
| | | LU2505.INE | 低硫燃料油 |

### ETF基金后缀

| 市场 | 后缀 | 示例 | 说明 |
|------|------|------|------|
| 上海ETF | `.SH` | 510050.SH | 50ETF |
| | | 510300.SH | 沪深300ETF |
| | | 511010.SH | 国债ETF |
| 深圳ETF | `.SZ` | 159915.SZ | 创业板ETF |
| | | 159845.SZ | 中证1000ETF |

### 期权代码格式

期权代码较复杂，格式：`标的代码-到期月-C/P-行权价`
- 示例：`510050C2506M03000` (50ETF购6月3.0)
        """)

        st.markdown("""
### 常用期货品种速查

**金融期货**：
- IF (沪深300)、IC (中证500)、IH (上证50)、IM (中证1000) → `.CFFEX`
- T (10年国债)、TF (5年国债)、TS (2年国债) → `.CFFEX`

**金属期货**：
- CU (铜)、AL (铝)、ZN (锌)、PB (铅)、NI (镍) → `.SHFE`
- AU (黄金)、AG (白银) → `.SHFE`

**能源化工**：
- SC (原油)、LU (燃料油) → `.INE`
- FU (燃料油)、BU (沥青) → `.SHFE`
- TA (PTA)、MA (甲醇)、EG (乙二醇) → `.CZCE`
- L (塑料)、V (PVC)、PP (聚丙烯) → `.DCE`

**农产品**：
- M (豆粕)、Y (豆油)、A (豆一) → `.DCE`
- C (玉米)、CS (玉米淀粉) → `.DCE`
- SR (白糖)、CF (棉花)、RM (菜粕) → `.CZCE`
- P (棕榈油)、OI (菜籽油) → `.DCE`

**黑色系**：
- RB (螺纹钢)、HC (热轧卷板)、SS (不锈钢) → `.SHFE`
- I (铁矿石)、J (焦炭)、JM (焦煤) → `.DCE`
- ZC (动力煤)、SF (硅铁)、SM (硅锰) → `.CZCE`
        """)

    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

    with col1:
        symbol_input = st.text_input(
            _("watchlist.symbol_input"),
            placeholder="例如: 600519.SH, TA2505.CZCE, 510050.SH",
            help="💡 不确定代码？点击上方「品种代码格式说明」查看完整列表"
        )

    with col2:
        # Get existing groups for selector
        all_groups = watchlist_db.get_all_groups()
        if not all_groups:
            all_groups = ['default']

        group_selector = st.selectbox(
            _("watchlist.group_selector"),
            options=all_groups + ["[新建分组...]"],
            index=0
        )

    with col3:
        contract_type = st.selectbox(
            "资产类型",
            options=['stock', 'futures', 'option'],
            format_func=lambda x: _('watchlist.contract_type.' + x)
        )

    with col4:
        st.write("")  # Spacing
        st.write("")  # Spacing
        add_button = st.button(
            _("watchlist.add_button"),
            type="primary",
            use_container_width=True
        )

    # Handle new group creation
    if group_selector == "[新建分组...]":
        new_group_name = st.text_input("新分组名称", key="new_group")
        final_group = new_group_name if new_group_name else "default"
    else:
        final_group = group_selector

    # Handle add button
    if add_button:
        if not symbol_input:
            st.error("❌ 请输入股票代码")
        else:
            try:
                watchlist_db.add_symbol(
                    symbol=symbol_input.strip().upper(),
                    group_name=final_group,
                    contract_type=contract_type,
                    status='active'
                )
                st.success(f"✅ {_('watchlist.messages.symbol_added')} {symbol_input}")
                st.rerun()  # Refresh page to show new symbol
            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                st.error(f"❌ {_('errors.operation_failed')}: {str(e)}")

    st.divider()

    # Display watchlist table
    st.subheader("📊 当前监视列表")

    # Filter controls
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns([2, 2, 2, 1])

    with col_filter1:
        filter_status = st.radio(
            "状态筛选",
            options=['active', 'paused', 'all'],
            format_func=lambda x: {
                'active': '活跃',
                'paused': '已暂停',
                'all': '全部'
            }[x],
            horizontal=True
        )

    with col_filter2:
        filter_groups = st.multiselect(
            "分组筛选",
            options=all_groups,
            default=[]
        )

    with col_filter3:
        filter_asset_type = st.multiselect(
            "资产类型筛选",
            options=['stock', 'futures', 'option'],
            format_func=lambda x: f"{get_asset_badge_emoji(x)} {get_asset_display_name(x)}",
            default=[]
        )

    with col_filter4:
        st.write("")
        st.write("")
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

    # Fetch watchlist data
    if filter_groups:
        # Get symbols from selected groups
        watchlist_data = []
        for group in filter_groups:
            watchlist_data.extend(watchlist_db.get_symbols_by_group(group, status=filter_status))
    else:
        watchlist_data = watchlist_db.get_all_symbols(status=filter_status)

    # Apply asset type filter
    if filter_asset_type:
        watchlist_data = [s for s in watchlist_data if s['contract_type'] in filter_asset_type]

    # Display statistics
    total_symbols = len(watchlist_data)
    active_count = sum(1 for s in watchlist_data if s['status'] == 'active')
    paused_count = total_symbols - active_count

    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("总数", total_symbols)
    col_stat2.metric("活跃", active_count, delta=None)
    col_stat3.metric("已暂停", paused_count, delta=None)

    # Display watchlist table
    if watchlist_data:
        # Convert to DataFrame for display
        df = pd.DataFrame(watchlist_data)

        # Format display columns
        df['contract_type_cn'] = df['contract_type'].map({
            'stock': '股票',
            'futures': '期货',
            'option': '期权'
        })

        df['status_cn'] = df['status'].map({
            'active': '🟢 活跃',
            'paused': '⏸️ 已暂停'
        })

        # Display table with action buttons
        for idx, row in df.iterrows():
            col_display, col_actions = st.columns([4, 1])

            with col_display:
                # Enhanced display with multi-asset badges
                status_emoji = "🟢" if row['status'] == 'active' else "⏸️"
                asset_type = row['contract_type']
                type_emoji = get_asset_badge_emoji(asset_type)
                type_display = get_asset_display_name(asset_type)

                # Auto-detect asset type from symbol if needed
                detected_type = detect_asset_type(row['symbol'])
                if detected_type != asset_type:
                    # Show warning if database type doesn't match symbol pattern
                    type_badge = f"{type_emoji} {type_display} ⚠️"
                else:
                    type_badge = f"{type_emoji} {type_display}"

                st.markdown(
                    f"{status_emoji} **{row['symbol']}** | "
                    f"{type_badge} | "
                    f"📁 {row['group_name']}"
                )

            with col_actions:
                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    # Pause/Resume button
                    if row['status'] == 'active':
                        if st.button("⏸️", key=f"pause_{idx}", help="暂停"):
                            watchlist_db.set_symbol_status(row['symbol'], 'paused')
                            st.success(f"已暂停 {row['symbol']}")
                            st.rerun()
                    else:
                        if st.button("▶️", key=f"resume_{idx}", help="恢复"):
                            watchlist_db.set_symbol_status(row['symbol'], 'active')
                            st.success(f"已恢复 {row['symbol']}")
                            st.rerun()

                with action_col2:
                    # Edit group button (placeholder for modal)
                    if st.button("✏️", key=f"edit_{idx}", help="编辑分组"):
                        st.session_state[f'edit_symbol_{idx}'] = row['symbol']

                with action_col3:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{idx}", help="删除"):
                        if watchlist_db.remove_symbol(row['symbol']):
                            st.success(f"✅ 已删除 {row['symbol']}")
                            st.rerun()
                        else:
                            st.error(f"❌ 删除失败")

            # Handle edit modal
            if f'edit_symbol_{idx}' in st.session_state:
                with st.expander(f"编辑 {row['symbol']} 的分组", expanded=True):
                    new_group = st.selectbox(
                        "选择新分组",
                        options=all_groups + ["[新建分组...]"],
                        key=f"new_group_{idx}"
                    )

                    if new_group == "[新建分组...]":
                        new_group = st.text_input("新分组名称", key=f"new_group_name_{idx}")

                    if st.button("保存", key=f"save_{idx}"):
                        if watchlist_db.update_symbol_group(row['symbol'], new_group):
                            st.success(f"✅ 已更新 {row['symbol']} 到分组 {new_group}")
                            del st.session_state[f'edit_symbol_{idx}']
                            st.rerun()

    else:
        st.info("📋 监视列表为空，请添加股票代码")

    # Batch actions
    if watchlist_data:
        st.divider()
        st.subheader("批量操作")

        col_batch1, col_batch2 = st.columns(2)

        with col_batch1:
            if st.button("⏸️ 暂停所有活跃股票", use_container_width=True):
                active_symbols = [s['symbol'] for s in watchlist_data if s['status'] == 'active']
                if active_symbols:
                    count = watchlist_db.batch_update_status(active_symbols, 'paused')
                    st.success(f"✅ 已暂停 {count} 个股票")
                    st.rerun()

        with col_batch2:
            if st.button("▶️ 恢复所有已暂停股票", use_container_width=True):
                paused_symbols = [s['symbol'] for s in watchlist_data if s['status'] == 'paused']
                if paused_symbols:
                    count = watchlist_db.batch_update_status(paused_symbols, 'active')
                    st.success(f"✅ 已恢复 {count} 个股票")
                    st.rerun()

# ===== TAB 2: BATCH IMPORT =====
with tab_import:
    st.subheader("📥 批量导入股票代码")

    st.markdown("""
    ### CSV 格式要求

    CSV 文件应包含以下列（带表头）：

    | symbol | group_name | contract_type |
    |--------|------------|---------------|
    | 600519.SH | 核心持仓 | stock |
    | 000001.SZ | 科技股 | stock |
    | IF2506.CFFEX | 期货 | futures |

    **说明**：
    - `symbol`（必需）：股票/期货/期权代码
    - `group_name`（可选）：分组名称，默认为 "default"
    - `contract_type`（可选）：资产类型（stock/futures/option），默认为 "stock"
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        _("watchlist.csv_upload"),
        type=['csv'],
        help="上传符合格式要求的 CSV 文件"
    )

    skip_duplicates = st.checkbox("跳过重复的股票代码（不报错）", value=True)

    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_path = f"/tmp/watchlist_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(temp_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Preview CSV
        st.subheader("📄 文件预览")
        try:
            preview_df = pd.read_csv(temp_path)
            st.dataframe(preview_df.head(10), use_container_width=True)

            st.info(f"📊 文件包含 {len(preview_df)} 行数据")

            # Import button
            if st.button("✅ 确认导入", type="primary", use_container_width=True):
                with st.spinner("正在导入..."):
                    try:
                        success_count, error_list = watchlist_db.batch_import_from_csv(
                            temp_path,
                            skip_duplicates=skip_duplicates
                        )

                        st.success(f"✅ 成功导入 {success_count} 个股票代码")

                        if error_list:
                            st.warning(f"⚠️ 导入过程中出现 {len(error_list)} 个错误")
                            with st.expander("查看错误详情"):
                                for error in error_list:
                                    st.error(error)

                        # Clean up temp file
                        os.remove(temp_path)

                        st.balloons()
                        st.info("💡 切换到「管理监视列表」标签查看导入结果")

                    except Exception as e:
                        st.error(f"❌ 导入失败: {str(e)}")

        except Exception as e:
            st.error(f"❌ 无法读取 CSV 文件: {str(e)}")

# ===== TAB 3: GROUP MANAGEMENT =====
with tab_groups:
    st.subheader("📁 分组管理")

    # Get all groups with statistics
    all_groups = watchlist_db.get_all_groups()

    if all_groups:
        st.info(f"📊 当前共有 {len(all_groups)} 个分组")

        for group in all_groups:
            # Get symbols in this group
            group_symbols = watchlist_db.get_symbols_by_group(group, status='all')
            active_in_group = sum(1 for s in group_symbols if s['status'] == 'active')

            col_group, col_stats, col_actions = st.columns([2, 2, 1])

            with col_group:
                st.markdown(f"### 📁 {group}")

            with col_stats:
                st.write("")
                st.write("")
                st.metric("股票数", len(group_symbols), delta=f"{active_in_group} 活跃")

            with col_actions:
                st.write("")
                st.write("")
                # Rename/Delete buttons could be added here
                if st.button("📋 查看", key=f"view_group_{group}"):
                    st.session_state['filter_group'] = group

            # Display symbols in group
            if f'view_group_{group}' in st.session_state or st.session_state.get('filter_group') == group:
                with st.expander(f"分组 {group} 中的股票", expanded=True):
                    if group_symbols:
                        for symbol in group_symbols:
                            status_emoji = "🟢" if symbol['status'] == 'active' else "⏸️"
                            asset_type = symbol['contract_type']
                            type_emoji = get_asset_badge_emoji(asset_type)
                            type_display = get_asset_display_name(asset_type)
                            st.write(f"{status_emoji} {symbol['symbol']} {type_emoji} {type_display}")
                    else:
                        st.info("该分组为空")

            st.divider()

    else:
        st.info("📋 暂无分组，添加股票时会自动创建分组")

# ===== FOOTER INFO =====
st.divider()
st.caption(f"💡 提示：监视列表中的活跃股票会被定时调度器自动更新数据 | "
           f"当前共 {watchlist_db.get_symbol_count('active')} 个活跃股票")
