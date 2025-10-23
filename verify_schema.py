#!/usr/bin/env python3
"""验证数据库 Schema 与模型定义是否一致"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加路径
sys.path.insert(0, 'investlib-data')

from sqlalchemy import create_engine, inspect
from investlib_data.models import Base, InvestmentRecord, CurrentHolding
from investlib_data.database import DATABASE_URL

def verify_schema():
    """验证 Schema 一致性"""
    print("=" * 60)
    print("数据库 Schema 验证")
    print("=" * 60)
    print()

    # 连接数据库
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    print(f"数据库: {DATABASE_URL}")
    print()

    # 检查 Alembic 版本
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"✓ Alembic 版本: {version}")
    print()

    # 验证 InvestmentRecord
    print("1. 验证 InvestmentRecord (investment_records 表)")
    print("-" * 60)

    # 获取表结构
    columns = inspector.get_columns('investment_records')
    column_names = {col['name'] for col in columns}

    # 期望的字段
    expected_fields = {
        'record_id', 'symbol', 'asset_type', 'purchase_amount',
        'purchase_price', 'purchase_date', 'quantity',
        'sale_date', 'sale_price', 'profit_loss',
        'direction', 'margin_used',  # v0.3 新增
        'data_source', 'ingestion_timestamp', 'checksum',
        'created_at', 'updated_at'
    }

    # 检查缺失字段
    missing = expected_fields - column_names
    extra = column_names - expected_fields

    if not missing and not extra:
        print("  ✓ 所有字段一致")
    else:
        if missing:
            print(f"  ✗ 缺失字段: {missing}")
        if extra:
            print(f"  ⚠️  额外字段: {extra}")

    # 检查关键字段
    key_fields = ['direction', 'margin_used']
    for field in key_fields:
        if field in column_names:
            print(f"  ✓ {field} 字段存在")
        else:
            print(f"  ✗ {field} 字段缺失")

    print()

    # 验证 CurrentHolding
    print("2. 验证 CurrentHolding (current_holdings 表)")
    print("-" * 60)

    columns = inspector.get_columns('current_holdings')
    column_names = {col['name'] for col in columns}

    expected_fields = {
        'holding_id', 'symbol', 'asset_type', 'quantity',
        'purchase_price', 'current_price',
        'profit_loss_amount', 'profit_loss_pct',
        'purchase_date', 'last_update_timestamp',
        'direction', 'margin_used',  # v0.3 新增
        'created_at', 'updated_at'
    }

    missing = expected_fields - column_names
    extra = column_names - expected_fields

    if not missing and not extra:
        print("  ✓ 所有字段一致")
    else:
        if missing:
            print(f"  ✗ 缺失字段: {missing}")
        if extra:
            print(f"  ⚠️  额外字段: {extra}")

    # 检查关键字段
    for field in key_fields:
        if field in column_names:
            print(f"  ✓ {field} 字段存在")
        else:
            print(f"  ✗ {field} 字段缺失")

    print()

    # 检查模型定义
    print("3. 验证模型定义")
    print("-" * 60)

    # InvestmentRecord
    record_attrs = set(dir(InvestmentRecord))
    if 'direction' in record_attrs and 'margin_used' in record_attrs:
        print("  ✓ InvestmentRecord 模型包含 direction 和 margin_used")
    else:
        print("  ✗ InvestmentRecord 模型缺少字段")

    # CurrentHolding
    holding_attrs = set(dir(CurrentHolding))
    if 'direction' in holding_attrs and 'margin_used' in holding_attrs:
        print("  ✓ CurrentHolding 模型包含 direction 和 margin_used")
    else:
        print("  ✗ CurrentHolding 模型缺少字段")

    print()
    print("=" * 60)
    print("验证完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        verify_schema()
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
