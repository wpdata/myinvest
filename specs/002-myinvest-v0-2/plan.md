# Implementation Plan: MyInvest v0.2 - Multi-Strategy System with Real Market Data Integration

**Branch**: `002-myinvest-v0-2` | **Date**: 2025-10-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/pw/ai/myinvest/specs/002-myinvest-v0-2/spec.md`

---

## Summary

V0.2 transitions MyInvest from prototype to production-ready system by ensuring **100% real market data integration** across all components, implementing a **Kroll risk-focused strategy**, building a **multi-strategy fusion engine**, adding a **historical backtest framework** with 3+ years of real data, and introducing **automated daily recommendation generation** with a strategy approval workflow.

**Primary Requirement**: All strategies, backtests, and recommendations MUST use real Tushare/AKShare data from Day 1 of V0.2.

**Technical Approach**:
1. Refactor existing Livermore strategy to use `MarketDataFetcher.fetch_with_fallback()` for real data
2. Implement Kroll strategy with same data pipeline (MA60, RSI, volume-based signals)
3. Build fusion engine with configurable weights and conflict detection
4. Create `investlib-backtest` library using 3+ years real historical data from Tushare
5. Deploy APScheduler for daily automated runs at 08:30 (after China A-share market close)
6. Add strategy approval workflow to gate live recommendation generation

---

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**:
- Streamlit 1.40+ (Web UI)
- Tushare/AKShare APIs (Market data - primary/fallback)
- APScheduler 3.10+ (Automation)
- pandas_ta or ta-lib (Technical indicators: RSI, ATR, MACD)
- Redis 7+ (Caching with 7-day retention)
- SQLite (Database for V0.2, PostgreSQL-ready migration path)

**Storage**: SQLite with new tables: `strategy_config`, `backtest_results`, `strategy_approval`, `scheduler_log`; Extended tables: `investment_recommendation` (add `data_source`, `data_timestamp`, `data_freshness`, `advisor_weights`, `is_automated`)

**Testing**: pytest 8.0+; All tests must use real API calls (no mocks for data layer); Integration tests with real Tushare/AKShare endpoints

**Target Platform**: Local development (macOS/Linux), Docker-ready for production

**Project Type**: Multi-library architecture (4 existing libraries + 1 new `investlib-backtest`)

**Performance Goals**:
- API response time: <5s for Tushare, <10s for AKShare fallback
- Backtest execution: <2 minutes for 3 years of data (single symbol)
- Scheduler execution: Complete daily recommendations within 10 minutes (08:30-08:40)
- API call success rate: >95% for Tushare primary source

**Constraints**:
- Single user mode only (user_id = "default_user")
- Simulated trading only (no real money at risk)
- Daily data granularity only (no intraday/tick data)
- Backtest limited to 10 symbols max per run (performance constraint)
- API rate limits: Tushare ~200 calls/day, AKShare no limit
- Cache retention: 7 days (expired data auto-deleted)

**Scale/Scope**:
- 5 User Stories (US 5-10)
- 48 Functional Requirements (FR-101 to FR-148)
- 15 Success Criteria (SC-201 to SC-215)
- Target: 20+ integration tests covering real API workflows

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### V0.1 Constitution Principles (Inherited)

✅ **I. Library-First Architecture**
- All business logic in `investlib-*` libraries
- New library: `investlib-backtest` for strategy validation
- Each library is independently testable and CLI-enabled

✅ **II. CLI Interface Mandatory**
- All libraries expose CLI with `--help`, `--dry-run`, JSON output
- Example: `investlib-backtest run --strategy livermore --period 3y --output json`

✅ **III. Test-First Development (NON-NEGOTIABLE)**
- Tests written BEFORE implementation for ALL new features
- Red-Green-Refactor cycle strictly enforced
- Integration tests use real API calls (no mocks for data layer)

✅ **VII. Data Integrity & Provenance**
- ALL data MUST include: `data_source` (Tushare/AKShare/Cache), `data_timestamp`, `data_freshness`
- Append-only logs for all recommendations
- Data validation: no gaps > 5 consecutive trading days

✅ **VIII. Investment Safety Principles**
- Mandatory stop-loss on all recommendations (Kroll: -2.5%, Livermore: -3.5%)
- Strategy approval workflow gates live recommendations
- Simulated trading only (no real money risk)

✅ **X. Graceful Degradation**
- Retry logic: 3 attempts with exponential backoff
- Fallback: Tushare → AKShare → Cache (7-day retention)
- All failure modes tested in integration suite

### V0.2 New Constitution Principles

✅ **XI. Real Data Mandate (NEW - P0 CRITICAL)**
- 100% of production recommendations MUST use real Tushare/AKShare data
- Test fixtures ONLY allowed in unit tests (not integration/contract tests)
- Every recommendation displays data source badge with timestamp

✅ **XII. Backtest Validation Requirement (NEW)**
- All strategies MUST pass 3-year backtest before approval
- Backtest data quality: no gaps > 5 days, qfq adjustment
- Minimum performance thresholds: Sharpe > 1.0, Max Drawdown < 30%

✅ **XIII. Scheduler Reliability (NEW)**
- Daily tasks MUST complete successfully or log detailed errors
- Execution summary logged to `scheduler_log` table
- Health check: alert if no execution in 24 hours

---

## Project Structure

### Documentation (this feature)

```
specs/002-myinvest-v0-2/
├── spec.md              # Feature specification (COMPLETE)
├── plan.md              # This file
├── research.md          # Phase 0: Library research (backtest frameworks)
├── data-model.md        # Phase 1: New tables and schema extensions
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/           # Phase 1: API contracts for new libraries
│   ├── investlib-backtest.md
│   ├── investlib-advisors-kroll.md
│   └── strategy-fusion.md
└── tasks.md             # Phase 2: Generated by /speckit.tasks (NOT in plan phase)
```

### Source Code (repository root)

**Structure Decision**: Multi-library architecture (extends V0.1 structure)

```
myinvest/
├── docker-compose.yml          # Docker orchestration (no changes)
├── .env.example                # Add: APSCHEDULER_TIMEZONE=Asia/Shanghai
├── requirements.txt            # Add: apscheduler, pandas_ta
├── pytest.ini                  # Configure real API tests
│
├── investlib-data/             # [EXISTING - REFACTOR]
│   ├── src/investlib_data/
│   │   ├── api/
│   │   │   └── data_fetcher.py  # REFACTOR: Add logging for data_source, data_timestamp
│   │   ├── models/
│   │   │   ├── market_data.py   # ADD: data_freshness enum (realtime/delayed/historical)
│   │   │   └── investment_recommendation.py  # EXTEND: Add new columns
│   │   └── storage/
│   │       └── db.py            # ADD: New tables (strategy_config, backtest_results, etc.)
│   └── tests/
│       └── test_real_data_integration.py  # NEW: Test real API calls
│
├── investlib-quant/            # [EXISTING - REFACTOR]
│   ├── src/investlib_quant/
│   │   ├── strategies/
│   │   │   └── livermore.py     # REFACTOR: Use MarketDataFetcher, log data_source
│   │   └── indicators/
│   │       ├── __init__.py      # NEW
│   │       ├── rsi.py           # NEW: For Kroll strategy
│   │       ├── atr.py           # NEW: For Kroll strategy
│   │       └── moving_average.py # NEW: MA60, MA120
│   └── tests/
│       └── test_livermore_real_data.py  # NEW: Integration test with real data
│
├── investlib-advisors/         # [EXISTING - EXTEND]
│   ├── src/investlib_advisors/
│   │   ├── agents/
│   │   │   ├── livermore_agent.py  # REFACTOR: Accept data_source metadata
│   │   │   └── kroll_agent.py      # NEW: Kroll advisor implementation
│   │   ├── prompts/
│   │   │   ├── livermore-v1.0.0.md # [EXISTING]
│   │   │   └── kroll-v1.0.0.md     # NEW: Kroll prompt template
│   │   ├── fusion/
│   │   │   ├── __init__.py         # NEW
│   │   │   ├── strategy_fusion.py  # NEW: Multi-strategy fusion engine
│   │   │   └── conflict_detector.py # NEW: Detect advisor disagreements
│   │   └── cli.py                  # EXTEND: Add --advisor kroll option
│   └── tests/
│       ├── test_kroll_agent.py     # NEW
│       └── test_fusion_engine.py   # NEW
│
├── investlib-backtest/         # [NEW LIBRARY]
│   ├── src/investlib_backtest/
│   │   ├── __init__.py
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── backtest_runner.py  # Core backtest engine
│   │   │   └── portfolio.py        # Portfolio state tracking
│   │   ├── metrics/
│   │   │   ├── __init__.py
│   │   │   ├── performance.py      # Calculate returns, drawdown, sharpe
│   │   │   └── trade_analysis.py   # Win rate, profit factor
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── report_generator.py # Generate HTML/JSON reports
│   │   │   └── charts.py           # Equity curve, drawdown charts
│   │   └── cli.py                  # CLI: backtest run/report commands
│   ├── tests/
│   │   ├── test_backtest_engine.py
│   │   ├── test_metrics.py
│   │   └── test_real_data_backtest.py  # Integration test with 3y real data
│   ├── pyproject.toml
│   └── README.md
│
└── investapp/                  # [EXISTING - EXTEND]
    ├── src/investapp/
    │   ├── app.py              # EXTEND: Add backtest page, scheduler status
    │   ├── scheduler/
    │   │   ├── __init__.py     # NEW
    │   │   ├── daily_tasks.py  # NEW: APScheduler job definitions
    │   │   └── health_check.py # NEW: Monitor scheduler health
    │   ├── pages/
    │   │   ├── overview.py     # EXTEND: Show data_source badges
    │   │   ├── recommendations.py # EXTEND: Display Kroll/Livermore/Fused cards
    │   │   ├── backtest.py     # NEW: Backtest UI page
    │   │   ├── approval.py     # NEW: Strategy approval workflow
    │   │   └── scheduler_log.py # NEW: View scheduler execution history
    │   └── components/
    │       ├── data_source_badge.py    # NEW: Display data provenance
    │       ├── fusion_card.py          # NEW: Show multi-strategy results
    │       └── conflict_warning.py     # NEW: Highlight advisor disagreements
    └── tests/
        ├── test_scheduler.py           # NEW
        └── test_approval_workflow.py   # NEW
```

---

## Architecture Overview

### High-Level Architecture for V0.2

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit Web UI                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │ Overview │ │ Recommend│ │ Backtest │ │ Approval │ │Scheduler││
│  │  Page    │ │   Page   │ │   Page   │ │  Page    │ │  Log   ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘│
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   investapp (Orchestrator)                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ APScheduler (Daily 08:30)                                  │ │
│  │  → Fetch real data → Generate recommendations → Save DB   │ │
│  └───────────────────────────────────────────────────────────┘ │
└───────┬──────────┬──────────┬──────────┬──────────────────────┘
        │          │          │          │
    ┌───▼──────┐ ┌▼────────┐ ┌▼───────┐ ┌▼──────────┐
    │investlib-│ │investlib-│ │investlib│ │investlib- │
    │data      │ │quant     │ │advisors │ │backtest   │
    │          │ │          │ │         │ │   [NEW]   │
    │• Tushare │ │• Livermore│ │• Livermore│ │• Engine  │
    │  Fetcher │ │  Strategy│ │  Agent  │ │• Metrics │
    │• AKShare │ │• Kroll   │ │• Kroll  │ │• Reports │
    │  Fallback│ │  Strategy│ │  Agent  │ │          │
    │• Data    │ │• Fusion  │ │• Fusion │ │          │
    │  Logging │ │  Engine  │ │  Engine │ │          │
    └──────────┘ └──────────┘ └─────────┘ └───────────┘
        │                                      │
        │                                      │ (3y data)
        ▼                                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    Data & Storage Layer                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │  SQLite DB     │  │  Redis Cache   │  │  Tushare/      │ │
│  │  • strategy_   │  │  • 7-day TTL   │  │  AKShare APIs  │ │
│  │    config      │  │  • Market data │  │  (Real Data)   │ │
│  │  • backtest_   │  │  • Fallback    │  │                │ │
│  │    results     │  │    on failure  │  │                │ │
│  │  • approval    │  │                │  │                │ │
│  │  • scheduler_  │  │                │  │                │ │
│  │    log         │  │                │  │                │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow: Real Data Integration (P0 Critical Path)

```
User triggers "Generate Recommendations" for 600519.SH
  │
  ▼
investapp/orchestrator/recommendation_flow.py
  │
  ├──> investlib-data/MarketDataFetcher.fetch_with_fallback()
  │      ├─[TRY]──> TushareClient.fetch_daily_data()
  │      │           └─[SUCCESS]─> Returns: {data, metadata: {source: "Tushare v1.2.85", timestamp: "2025-10-16T15:32:00Z"}}
  │      │           └─[FAILURE]─> Retry 3x → Fallback to AKShare
  │      ├─[FALLBACK]─> AKShareClient.fetch_daily_data()
  │      │                └─[SUCCESS]─> Returns: {data, metadata: {source: "AKShare v1.11.0", timestamp: "..."}}
  │      └─[CACHE]──> Redis.get(cache_key) if both APIs fail (within 7-day retention)
  │
  ├──> investlib-quant/LivermoreStrategy.generate_signal(market_data)
  │      └─ Calculates MA120, MACD using real OHLCV
  │         Returns: {action: "BUY", entry: 1680, stop_loss: 1620, confidence: "HIGH"}
  │
  ├──> investlib-quant/KrollStrategy.generate_signal(market_data)
  │      └─ Calculates MA60, RSI(14), ATR using real OHLCV
  │         Returns: {action: "BUY", entry: 1680, stop_loss: 1638, confidence: "MEDIUM"}
  │
  ├──> investlib-advisors/StrategyFusion.combine(livermore_signal, kroll_signal, weights={kroll: 0.6, livermore: 0.4})
  │      └─ Detects agreement → Confidence *= 1.3
  │         Returns: {action: "BUY", position: 14.8%, confidence: "HIGH", advisor_weights: {kroll: 0.6, livermore: 0.4}}
  │
  └──> Save to investment_recommendation table with:
         - data_source: "Tushare v1.2.85"
         - data_timestamp: "2025-10-16T15:32:00Z"
         - data_freshness: "realtime"
         - advisor_weights: {"kroll": 0.6, "livermore": 0.4}
         - is_automated: false
```

---

## Key Design Decisions

### Decision 1: Real Data Integration is P0 (Highest Priority)

**Rationale**: Without real data flowing through the entire system, all other V0.2 features (Kroll strategy, backtest, fusion) are meaningless. This is the foundation for production readiness.

**Implementation**:
- Refactor `investlib-quant/strategies/livermore.py` to call `MarketDataFetcher.fetch_with_fallback()` instead of mock data
- Add `data_source`, `data_timestamp`, `data_freshness` logging at EVERY layer (data → strategy → advisor → recommendation)
- Display data source badges in all UI components
- Write integration tests that verify real API calls (no mocks for data fetcher)

**Verification**:
- Success Criterion SC-201: 100% of recommendations display data source badge
- Success Criterion SC-202: 0 test fixtures used in production pipeline
- Success Criterion SC-203: API fallback success rate > 98%

---

### Decision 2: Kroll Strategy Uses Same Data Pipeline as Livermore

**Rationale**: Consistency and testability. Both strategies must consume identical market data to ensure fair comparison and fusion.

**Implementation**:
- Both advisors call `MarketDataFetcher.fetch_with_fallback()` with same symbol/date range
- Kroll calculates MA60 (vs Livermore MA120), RSI(14), ATR from real OHLCV
- Both strategies return standardized signal format: `{action, entry_price, stop_loss, take_profit, position_size_pct, confidence}`

**Trade-offs**:
- PRO: Consistent data ensures accurate fusion calculations
- PRO: Single data fetch for both strategies (performance optimization)
- CON: Requires minimum 120 days of data for Livermore (MA120) - handled by validation

---

### Decision 3: Backtest Engine Uses 3+ Years Real Historical Data

**Rationale**: Validate strategies across multiple market conditions (bull/bear/sideways) before deploying to live recommendations. 3 years captures sufficient market cycles for Chinese A-shares.

**Implementation**:
- `investlib-backtest` fetches historical data from Tushare using `adj='qfq'` (前复权)
- Data quality validation: reject backtest if gaps > 5 consecutive trading days
- Simulate realistic transaction costs: 0.03% commission + 0.1% slippage
- Generate comprehensive metrics: return, annualized_return, max_drawdown, sharpe_ratio, win_rate

**Target Period**: 2022-01-01 to 2024-12-31 (≈730 trading days)

**Verification**:
- Success Criterion SC-208: Backtest runs successfully on 3-year real data
- Success Criterion SC-209: All required metrics displayed in report
- Success Criterion SC-210: Trade log shows 100% real data timestamps

---

### Decision 4: Scheduler Runs Weekdays at 08:30 (Before Market Open)

**Rationale**: China A-share market closes at 15:00. Allow 30-35 minutes for data settlement on Tushare/AKShare before fetching closing prices.

**Implementation**:
- APScheduler CronTrigger: `"0 35 15 * * mon-fri"` (timezone: Asia/Shanghai)
- Daily task sequence:
  1. Fetch closing data for all watchlist symbols
  2. Generate Kroll + Livermore + Fused recommendations
  3. Save to database with `is_automated=true`
  4. Log execution summary to `scheduler_log` table
- Error handling: Retry 3x with exponential backoff, fallback to AKShare, log failure details

**Verification**:
- Success Criterion SC-211: Scheduler executes successfully for 5 consecutive days
- Success Criterion SC-212: Recommendations generated within 10 minutes (08:30-08:40)

---

### Decision 5: Strategy Approval Workflow Gates Live Recommendations

**Rationale**: Investment safety principle - only validated strategies should generate actionable recommendations. Requires manual review of backtest performance before approval.

**Implementation**:
- New table: `strategy_approval` with status enum: PENDING_APPROVAL | APPROVED | REJECTED
- Automated scheduler only uses strategies with `status="APPROVED"`
- Approval UI displays: backtest metrics, equity curve, trade history, risk assessment
- Immutable approval records (append-only)

**Minimum Approval Criteria** (suggested, not enforced in code):
- Sharpe Ratio > 1.0
- Max Drawdown < 30%
- Win Rate > 50%
- Minimum 30 trades in backtest period

---

## Data Model Extensions

### New Tables for V0.2

#### 1. strategy_config
Stores multi-strategy fusion weights per user.

```sql
CREATE TABLE strategy_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) DEFAULT 'default_user',
    kroll_weight FLOAT CHECK (kroll_weight >= 0 AND kroll_weight <= 1),
    livermore_weight FLOAT CHECK (livermore_weight >= 0 AND livermore_weight <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT weights_sum_one CHECK (kroll_weight + livermore_weight = 1.0)
);
```

**Default Value**: kroll_weight=0.5, livermore_weight=0.5

---

#### 2. backtest_results
Stores complete backtest execution results and metrics.

```sql
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_name VARCHAR(50) CHECK (strategy_name IN ('livermore', 'kroll', 'fused')),
    strategy_version VARCHAR(20) DEFAULT 'v1.0.0',
    symbols TEXT,  -- JSON array: ["600519.SH", "000001.SZ"]
    start_date DATE,
    end_date DATE,
    initial_capital DECIMAL(15,2),
    final_capital DECIMAL(15,2),
    total_return FLOAT,
    annualized_return FLOAT,
    max_drawdown FLOAT,
    sharpe_ratio FLOAT,
    sortino_ratio FLOAT,
    win_rate FLOAT,
    total_trades INT,
    trade_log JSONB,  -- Array of trades: [{date, symbol, action, entry, exit, pnl, data_source}, ...]
    data_source VARCHAR(50),  -- "Tushare v1.2.85"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
```sql
CREATE INDEX idx_backtest_strategy ON backtest_results(strategy_name, strategy_version);
CREATE INDEX idx_backtest_dates ON backtest_results(start_date, end_date);
```

---

#### 3. strategy_approval
Tracks approval status of backtested strategies.

```sql
CREATE TABLE strategy_approval (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id UUID REFERENCES backtest_results(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED')),
    approver_id VARCHAR(255) DEFAULT 'default_user',
    approval_time TIMESTAMP,
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Business Rule**: Approval records are immutable (append-only). To change approval, create new record.

---

#### 4. scheduler_log
Tracks daily automated task execution.

```sql
CREATE TABLE scheduler_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_time TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('SUCCESS', 'FAILURE', 'PARTIAL')),
    symbols_processed INT,
    recommendations_generated INT,
    data_source VARCHAR(50),  -- "Tushare" | "AKShare" | "Cache"
    error_message TEXT,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
```sql
CREATE INDEX idx_scheduler_time ON scheduler_log(execution_time DESC);
CREATE INDEX idx_scheduler_status ON scheduler_log(status);
```

---

### Extended Tables from V0.1

#### investment_recommendation (add columns)

```sql
ALTER TABLE investment_recommendation ADD COLUMN data_source VARCHAR(100);
ALTER TABLE investment_recommendation ADD COLUMN data_timestamp TIMESTAMP;
ALTER TABLE investment_recommendation ADD COLUMN data_freshness VARCHAR(20) CHECK (data_freshness IN ('realtime', 'delayed', 'historical'));
ALTER TABLE investment_recommendation ADD COLUMN advisor_weights JSONB;  -- {"kroll": 0.6, "livermore": 0.4}
ALTER TABLE investment_recommendation ADD COLUMN is_automated BOOLEAN DEFAULT false;
```

**Migration Note**: For existing V0.1 records, set:
- `data_source = 'test_fixture'`
- `data_freshness = 'historical'`
- `advisor_weights = NULL`
- `is_automated = false`

---

## Implementation Phases

### Phase 0: Foundation & Real Data Integration (Week 1) - P0 CRITICAL

**Goal**: Ensure 100% of system components use real Tushare/AKShare data.

**Tasks**:
1. **Refactor investlib-data** (Priority: P0)
   - Add `data_source`, `data_timestamp`, `data_freshness` to `MarketDataFetcher` response
   - Implement data freshness calculation: `<5s = realtime, 5s-15min = delayed, >15min = historical`
   - Add structured logging: `log.info(f"Fetched {symbol} from {source} at {timestamp}")`
   - Test real API calls in `test_real_data_integration.py`

2. **Refactor investlib-quant/livermore.py** (Priority: P0)
   - Replace test data fixtures with `MarketDataFetcher.fetch_with_fallback()` calls
   - Accept `data_source` and `data_timestamp` in signal generation
   - Log data provenance in strategy output
   - Write integration test: `test_livermore_real_data.py` with real Tushare call

3. **Extend investapp UI** (Priority: P1)
   - Create `DataSourceBadge` component to display: "Tushare v1.2.85 | 2025-10-16 15:32"
   - Add data freshness indicator (green=realtime, yellow=delayed, gray=historical)
   - Update recommendation cards to show data metadata

4. **Database migration** (Priority: P1)
   - Add new columns to `investment_recommendation` table
   - Create migration script: `migrations/002_add_data_metadata.sql`
   - Backfill existing records with `data_source='test_fixture'`

**Deliverables**:
- All Livermore recommendations show real data source
- Integration test passes with real API call
- UI displays data source badges

**Success Criteria**:
- SC-201: 100% recommendations display data source
- SC-202: 0 test fixtures in production flow
- SC-203: API fallback success rate > 98%

---

### Phase 1: Kroll Strategy Implementation (Week 1-2)

**Goal**: Implement risk-focused Kroll strategy using same real data pipeline.

**Tasks**:
1. **Implement technical indicators** (Priority: P0)
   - Create `investlib-quant/indicators/rsi.py` - RSI(14) calculation
   - Create `investlib-quant/indicators/atr.py` - ATR calculation
   - Create `investlib-quant/indicators/moving_average.py` - MA60, MA120
   - Unit tests with real market data samples

2. **Implement KrollStrategy** (Priority: P0)
   - Create `investlib-quant/strategies/kroll.py`
   - Entry signal: `price > MA60 AND volume > 1.5x average AND RSI < 70`
   - Position sizing: Max 12% per position
   - Stop-loss: `entry * 0.975` (-2.5%)
   - Take-profit: `entry * 1.05` (+5%)
   - Confidence: HIGH if RSI < 60, MEDIUM if RSI 60-70

3. **Create Kroll Agent** (Priority: P0)
   - Create `investlib-advisors/agents/kroll_agent.py`
   - Create prompt template: `prompts/kroll-v1.0.0.md`
   - Integrate with `KrollStrategy` for signal generation
   - Return standardized recommendation format

4. **CLI integration** (Priority: P1)
   - Extend `investlib-advisors/cli.py`: Add `--advisor kroll` option
   - Support: `investlib-advisors generate --advisor kroll --symbol 600519.SH --output json`

**Deliverables**:
- Kroll strategy generates valid signals with required fields
- Kroll prompt template version-controlled
- CLI command works end-to-end with real data

**Success Criteria**:
- SC-205: Kroll generates valid recommendations (entry, stop, take_profit, position ≤ 12%)

---

### Phase 2: Multi-Strategy Fusion Engine (Week 2)

**Goal**: Build fusion engine to combine Kroll and Livermore with configurable weights.

**Tasks**:
1. **Implement StrategyFusion** (Priority: P0)
   - Create `investlib-advisors/fusion/strategy_fusion.py`
   - Fusion algorithm:
     ```python
     fused_position = (kroll_pos × kroll_weight) + (livermore_pos × livermore_weight)
     fused_stop_loss = (kroll_stop × kroll_weight) + (livermore_stop × livermore_weight)
     ```
   - Confidence adjustment:
     - Both agree (both BUY or both SELL): `confidence *= 1.3`
     - One BUY, one HOLD: `confidence *= 1.0`
     - One BUY, one SELL: `confidence *= 0.5` + flag warning

2. **Implement ConflictDetector** (Priority: P0)
   - Create `investlib-advisors/fusion/conflict_detector.py`
   - Detect conflicts: `|action_kroll - action_livermore| > threshold`
   - Generate warning messages: "⚠️ ADVISOR CONFLICT: Kroll recommends SELL, Livermore recommends BUY"

3. **Strategy config management** (Priority: P1)
   - Create database table: `strategy_config`
   - Implement CRUD operations in `investlib-data/storage/db.py`
   - Default weights: 50% Kroll + 50% Livermore

4. **UI for fusion results** (Priority: P1)
   - Create `investapp/components/fusion_card.py`
   - Display three cards side-by-side: Kroll | Livermore | Fused
   - Show advisor weights on fused card
   - Add weight adjustment sliders (save to `strategy_config`)

**Deliverables**:
- Fusion engine correctly calculates weighted averages
- Conflict detector flags disagreements
- UI displays all three recommendation cards

**Success Criteria**:
- SC-206: Fusion calculates correctly with 60/40, 80/20, 50/50 splits
- SC-207: Conflict warning displayed when Kroll=SELL and Livermore=BUY

---

### Phase 3: Backtest Engine Implementation (Week 2-3)

**Goal**: Build backtest engine using 3+ years of real historical data.

**Tasks**:
1. **Create investlib-backtest library** (Priority: P0)
   - Scaffold new library: `investlib-backtest/`
   - Add dependencies: pandas, numpy, matplotlib
   - Create CLI: `investlib-backtest run --strategy livermore --period 3y`

2. **Implement BacktestRunner** (Priority: P0)
   - Create `engine/backtest_runner.py`
   - Fetch 3 years of real data: `MarketDataFetcher.fetch_historical(symbol, "20220101", "20241231")`
   - Validate data quality: Check gaps > 5 days, reject if invalid
   - Simulate daily signal generation + trade execution
   - Apply transaction costs: 0.03% commission + 0.1% slippage

3. **Implement performance metrics** (Priority: P0)
   - Create `metrics/performance.py`
   - Calculate:
     - Total Return: `(final_capital - initial_capital) / initial_capital`
     - Annualized Return: `(1 + total_return)^(1/years) - 1`
     - Max Drawdown: `max((peak - trough) / peak)`
     - Sharpe Ratio: `mean(returns) / std(returns) * sqrt(252)`
     - Sortino Ratio: Similar to Sharpe but only downside deviation
   - Calculate:
     - Win Rate: `winning_trades / total_trades`
     - Profit Factor: `sum(winning_pnl) / abs(sum(losing_pnl))`

4. **Implement report generation** (Priority: P1)
   - Create `reports/report_generator.py`
   - Generate equity curve chart (matplotlib/plotly)
   - Generate drawdown chart
   - Export trade log to JSONB
   - Save to `backtest_results` table

5. **Backtest UI page** (Priority: P1)
   - Create `investapp/pages/backtest.py`
   - Input form: strategy, symbols, date range, initial capital
   - Display progress bar during execution
   - Show results: metrics table, equity curve, trade history

**Deliverables**:
- Backtest runs successfully on 3-year real data
- All metrics calculated correctly
- Report displays equity curve and trade log

**Success Criteria**:
- SC-208: Backtest runs on 3 years real data (2022-2024)
- SC-209: Report displays all required metrics
- SC-210: Trade log shows 100% real data timestamps

---

### Phase 4: Automation & Approval Workflow (Week 3)

**Goal**: Implement daily automated scheduler and strategy approval workflow.

**Tasks**:
1. **Implement APScheduler** (Priority: P0)
   - Create `investapp/scheduler/daily_tasks.py`
   - Configure CronTrigger: `"0 35 15 * * mon-fri"` (timezone: Asia/Shanghai)
   - Daily task sequence:
     1. Fetch closing data for all watchlist symbols
     2. Generate Kroll + Livermore + Fused recommendations
     3. Save to database with `is_automated=true`
     4. Log execution summary to `scheduler_log`

2. **Implement error handling** (Priority: P0)
   - Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)
   - Fallback: Tushare → AKShare → Cache
   - Log all failures with error_message and stack trace

3. **Implement health check** (Priority: P1)
   - Create `investapp/scheduler/health_check.py`
   - Check: Last execution time within 24 hours
   - Alert mechanism: Log warning if stale (for now, future: email/SMS)

4. **Strategy approval workflow** (Priority: P1)
   - Create database table: `strategy_approval`
   - Create `investapp/pages/approval.py`
   - Display backtest report with metrics
   - Add approval form: status dropdown, notes textarea
   - Enforce rule: Only APPROVED strategies used in scheduler

5. **Scheduler log UI** (Priority: P2)
   - Create `investapp/pages/scheduler_log.py`
   - Display execution history table
   - Filter by date, status (SUCCESS/FAILURE/PARTIAL)

**Deliverables**:
- Scheduler executes daily at 08:30
- Approval workflow gates live recommendations
- Scheduler log tracks all executions

**Success Criteria**:
- SC-211: Scheduler runs successfully for 5 consecutive days
- SC-212: Recommendations generated within 10 minutes (08:30-08:40)
- SC-213: Scheduler handles API failures gracefully
- SC-214: Only APPROVED strategies generate live recommendations
- SC-215: Approval records are immutable

---

### Phase 5: Testing & Polish (Week 3-4)

**Goal**: Comprehensive testing, documentation, and quality assurance.

**Tasks**:
1. **Integration testing** (Priority: P0)
   - Test real API calls in all layers (data → strategy → advisor → recommendation)
   - Test API fallback: Tushare fails → AKShare succeeds
   - Test cache fallback: Both APIs fail → Cache within 7 days
   - Test scheduler execution: Mock clock to trigger at 08:30

2. **End-to-end testing** (Priority: P0)
   - Test user journey 1: Generate recommendation → Display data source badge
   - Test user journey 2: Run backtest → Submit for approval → Approve → Scheduler uses strategy
   - Test user journey 3: Adjust fusion weights → Generate recommendations → Verify weighted averages

3. **Performance testing** (Priority: P1)
   - Backtest performance: 3-year data should complete in <2 minutes
   - Scheduler performance: Daily task completes in <10 minutes
   - API response time: Tushare <5s, AKShare <10s

4. **Documentation** (Priority: P1)
   - Update README.md with V0.2 features
   - Create `docs/KROLL_STRATEGY.md` explaining Kroll logic
   - Create `docs/BACKTEST_GUIDE.md` for running backtests
   - Create `docs/SCHEDULER_SETUP.md` for configuring automation

5. **Code quality** (Priority: P1)
   - Run linter: `ruff check .`
   - Run type checker: `mypy investlib-*`
   - Verify test coverage: >80% for new code

**Deliverables**:
- All integration tests pass
- Performance benchmarks met
- Documentation complete

**Success Criteria**: All 15 success criteria (SC-201 to SC-215) verified

---

## Testing Strategy

### Test Pyramid for V0.2

```
            /\
           /  \
          / E2E \ (5 tests)
         /______\
        /        \
       / Integr.  \ (20+ tests)
      /____________\
     /              \
    /   Unit Tests   \ (100+ tests)
   /____________________\
```

### Unit Tests (investlib-* libraries)

**Coverage Target**: >80% for all new code

**Key Test Files**:
- `investlib-quant/tests/test_kroll.py` - Test Kroll signal generation with synthetic data
- `investlib-backtest/tests/test_metrics.py` - Test metric calculations (sharpe, drawdown)
- `investlib-advisors/tests/test_fusion_engine.py` - Test weighted averages, conflict detection

**Example Unit Test**:
```python
def test_kroll_buy_signal():
    """Test Kroll generates BUY signal when price > MA60, volume > 1.5x, RSI < 70"""
    market_data = create_test_data(
        close_prices=[100, 102, 105, 110],  # Price breaks above MA60=108
        volumes=[1000, 1000, 1000, 1800],   # Volume surge 1.8x
        ma60=108,
        rsi=65
    )
    strategy = KrollStrategy()
    signal = strategy.generate_signal(market_data)

    assert signal['action'] == 'BUY'
    assert signal['entry_price'] == 110
    assert signal['stop_loss'] == 107.25  # 110 * 0.975
    assert signal['position_size_pct'] == 12
```

---

### Integration Tests (Real API Calls)

**Coverage Target**: 100% of critical data flows

**Key Test Files**:
- `investlib-data/tests/test_real_data_integration.py` - Test Tushare → AKShare fallback
- `investlib-quant/tests/test_livermore_real_data.py` - Test Livermore with real data
- `investlib-backtest/tests/test_real_data_backtest.py` - Test 3-year backtest with real data

**Example Integration Test**:
```python
@pytest.mark.integration
def test_real_data_fallback():
    """Test API fallback: Tushare fails → AKShare succeeds"""
    fetcher = MarketDataFetcher(
        tushare_token="INVALID_TOKEN",  # Force Tushare to fail
        redis_client=get_redis_client()
    )

    data = fetcher.fetch_with_fallback(
        symbol="600519.SH",
        start_date="20250101",
        end_date="20250110"
    )

    assert data is not None
    assert data['metadata']['source'] == "AKShare v1.11.0"
    assert 'data_timestamp' in data['metadata']
```

**CI Configuration** (pytest.ini):
```ini
[pytest]
markers =
    integration: Real API calls (run with --run-integration flag)
    slow: Tests taking >10 seconds
```

Run integration tests:
```bash
pytest --run-integration -v
```

---

### End-to-End Tests (User Journeys)

**Coverage Target**: 5 critical user flows

**Test Scenarios**:
1. **E2E Test 1: Generate Recommendation with Real Data**
   - User clicks "Generate Recommendations" for 600519.SH
   - System fetches from Tushare → Returns real data
   - Livermore + Kroll analyze → Generate signals
   - Fusion combines → Display 3 cards with data source badges

2. **E2E Test 2: Backtest → Approval → Scheduler**
   - User runs backtest for Livermore (3 years)
   - User submits for approval → Status = PENDING_APPROVAL
   - User approves → Status = APPROVED
   - Scheduler runs at 08:30 → Uses approved strategy

3. **E2E Test 3: API Failure Handling**
   - Mock Tushare to return 429 (rate limit)
   - System retries 3x → Falls back to AKShare
   - Recommendation generated with data_source="AKShare"
   - Warning displayed: "Using AKShare fallback"

4. **E2E Test 4: Fusion Weight Adjustment**
   - User sets weights to 80% Kroll + 20% Livermore
   - User generates recommendations
   - Verify fused position = (12% × 0.8) + (20% × 0.2) = 13.6%

5. **E2E Test 5: Conflict Detection**
   - Kroll returns SELL signal
   - Livermore returns BUY signal
   - Fusion detects conflict → Confidence *= 0.5
   - UI displays warning: "⚠️ ADVISOR CONFLICT"

---

## Success Criteria (V0.2 Complete)

### Real Data Integration (P0)
- ✅ SC-201: 100% of live recommendations display data source badge (e.g., "Tushare v1.2.85 | 2025-10-16 15:32")
- ✅ SC-202: 0 test fixtures used in production recommendation pipeline
- ✅ SC-203: API fallback success rate > 98% (when Tushare fails, AKShare succeeds within 5s)
- ✅ SC-204: Data freshness correctly displayed: <5s = realtime (green), 5s-15min = delayed (yellow), >15min = historical (gray)

### Strategy Performance
- ✅ SC-205: Kroll strategy generates valid recommendations with required fields (entry, stop_loss, take_profit, position ≤ 12%)
- ✅ SC-206: Multi-strategy fusion correctly calculates weighted averages (test with 60/40, 80/20, 50/50 splits)
- ✅ SC-207: Conflict detection works: when Kroll=SELL and Livermore=BUY, system displays warning

### Backtest Validation
- ✅ SC-208: Backtest engine successfully runs 3-year test (2022-2024) using real Tushare data
- ✅ SC-209: Backtest report displays all required metrics (return, drawdown, sharpe, win_rate)
- ✅ SC-210: Trade log shows 100% real data timestamps (no synthetic/mock timestamps)

### Automation
- ✅ SC-211: Scheduler executes successfully for 5 consecutive days without manual intervention
- ✅ SC-212: Daily recommendations are generated within 10 minutes of market close (08:30-08:40)
- ✅ SC-213: Scheduler handles API failures gracefully (logs error, retries with fallback, continues execution)

### Approval Workflow
- ✅ SC-214: Only APPROVED strategies generate live recommendations (test by submitting unapproved strategy)
- ✅ SC-215: Approval records are immutable (append-only, cannot be modified after creation)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Tushare API quota exhausted** | High | Medium | Implement aggressive caching (7 days), use AKShare fallback, monitor daily quota usage via dashboard |
| **Historical data gaps (> 5 days)** | High | Medium | Pre-validate data completeness before backtest, reject if gaps > 5 days, log warnings, provide data quality report |
| **Strategy overfitting on 3-year data** | High | High | Use walk-forward validation, test on out-of-sample period (2025 data), require backtest to pass in 3+ market conditions (bull/bear/sideways) |
| **Scheduler fails silently** | Medium | Medium | Add health check endpoint, log all executions to `scheduler_log`, send alert if no execution in 24 hours |
| **Real data reveals strategy flaws** | High | High | Start with paper trading only, require manual review of all signals, implement kill switch to pause scheduler |
| **APScheduler not running (process died)** | Medium | Low | Use process supervisor (systemd/supervisord), add startup script to launch scheduler, health check pings external monitor |
| **Fusion weights not summing to 1.0** | Low | Low | Database CHECK constraint enforces sum=1.0, UI sliders automatically adjust complementary weight |
| **Approval workflow bypassed** | Medium | Low | Enforce at database level: scheduled task query filters `WHERE status='APPROVED'`, log all strategy executions with approval_id |

---

## Complexity Tracking

*No constitution violations requiring justification.*

All design decisions align with established principles:
- Library-first architecture maintained (4 existing + 1 new library)
- CLI interface provided for all libraries
- Test-first development enforced
- Data integrity tracked at all layers
- Investment safety principles upheld (mandatory stop-loss, approval workflow)

---

## Appendix: Key Functional Requirements Reference

### Real Data Integration (FR-101 to FR-134)
- FR-101: Livermore strategy MUST call `MarketDataFetcher.fetch_with_fallback()` for real data
- FR-102: Kroll strategy MUST use same real data pipeline
- FR-103: All strategy analysis MUST log data source (Tushare/AKShare/Cache) and timestamp
- FR-104: Dashboard MUST display data freshness indicator for every recommendation
- FR-105: System MUST track API call success rate (target: >95% for Tushare)
- FR-130 to FR-134: Data source tracking, freshness calculation, cache retention, API monitoring

### Strategy Implementation (FR-106 to FR-138)
- FR-106 to FR-110: Kroll strategy requirements (real data, indicators, stop-loss, versioning)
- FR-135 to FR-138: Prompt versioning, signal generation, position sizing, execution logging

### Backtest Engine (FR-116 to FR-143)
- FR-116 to FR-120: Backtest data requirements (real data, completeness validation, trade logging)
- FR-139 to FR-143: Data quality, transaction costs, performance metrics

### Automated Scheduler (FR-121 to FR-148)
- FR-121 to FR-125: Scheduler configuration, data fetching, metadata tracking, error handling, execution logging
- FR-144 to FR-148: Timing, watchlist processing, recommendation generation, failure handling, log persistence

---

**Document Version**: v1.0
**Created**: 2025-10-16
**Status**: ✅ Ready for Phase 0 Research
**Next Step**: Run `/speckit.plan` to generate research.md, data-model.md, contracts/
