#!/usr/bin/env python
"""Fix holdings by removing sold positions from current_holdings table."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investlib_data.database import get_engine, SessionLocal
from investlib_data.holdings import HoldingsCalculator

def main():
    """Recalculate all current holdings to remove sold positions."""
    print("正在重新计算持仓...")

    session = SessionLocal()

    try:
        calculator = HoldingsCalculator()
        calculator.calculate_holdings(session)

        print("✅ 持仓计算完成！已平仓的持仓已从当前持仓中移除。")

        # Show current holdings
        from investlib_data.models import CurrentHolding
        holdings = session.query(CurrentHolding).all()

        if holdings:
            print(f"\n当前持仓列表 ({len(holdings)} 个):")
            print("-" * 80)
            for h in holdings:
                print(f"  {h.symbol:12s} | {h.asset_type.value:10s} | 数量: {h.quantity:8.2f} | 成本: ¥{h.purchase_price:.3f}")
        else:
            print("\n当前没有持仓")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
