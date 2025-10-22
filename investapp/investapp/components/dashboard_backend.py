"""Backend logic for the main dashboard."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from investlib_data.models import CurrentHolding, InvestmentRecord, AccountBalance, AssetType

def get_dashboard_data(session: Session) -> dict:
    """Gathers all data required for the dashboard.

    Args:
        session: The database session.

    Returns:
        A dictionary containing dashboard data.
    """
    # Get current holdings grouped by asset type
    holdings = session.query(CurrentHolding).all()
    holdings_by_type = {}
    for asset_type in AssetType:
        type_holdings = [h for h in holdings if h.asset_type == asset_type]
        if type_holdings:
            holdings_by_type[asset_type] = type_holdings

    # Get account balances
    balances = session.query(AccountBalance).all()
    balances_by_type = {b.account_type: b.available_cash for b in balances}

    # Calculate total assets (holdings + cash)
    total_holdings_value = sum(h.quantity * h.current_price for h in holdings)
    total_cash = sum(balances_by_type.values())
    total_assets = total_holdings_value + total_cash

    # Get profit loss history
    # For v0.1 MVP: Simplified implementation shows current unrealized P/L for each holding
    # Note: This is a snapshot, not historical daily P/L tracking
    # Real historical P/L tracking requires daily price data (coming in User Story 2/4)

    profit_loss_history = []

    if holdings:
        # Create a simple timeline showing P/L for each position
        for h in holdings:
            profit_loss_history.append((h.purchase_date, 0))  # Start at 0 on purchase date

        # Add current P/L as the latest data point
        from datetime import date
        today = date.today()
        current_total_pl = sum(h.profit_loss_amount for h in holdings)
        profit_loss_history.append((today, current_total_pl))

    # Also query sold positions P/L (if any exist)
    sold_records = session.query(InvestmentRecord.sale_date, InvestmentRecord.profit_loss).filter(
        InvestmentRecord.profit_loss.isnot(None),
        InvestmentRecord.sale_date.isnot(None)
    ).all()

    # Add sold positions to history
    for sale_date, pl in sold_records:
        profit_loss_history.append((sale_date, pl))

    return {
        "total_assets": total_assets,
        "total_holdings_value": total_holdings_value,
        "total_cash": total_cash,
        "holdings": holdings,  # All holdings
        "holdings_by_type": holdings_by_type,  # Grouped by asset type
        "balances_by_type": balances_by_type,  # Cash balances by account type
        "profit_loss_history": profit_loss_history,
        "sold_records": sold_records,  # Historical sold positions
    }
