"""Streamlit page for managing investment records."""

import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import InvestmentRecord, DataSource, CurrentHolding, AssetType
from investlib_data.import_csv import CSVImporter
from investlib_data.holdings import HoldingsCalculator
from datetime import datetime
import pandas as pd
import os

st.set_page_config(page_title="投资记录 Records", page_icon="📝", layout="wide")

# Database connection
# 使用绝对路径确保无论从哪个目录启动都能找到正确的数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////Users/pw/ai/myinvest/data/myinvest.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def get_records(session):
    return session.query(InvestmentRecord).all()

st.title("📝 投资记录管理")

# --- Import CSV Section ---
st.header("从 CSV 文件导入")
uploaded_file = st.file_uploader("选择一个 CSV 文件", type="csv")
if uploaded_file is not None:
    # To call the CLI, we would need to save the file and then run a subprocess.
    # For a pure Streamlit app, it's easier to call the importer logic directly.
    with open("temp.csv", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    session = Session()
    importer = CSVImporter()
    result = importer.save_to_database("temp.csv", session)
    
    # Calculate holdings after import
    calculator = HoldingsCalculator()
    calculator.calculate_holdings(session)
    
    session.close()
    os.remove("temp.csv")

    st.success(f"导入完成! 成功: {result['imported']}, 失败: {result['rejected']}")
    if result['errors']:
        st.error("导入失败的记录:")
        for error in result['errors']:
            st.write(error)

# --- Manual Entry Section ---
st.header("手动输入记录")
with st.form("manual_entry_form"):
    asset_type = st.selectbox("资产类型", options=[
        ("股票", AssetType.STOCK),
        ("ETF基金", AssetType.ETF),
        ("场外基金", AssetType.FUND),
        ("期货", AssetType.FUTURES),
        ("期权", AssetType.OPTION),
        ("债券", AssetType.BOND),
        ("可转债", AssetType.CONVERTIBLE_BOND),
        ("其他", AssetType.OTHER)
    ], format_func=lambda x: x[0])

    symbol = st.text_input("代码 (e.g., 600519.SH, IF2401, 510050C2401M04000)")

    # 方向选择 - 所有资产都显示，但添加说明
    col1, col2 = st.columns(2)
    with col1:
        # 根据资产类型提供不同的帮助文本
        selected_asset_type = asset_type[1]
        can_short = selected_asset_type in [AssetType.FUTURES, AssetType.OPTION]

        if can_short:
            help_text = "期货/期权可以做多或做空"
            default_index = 0
        else:
            help_text = "股票/ETF/基金通常只能做多"
            default_index = 0

        direction = st.selectbox(
            "持仓方向",
            options=[("做多 (Long)", "long"), ("做空 (Short)", "short")],
            format_func=lambda x: x[0],
            index=default_index,
            help=help_text
        )
    with col2:
        purchase_date = st.date_input("买入日期")

    # 价格和数量
    col3, col4 = st.columns(2)
    with col3:
        purchase_price = st.number_input("买入价格", min_value=0.01, format="%.3f")
    with col4:
        quantity = st.number_input("数量", min_value=1)

    # 保证金（所有资产都显示，但添加说明）
    if can_short:
        help_text = "期货/期权合约使用的保证金金额"
    else:
        help_text = "股票/ETF无需保证金，保持为0"

    margin_used = st.number_input(
        "保证金",
        min_value=0.0,
        value=0.0,
        format="%.2f",
        help=help_text
    )

    submitted = st.form_submit_button("添加记录")

    if submitted:
        try:
            session = Session()

            # 计算买入金额
            purchase_amount = purchase_price * quantity

            record = InvestmentRecord(
                symbol=symbol,
                asset_type=asset_type[1],  # Extract AssetType enum from tuple
                purchase_date=purchase_date,
                purchase_price=purchase_price,
                quantity=quantity,
                purchase_amount=purchase_amount,
                direction=direction[1],  # "long" or "short"
                margin_used=margin_used,
                data_source=DataSource.MANUAL_ENTRY,
            )
            checksum_data = f"{record.symbol}{record.purchase_date}{record.purchase_price}{record.quantity}"
            record.checksum = __import__('hashlib').sha256(checksum_data.encode()).hexdigest()
            session.add(record)
            session.commit()

            # Calculate holdings after manual entry
            calculator = HoldingsCalculator()
            calculator.calculate_holdings(session)

            direction_text = "做多" if direction[1] == "long" else "做空"
            st.success(
                f"✅ 记录添加成功！\n\n"
                f"- {asset_type[0]}: {symbol}\n"
                f"- 方向: {direction_text}\n"
                f"- 数量: {quantity}\n"
                f"- 价格: ¥{purchase_price:.2f}\n"
                f"- 金额: ¥{purchase_amount:.2f}"
                + (f"\n- 保证金: ¥{margin_used:.2f}" if margin_used > 0 else "")
            )
        except Exception as e:
            st.error(f"错误: {e}")
            import traceback
            st.code(traceback.format_exc())
        finally:
            session.close()

# --- Sell/Close Position Section ---
st.header("记录卖出/平仓")
st.markdown("选择一个未平仓的持仓记录，输入卖出信息")

# Get open positions (records without sale_date)
session_sell = Session()
open_positions = session_sell.query(InvestmentRecord).filter(
    InvestmentRecord.sale_date.is_(None)
).all()

if open_positions:
    # Create a dict for display with direction info
    position_display = {}
    for rec in open_positions:
        # 安全获取 direction，旧记录可能没有
        direction = getattr(rec, 'direction', 'long')
        direction_text = "做多" if direction == "long" else "做空"

        asset_type_text = rec.asset_type.value if hasattr(rec.asset_type, 'value') else str(rec.asset_type)

        # 只有期货/期权才显示方向
        if asset_type_text in ['futures', 'option']:
            display_text = f"{rec.symbol} [{asset_type_text}] {direction_text} - {rec.purchase_date} ({rec.quantity}@¥{rec.purchase_price:.2f})"
        else:
            display_text = f"{rec.symbol} [{asset_type_text}] - {rec.purchase_date} ({rec.quantity}@¥{rec.purchase_price:.2f})"

        position_display[display_text] = rec.record_id

    with st.form("sell_form"):
        selected_position = st.selectbox(
            "选择要平仓的持仓",
            options=list(position_display.keys()),
            help="显示格式: 代码 [资产类型] 方向 - 日期 (数量@价格)"
        )
        sale_date = st.date_input("平仓日期", value=datetime.today().date())
        sale_price = st.number_input("平仓价格", min_value=0.01, format="%.3f")
        sell_submitted = st.form_submit_button("记录平仓")

        if sell_submitted and selected_position:
            try:
                record_id = position_display[selected_position]
                record = session_sell.query(InvestmentRecord).filter_by(record_id=record_id).first()

                if record:
                    # Update sale information
                    record.sale_date = sale_date
                    record.sale_price = sale_price

                    # Calculate profit/loss based on direction
                    sale_amount = sale_price * record.quantity

                    # 安全获取 direction，旧记录可能没有
                    direction = getattr(record, 'direction', 'long')

                    if direction == "long":
                        # 做多: 卖出价 > 买入价 = 盈利
                        record.profit_loss = sale_amount - record.purchase_amount
                    else:  # short
                        # 做空: 买入价 > 卖出价 = 盈利（先高价卖，后低价买回）
                        record.profit_loss = record.purchase_amount - sale_amount

                    session_sell.commit()

                    # Recalculate current holdings
                    calculator = HoldingsCalculator()
                    calculator.calculate_holdings(session_sell)

                    # Display result
                    profit_pct = (record.profit_loss / record.purchase_amount) * 100
                    direction_text = "做多" if direction == "long" else "做空"

                    # 判断是否需要显示方向
                    asset_type_text = record.asset_type.value if hasattr(record.asset_type, 'value') else str(record.asset_type)
                    show_direction = asset_type_text in ['futures', 'option']

                    success_msg = f"✅ 平仓记录已保存！\n\n- 资产: {record.symbol}\n"
                    if show_direction:
                        success_msg += f"- 方向: {direction_text}\n"
                    success_msg += (
                        f"- 开仓: ¥{record.purchase_amount:.2f}\n"
                        f"- 平仓: ¥{sale_amount:.2f}\n"
                        f"- 盈亏: ¥{record.profit_loss:.2f} ({profit_pct:+.2f}%)"
                    )
                    st.success(success_msg)
                    st.rerun()
                else:
                    st.error("找不到该记录")

            except Exception as e:
                session_sell.rollback()
                st.error(f"错误: {e}")
                import traceback
                st.code(traceback.format_exc())
else:
    st.info("当前没有未平仓的持仓记录")

session_sell.close()

# --- Display Records Section ---
st.header("所有投资记录")
session = Session()
records = get_records(session)
if records:
    df = pd.DataFrame([r.__dict__ for r in records])
    df = df.drop(columns=['_sa_instance_state', 'record_id', 'ingestion_timestamp', 'checksum', 'created_at', 'updated_at'], errors='ignore')

    # Convert enums to string to avoid PyArrow conversion error
    if 'data_source' in df.columns:
        df['data_source'] = df['data_source'].apply(lambda x: x.value if hasattr(x, 'value') else x)
    if 'asset_type' in df.columns:
        df['asset_type'] = df['asset_type'].apply(lambda x: x.value if hasattr(x, 'value') else x)

    # Convert direction to Chinese, handle missing values
    if 'direction' in df.columns:
        df['direction'] = df['direction'].fillna('long').apply(lambda x: "做多" if x == "long" else "做空")

    # 检查是否有期货或期权
    has_derivatives = False
    if 'asset_type' in df.columns:
        has_derivatives = df['asset_type'].isin(['futures', 'option']).any()

    # 只为期货和期权显示方向列，其他资产类型隐藏方向
    show_direction_column = False
    if 'direction' in df.columns:
        if has_derivatives:
            show_direction_column = True
        else:
            # 如果没有期货/期权，删除方向列
            df = df.drop(columns=['direction'], errors='ignore')

    # Rename columns for better display
    rename_dict = {
        'symbol': '代码',
        'asset_type': '资产类型',
        'purchase_amount': '买入金额',
        'purchase_price': '买入价格',
        'purchase_date': '买入日期',
        'quantity': '数量',
        'sale_date': '卖出日期',
        'sale_price': '卖出价格',
        'profit_loss': '盈亏',
        'data_source': '数据来源'
    }

    if show_direction_column:
        rename_dict['direction'] = '方向'

    # 只在有期货/期权时显示保证金
    if 'margin_used' in df.columns:
        if has_derivatives:
            rename_dict['margin_used'] = '保证金'
        else:
            df = df.drop(columns=['margin_used'], errors='ignore')

    df = df.rename(columns=rename_dict)

    # Reorder columns for better readability
    column_order = ['代码', '资产类型']
    if show_direction_column:
        column_order.append('方向')
    column_order.extend(['买入日期', '买入价格', '数量', '买入金额'])
    if has_derivatives and '保证金' in df.columns:
        column_order.append('保证金')
    column_order.extend(['卖出日期', '卖出价格', '盈亏', '数据来源'])

    # Only keep columns that exist
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]

    st.dataframe(df, use_container_width=True)
else:
    st.info("数据库中没有记录。")

session.close()
