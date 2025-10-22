"""CSV import logic for investment records."""

import pandas as pd
from sqlalchemy.orm import Session
from investlib_data.models import InvestmentRecord, DataSource
from datetime import datetime
import hashlib

class CSVImporter:
    """Imports investment records from a CSV file."""

    def parse_csv(self, file_path: str) -> pd.DataFrame:
        """Parses a CSV file into a pandas DataFrame."""
        return pd.read_csv(file_path)

    def save_to_database(self, file_path: str, session: Session) -> dict:
        """Parses a CSV file and saves the records to the database."""
        df = self.parse_csv(file_path)
        imported_count = 0
        rejected_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Validation
                if row['purchase_price'] <= 0:
                    raise ValueError("Purchase price must be positive.")
                if row['quantity'] <= 0:
                    raise ValueError("Quantity must be positive.")
                purchase_date = datetime.strptime(row['purchase_date'], '%Y-%m-%d').date()
                if purchase_date > datetime.now().date():
                    raise ValueError("Purchase date cannot be in the future.")

                # Create InvestmentRecord object
                record = InvestmentRecord(
                    symbol=row['symbol'],
                    purchase_date=purchase_date,
                    purchase_price=row['purchase_price'],
                    quantity=row['quantity'],
                    purchase_amount=row['purchase_price'] * row['quantity'],
                    data_source=DataSource.BROKER_STATEMENT,
                )
                # Handle optional fields
                if pd.notna(row.get('sale_date')) and row.get('sale_date'):
                    record.sale_date = datetime.strptime(row['sale_date'], '%Y-%m-%d').date()
                if pd.notna(row.get('sale_price')):
                    record.sale_price = row['sale_price']
                if record.sale_date and record.sale_price:
                    record.profit_loss = (record.sale_price - record.purchase_price) * record.quantity

                # Calculate checksum
                checksum_data = f"{record.symbol}{record.purchase_date}{record.purchase_price}{record.quantity}"
                record.checksum = hashlib.sha256(checksum_data.encode()).hexdigest()

                session.add(record)
                imported_count += 1
            except Exception as e:
                rejected_count += 1
                errors.append(f"Row {index + 2}: {e}")

        session.commit()

        return {"imported": imported_count, "rejected": rejected_count, "errors": errors}
