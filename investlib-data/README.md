# investlib-data

Market data collection and personal investment record management library.

## Features

- CSV import with validation
- Tushare/AKShare API integration
- 7-day cache management
- SQLAlchemy ORM models

## CLI Commands

```bash
# Initialize database
investlib-data init-db

# Import CSV
investlib-data import-csv --file records.csv --output json

# Fetch market data
investlib-data fetch-market --symbol 600519.SH --output json
```

## Usage as Library

```python
from investlib_data.models import InvestmentRecord
from investlib_data.import_csv import CSVImporter

importer = CSVImporter()
results = importer.parse_csv("records.csv")
```
