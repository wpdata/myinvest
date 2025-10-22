# Data Model: MyInvest v0.1

**Date**: 2025-10-14
**Feature**: MyInvest v0.1 - Intelligent Investment Analysis System
**Purpose**: Define entity schemas, relationships, validation rules, and state transitions

## Overview

MyInvest v0.1 uses 5 core entities to manage personal investment data, market data, AI recommendations, operation logs, and current portfolio positions. All entities are implemented using SQLAlchemy 2.0+ ORM with SQLite backend (v0.1) and designed for seamless PostgreSQL migration (v0.2+).

**Key Design Principles**:
- Data Integrity (Constitution Principle VII): All data includes source, timestamp, validation
- Append-Only Logging (Constitution Principle VIII): OperationLog immutable
- Graceful Degradation (Constitution Principle X): MarketDataPoint includes cache expiry
- Traceability: Every entity tracks provenance and version information

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│  InvestmentRecord   │
│  (Historical Txns)  │
└─────────────────────┘
          ↓ (aggregates to)
┌─────────────────────┐
│  CurrentHolding     │
│  (Portfolio)        │
└─────────────────────┘


┌─────────────────────┐
│  MarketDataPoint    │
│  (OHLCV + Metadata) │
└─────────────────────┘
          ↓ (feeds into)
┌──────────────────────────┐
│  InvestmentRecommendation│
│  (AI Suggestions)        │
└──────────────────────────┘
          ↓ (executed as)
┌─────────────────────┐
│  OperationLog       │
│  (Audit Trail)      │
└─────────────────────┘
          ↓ (updates)
┌─────────────────────┐
│  CurrentHolding     │
│  (Portfolio)        │
└─────────────────────┘
```

---

## 1. InvestmentRecord

**Purpose**: Store historical investment transactions (manual entry or CSV import)

**SQLAlchemy Model**:

```python
from sqlalchemy import String, Float, Date, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from typing import Optional
import enum

class DataSource(enum.Enum):
    MANUAL_ENTRY = "manual_entry"
    BROKER_STATEMENT = "broker_statement"
    API_IMPORT = "api_import"

class InvestmentRecord(Base):
    __tablename__ = "investment_records"

    # Primary key
    record_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Investment details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    purchase_amount: Mapped[float] = mapped_column(Float, nullable=False)  # Capital invested
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional sale information
    sale_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sale_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Data integrity fields (Constitution Principle VII)
    data_source: Mapped[DataSource] = mapped_column(Enum(DataSource), nullable=False)
    ingestion_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Field Descriptions**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| record_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| symbol | VARCHAR(20) | NOT NULL, INDEX | Stock/futures code (e.g., "600519.SH") |
| purchase_amount | FLOAT | NOT NULL, >0 | Capital invested (purchase_price * quantity) |
| purchase_price | FLOAT | NOT NULL, >0 | Price per share/contract |
| purchase_date | DATE | NOT NULL, <=TODAY, INDEX | Transaction date |
| quantity | FLOAT | NOT NULL, >0 | Number of shares/contracts |
| sale_date | DATE | NULL, >=purchase_date | Sale date (if sold) |
| sale_price | FLOAT | NULL, >0 | Sale price per share (if sold) |
| profit_loss | FLOAT | NULL | Calculated: (sale_price - purchase_price) * quantity |
| data_source | ENUM | NOT NULL | Source of record (manual/broker/api) |
| ingestion_timestamp | DATETIME | NOT NULL | When record was imported (ISO 8601) |
| checksum | VARCHAR(64) | NOT NULL | SHA256 hash for validation |

**Validation Rules**:
1. `purchase_price > 0`
2. `quantity > 0`
3. `purchase_date <= TODAY`
4. `sale_date IS NULL OR sale_date >= purchase_date`
5. `sale_price IS NULL OR sale_price > 0`
6. `symbol MATCHES /^[0-9]{6}\.(SH|SZ|HK)$/` (Chinese stock format)
7. `checksum = SHA256(symbol + purchase_date + purchase_price + quantity)`

**Indexes**:
- `idx_symbol` on `symbol` (for holdings aggregation)
- `idx_purchase_date` on `purchase_date` (for timeline queries)

**State Transitions**:
- **CREATED** → record imported/created
- **SOLD** → sale_date, sale_price, profit_loss populated
- No DELETE (soft delete via is_active flag if needed in future)

---

## 2. MarketDataPoint

**Purpose**: Store market data from APIs with 7-day cache retention for graceful degradation

**SQLAlchemy Model**:

```python
from datetime import datetime, timedelta

class DataFreshness(enum.Enum):
    REALTIME = "realtime"       # <5s delay
    DELAYED = "delayed"         # 5s-15min delay
    HISTORICAL = "historical"   # >15min delay

class AdjustmentMethod(enum.Enum):
    FORWARD = "forward"         # 前复权
    BACKWARD = "backward"       # 后复权
    UNADJUSTED = "unadjusted"   # 不复权

class MarketDataPoint(Base):
    __tablename__ = "market_data"

    # Composite primary key
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)

    # OHLCV data
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)

    # Data integrity fields (Constitution Principle VII)
    api_source: Mapped[str] = mapped_column(String(50), nullable=False)  # "Tushare v1.2.85"
    api_version: Mapped[str] = mapped_column(String(20), nullable=False)
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    data_freshness: Mapped[DataFreshness] = mapped_column(Enum(DataFreshness), nullable=False)
    adjustment_method: Mapped[AdjustmentMethod] = mapped_column(Enum(AdjustmentMethod), nullable=False)

    # 7-day cache expiry (Constitution Clarification)
    cache_expiry_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=7),
        nullable=False,
        index=True
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
```

**Field Descriptions**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| symbol | VARCHAR(20) | PRIMARY KEY | Stock/futures code |
| timestamp | DATETIME | PRIMARY KEY | Market data timestamp (daily close for v0.1) |
| open_price | FLOAT | NOT NULL, >0 | Opening price |
| high_price | FLOAT | NOT NULL, >=open_price | Highest price |
| low_price | FLOAT | NOT NULL, <=open_price | Lowest price |
| close_price | FLOAT | NOT NULL, >0 | Closing price |
| volume | FLOAT | NOT NULL, >=0 | Trading volume |
| api_source | VARCHAR(50) | NOT NULL | API name + version (e.g., "Tushare v1.2.85") |
| api_version | VARCHAR(20) | NOT NULL | Semantic version |
| retrieval_timestamp | DATETIME | NOT NULL | When data was fetched (ISO 8601) |
| data_freshness | ENUM | NOT NULL | realtime/delayed/historical |
| adjustment_method | ENUM | NOT NULL | forward/backward/unadjusted |
| cache_expiry_date | DATETIME | NOT NULL, INDEX | retrieval_timestamp + 7 days |

**Validation Rules**:
1. `open_price > 0, high_price > 0, low_price > 0, close_price > 0`
2. `high_price >= low_price`
3. `high_price >= open_price AND high_price >= close_price`
4. `low_price <= open_price AND low_price <= close_price`
5. `volume >= 0`
6. `cache_expiry_date = retrieval_timestamp + 7 days`

**Indexes**:
- Composite primary key: `(symbol, timestamp)`
- `idx_cache_expiry` on `cache_expiry_date` (for cleanup queries)

**Cache Management**:
- Daily cleanup job: `DELETE WHERE cache_expiry_date < NOW()`
- Graceful degradation: If API fails, query cache for most recent data
- Display warning if `data_freshness == HISTORICAL` or cache data used

---

## 3. InvestmentRecommendation

**Purpose**: Store AI-generated investment suggestions with full traceability

**SQLAlchemy Model**:

```python
from uuid import uuid4

class RecommendationAction(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class Confidence(enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class InvestmentRecommendation(Base):
    __tablename__ = "investment_recommendations"

    # Primary key
    recommendation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Recommendation details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    action: Mapped[RecommendationAction] = mapped_column(Enum(RecommendationAction), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)  # MANDATORY (Constitution)
    take_profit: Mapped[float] = mapped_column(Float, nullable=False)
    position_size_pct: Mapped[float] = mapped_column(Float, nullable=False)  # % of total capital
    max_loss_amount: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)

    # AI Advisor metadata (Constitution Principle IX)
    advisor_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Livermore"
    advisor_version: Mapped[str] = mapped_column(String(20), nullable=False)  # "v1.0.0"
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "Trend Following"

    # Explainability (Constitution Principle IX)
    reasoning: Mapped[str] = mapped_column(String(1000), nullable=False)  # Why this recommendation
    confidence: Mapped[Confidence] = mapped_column(Enum(Confidence), nullable=False)
    key_factors: Mapped[str] = mapped_column(String(500), nullable=False)  # JSON array
    historical_precedents: Mapped[str] = mapped_column(String(1000), nullable=True)  # JSON array

    # Data provenance (Constitution Principle VII)
    market_data_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)  # "Tushare v1.2.85"

    # Audit
    created_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

**Field Descriptions**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| recommendation_id | VARCHAR(36) | PRIMARY KEY, UUID | Unique identifier |
| symbol | VARCHAR(20) | NOT NULL, INDEX | Stock symbol |
| action | ENUM | NOT NULL | BUY/SELL/HOLD |
| entry_price | FLOAT | NOT NULL, >0 | Recommended entry price |
| stop_loss | FLOAT | NOT NULL, >0 | **MANDATORY** stop-loss price |
| take_profit | FLOAT | NOT NULL, >0 | Target take-profit price |
| position_size_pct | FLOAT | NOT NULL, 0-100 | Position size as % of capital |
| max_loss_amount | FLOAT | NOT NULL, >0 | Maximum loss in base currency |
| expected_return_pct | FLOAT | NOT NULL | Expected return percentage |
| advisor_name | VARCHAR(50) | NOT NULL | Name of AI advisor |
| advisor_version | VARCHAR(20) | NOT NULL | Semantic version of advisor |
| strategy_name | VARCHAR(50) | NOT NULL | Strategy name |
| reasoning | VARCHAR(1000) | NOT NULL | Explanation text |
| confidence | ENUM | NOT NULL | HIGH/MEDIUM/LOW |
| key_factors | VARCHAR(500) | NOT NULL | JSON array of factors |
| historical_precedents | VARCHAR(1000) | NULL | JSON array of similar cases |
| market_data_timestamp | DATETIME | NOT NULL | Timestamp of market data used |
| data_source | VARCHAR(50) | NOT NULL | API source used |

**Validation Rules**:
1. `stop_loss IS NOT NULL` (backend validation, Constitution Principle VIII)
2. For BUY: `stop_loss < entry_price`
3. For SELL: `stop_loss > entry_price`
4. `position_size_pct >= 0 AND position_size_pct <= 20` (configurable limit)
5. `max_loss_amount = position_size_pct * capital * abs(entry_price - stop_loss) / entry_price`
6. `confidence IN ('HIGH', 'MEDIUM', 'LOW')`

**Indexes**:
- `idx_symbol` on `symbol`
- `idx_created_timestamp` on `created_timestamp` (for "Today's Recommendations")

**JSON Field Schemas**:

**key_factors** (JSON array):
```json
["Price broke above 120-day MA", "Volume spike +30%", "MACD golden cross"]
```

**historical_precedents** (JSON array):
```json
[
  {"date": "2023-03-15", "pattern": "Similar breakout", "outcome": "+12% in 15 days"},
  {"date": "2022-11-08", "pattern": "MA breakout", "outcome": "+8% in 10 days"}
]
```

---

## 4. OperationLog

**Purpose**: Immutable audit trail of all investment operations (Constitution Principle VIII)

**SQLAlchemy Model**:

```python
class OperationType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    MODIFY = "MODIFY"
    CANCEL = "CANCEL"

class ExecutionStatus(enum.Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"

class ExecutionMode(enum.Enum):
    SIMULATED = "SIMULATED"
    LIVE = "LIVE"  # v0.2+

class OperationLog(Base):
    __tablename__ = "operation_log"

    # Prevent updates/deletes at ORM level (append-only)
    __mapper_args__ = {"confirm_deleted_rows": False}

    # Primary key
    operation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Immutable timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # User and operation details
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, default="default_user")
    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Traceability (Constitution Principle IX)
    original_recommendation: Mapped[str] = mapped_column(String(2000), nullable=False)  # JSON
    user_modification: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # JSON

    # Execution details
    execution_status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), nullable=False)
    execution_mode: Mapped[ExecutionMode] = mapped_column(Enum(ExecutionMode), nullable=False, default=ExecutionMode.SIMULATED)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Foreign key to recommendation
    recommendation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # UUID

    # NO updated_at field (append-only)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
```

**Field Descriptions**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| operation_id | VARCHAR(36) | PRIMARY KEY, UUID | Unique operation identifier |
| timestamp | DATETIME | NOT NULL, IMMUTABLE, INDEX | Operation timestamp (ISO 8601) |
| user_id | VARCHAR(50) | NOT NULL | User identifier (default_user for v0.1) |
| operation_type | ENUM | NOT NULL | BUY/SELL/MODIFY/CANCEL |
| symbol | VARCHAR(20) | NOT NULL, INDEX | Stock symbol |
| original_recommendation | VARCHAR(2000) | NOT NULL | Full recommendation JSON |
| user_modification | VARCHAR(1000) | NULL | User's changes JSON |
| execution_status | ENUM | NOT NULL | PENDING/EXECUTED/CANCELLED |
| execution_mode | ENUM | NOT NULL | SIMULATED/LIVE |
| notes | VARCHAR(500) | NULL | User notes |
| recommendation_id | VARCHAR(36) | NULL | Reference to recommendation |

**Validation Rules**:
1. **Append-Only**: No UPDATE or DELETE allowed (enforced at ORM and DB level)
2. `timestamp` is immutable (set once on insert)
3. `original_recommendation` is valid JSON
4. `user_modification` is NULL or valid JSON

**Indexes**:
- `idx_timestamp` on `timestamp` (for log viewer queries)
- `idx_symbol` on `symbol` (for filtering by stock)

**Append-Only Enforcement**:

At SQLAlchemy level:
```python
@event.listens_for(OperationLog, 'before_update')
def prevent_update(mapper, connection, target):
    raise ValueError("OperationLog is append-only, updates not allowed")

@event.listens_for(OperationLog, 'before_delete')
def prevent_delete(mapper, connection, target):
    raise ValueError("OperationLog is append-only, deletes not allowed")
```

At database level (trigger):
```sql
CREATE TRIGGER prevent_operation_log_update
BEFORE UPDATE ON operation_log
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'OperationLog is append-only');
END;
```

**JSON Field Schemas**:

**original_recommendation**:
```json
{
  "recommendation_id": "uuid",
  "symbol": "600519.SH",
  "action": "BUY",
  "entry_price": 1680.0,
  "stop_loss": 1620.0,
  "take_profit": 1800.0,
  "position_size_pct": 15,
  "max_loss_amount": 9000.0
}
```

**user_modification**:
```json
{
  "modified_fields": ["stop_loss", "position_size_pct"],
  "changes": {
    "stop_loss": {"old": 1620.0, "new": 1640.0},
    "position_size_pct": {"old": 15, "new": 10}
  },
  "reason": "Reduced risk due to volatility"
}
```

---

## 5. CurrentHolding

**Purpose**: Track current portfolio positions (aggregated from InvestmentRecord and OperationLog)

**SQLAlchemy Model**:

```python
class CurrentHolding(Base):
    __tablename__ = "current_holdings"

    # Primary key
    holding_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Holdings details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)  # Average cost
    current_price: Mapped[float] = mapped_column(Float, nullable=False)  # Latest market price

    # Calculated fields
    profit_loss_amount: Mapped[float] = mapped_column(Float, nullable=False)
    profit_loss_pct: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamps
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)  # Initial purchase
    last_update_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Field Descriptions**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| holding_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| symbol | VARCHAR(20) | NOT NULL, UNIQUE, INDEX | Stock symbol |
| quantity | FLOAT | NOT NULL, >0 | Total shares held |
| purchase_price | FLOAT | NOT NULL, >0 | Average cost per share |
| current_price | FLOAT | NOT NULL, >0 | Latest market price |
| profit_loss_amount | FLOAT | NOT NULL | (current_price - purchase_price) * quantity |
| profit_loss_pct | FLOAT | NOT NULL | (current_price / purchase_price - 1) * 100 |
| purchase_date | DATE | NOT NULL | Initial purchase date |
| last_update_timestamp | DATETIME | NOT NULL | Last price update |

**Validation Rules**:
1. `quantity > 0`
2. `purchase_price > 0`
3. `current_price > 0`
4. `profit_loss_amount = (current_price - purchase_price) * quantity`
5. `profit_loss_pct = ((current_price / purchase_price) - 1) * 100`

**Indexes**:
- `idx_symbol` on `symbol` (unique)

**State Transitions**:
- **CREATED** → New position opened (from OperationLog BUY)
- **UPDATED** → Quantity/price changed (from OperationLog BUY/SELL, or market data update)
- **CLOSED** → Position fully sold (quantity = 0, soft delete or move to archive)

**Aggregation Logic**:

Holdings are calculated from InvestmentRecord and OperationLog:

```sql
-- Calculate current holdings
SELECT
    symbol,
    SUM(quantity) as total_quantity,
    SUM(quantity * purchase_price) / SUM(quantity) as avg_purchase_price
FROM investment_records
WHERE sale_date IS NULL
GROUP BY symbol
HAVING SUM(quantity) > 0;
```

---

## Relationships Between Entities

### Many-to-One

- **OperationLog.recommendation_id** → **InvestmentRecommendation.recommendation_id**
  - Each operation logs which recommendation it executed
  - Nullable (user can manually create operations)

### Implicit Relationships (Query-Based)

- **InvestmentRecord** → **CurrentHolding** (aggregation)
  - Holdings calculated from unsold investment records
  - No foreign key (derived data)

- **MarketDataPoint** → **InvestmentRecommendation** (input data)
  - Market data feeds recommendation generation
  - No foreign key (temporal relationship via timestamp)

---

## Database Schema Summary

| Entity | Table Name | Primary Key | Indexes | Special Constraints |
|--------|-----------|-------------|---------|---------------------|
| InvestmentRecord | investment_records | record_id (INT) | symbol, purchase_date | purchase_price > 0, date <= today |
| MarketDataPoint | market_data | (symbol, timestamp) | cache_expiry_date | OHLC validation, 7-day expiry |
| InvestmentRecommendation | investment_recommendations | recommendation_id (UUID) | symbol, created_timestamp | stop_loss NOT NULL, position <= 20% |
| OperationLog | operation_log | operation_id (UUID) | timestamp, symbol | Append-only (no updates/deletes) |
| CurrentHolding | current_holdings | holding_id (INT) | symbol (UNIQUE) | quantity > 0, P&L calculated |

---

## Migration Strategy

### Initial Migration (Alembic)

```bash
# Create initial schema
alembic revision --autogenerate -m "Initial schema: 5 core entities"
alembic upgrade head
```

**Generated Tables**:
1. `investment_records`
2. `market_data`
3. `investment_recommendations`
4. `operation_log` (with update/delete prevention triggers)
5. `current_holdings`

### Future Migrations (v0.2+)

Planned schema changes:
- Add `user_id` foreign key when multi-user support added
- Add `backtest_results` table when backtesting implemented
- Migrate SQLite → PostgreSQL (no schema changes, just connection string)

---

**Data Model Complete**: All 5 entities defined with schemas, validation rules, and relationships. Proceed to API contracts generation.
