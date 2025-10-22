"""Operation Logs viewer page."""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.operation_logger import OperationLogger
import pandas as pd
import json

st.set_page_config(page_title="操作日志 Logs", page_icon="📋", layout="wide")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/myinvest.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

st.title("📋 操作日志")

st.info("🟢 当前模式：模拟交易")

# Filters
col1, col2 = st.columns([1, 3])

with col1:
    symbol_filter = st.text_input("筛选股票代码", placeholder="例如：600519.SH")

# Load logs
session = Session()
logger = OperationLogger(session)

try:
    logs = logger.get_operations(
        user_id="default_user",
        symbol=symbol_filter if symbol_filter else None,
        limit=50
    )

    if not logs:
        st.info("暂无操作记录")
    else:
        st.subheader(f"共 {len(logs)} 条记录")

        # Display as table
        log_data = []
        for log in logs:
            log_data.append({
                '时间': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                '股票': log.symbol,
                '操作': log.operation_type.value,
                '状态': log.execution_status.value,
                '模式': log.execution_mode.value
            })

        df = pd.DataFrame(log_data)
        st.dataframe(df, width='stretch')

        # Details expander
        st.subheader("操作详情")
        for i, log in enumerate(logs[:10]):  # Show first 10
            with st.expander(f"{log.symbol} - {log.operation_type.value} ({log.timestamp.strftime('%Y-%m-%d %H:%M')})"):
                st.write("**原始推荐：**")
                try:
                    rec = json.loads(log.original_recommendation)
                    st.json(rec)
                except:
                    st.text(log.original_recommendation)

                if log.user_modification:
                    st.write("**用户修改：**")
                    try:
                        mod = json.loads(log.user_modification)
                        st.json(mod)
                    except:
                        st.text(log.user_modification)

                if log.notes:
                    st.write(f"**备注：** {log.notes}")

finally:
    session.close()
