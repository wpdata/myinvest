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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/myinvest.db")
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
    symbol = st.text_input("代码 (e.g., 600519.SH, 512890.SH)")
    purchase_date = st.date_input("买入日期")
    purchase_price = st.number_input("买入价格", min_value=0.01, format="%.3f")
    quantity = st.number_input("数量", min_value=1)
    submitted = st.form_submit_button("添加记录")

    if submitted:
        try:
            session = Session()
            record = InvestmentRecord(
                symbol=symbol,
                asset_type=asset_type[1],  # Extract AssetType enum from tuple
                purchase_date=purchase_date,
                purchase_price=purchase_price,
                quantity=quantity,
                purchase_amount=purchase_price * quantity,
                data_source=DataSource.MANUAL_ENTRY,
            )
            checksum_data = f"{record.symbol}{record.purchase_date}{record.purchase_price}{record.quantity}"
            record.checksum = __import__('hashlib').sha256(checksum_data.encode()).hexdigest()
            session.add(record)
            session.commit()

            # Calculate holdings after manual entry
            calculator = HoldingsCalculator()
            calculator.calculate_holdings(session)

            st.success("记录添加成功!")
        except Exception as e:
            st.error(f"错误: {e}")
        finally:
            session.close()

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

    # Rename columns for better display
    df = df.rename(columns={
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
    })

    st.dataframe(df, use_container_width=True)
else:
    st.info("数据库中没有记录。")

session.close()
