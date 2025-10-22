"""Holdings calculation logic."""

from sqlalchemy.orm import Session
from investlib_data.models import InvestmentRecord, CurrentHolding

class HoldingsCalculator:
    """Calculates current holdings from investment records."""

    def calculate_holdings(self, session: Session):
        """Calculates and updates the CurrentHolding table."""
        # Debugging: Simpler query + manual aggregation
        unsold_records = session.query(InvestmentRecord).filter(InvestmentRecord.sale_date.is_(None)).all()

        holdings_to_process = {}
        for record in unsold_records:
            if record.symbol not in holdings_to_process:
                holdings_to_process[record.symbol] = {
                    "total_quantity": 0,
                    "total_amount": 0,
                    "initial_purchase_date": record.purchase_date,
                    "asset_type": record.asset_type,  # Preserve asset type
                }

            holdings_to_process[record.symbol]["total_quantity"] += record.quantity
            holdings_to_process[record.symbol]["total_amount"] += record.purchase_amount
            if record.purchase_date < holdings_to_process[record.symbol]["initial_purchase_date"]:
                holdings_to_process[record.symbol]["initial_purchase_date"] = record.purchase_date

        for symbol, data in holdings_to_process.items():
            avg_purchase_price = data["total_amount"] / data["total_quantity"]
            
            holding = session.query(CurrentHolding).filter_by(symbol=symbol).first()

            if holding:
                holding.quantity = data["total_quantity"]
                holding.purchase_price = avg_purchase_price
                holding.purchase_date = data["initial_purchase_date"]
                holding.asset_type = data["asset_type"]  # Update asset type
            else:
                holding = CurrentHolding(
                    symbol=symbol,
                    asset_type=data["asset_type"],  # Set asset type
                    quantity=data["total_quantity"],
                    purchase_price=avg_purchase_price,
                    purchase_date=data["initial_purchase_date"],
                    current_price=0,  # Placeholder
                    profit_loss_amount=0,
                    profit_loss_pct=0
                )
                session.add(holding)
        
        session.commit()
