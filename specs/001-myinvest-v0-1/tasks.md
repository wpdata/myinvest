# Implementation Tasks: MyInvest v0.1

**Feature Branch**: `001-myinvest-v0-1`
**Created**: 2025-10-14
**Status**: Ready for Implementation
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Overview

This document defines the implementation tasks for MyInvest v0.1, organized by user story to enable independent, incremental delivery. Each user story is a complete, independently testable feature increment.

**Key Principles**:
- **Test-First**: All tests written and approved BEFORE implementation (Constitution Principle III - NON-NEGOTIABLE)
- **Library-First**: All business logic in investlib-* libraries (Constitution Principle I)
- **Independent Stories**: Each user story can be implemented and tested independently
- **Incremental Delivery**: P1 → P2 → P3 → P4 delivery sequence
- **Parallel Execution**: Tasks marked [P] can run in parallel

**Total Tasks**: 78 tasks across 4 user stories + setup + polish

## Task Organization

- **Phase 1: Setup & Infrastructure** (T001-T008) - Project initialization, shared configuration
- **Phase 2: Foundational Prerequisites** (T009-T020) - Database schema, base libraries (BLOCKING for all stories)
- **Phase 3: User Story 1 (P1)** (T021-T035) - Import and View Investment History
- **Phase 4: User Story 2 (P2)** (T036-T051) - Investment Recommendations
- **Phase 5: User Story 3 (P3)** (T052-T063) - Simulated Trading
- **Phase 6: User Story 4 (P4)** (T064-T073) - Market Data Visualization
- **Phase 7: Polish & Integration** (T074-T078) - Cross-cutting concerns

---

## Phase 1: Setup & Infrastructure

**Goal**: Initialize project structure, dependencies, and shared configuration

**Duration Estimate**: 2-3 hours

### [X] T001 [P] - Create Project Directory Structure

**Story**: Setup
**Files**: Root directory structure
**Action**: Create all directories per plan.md structure:
```bash
mkdir -p investlib-data/investlib_data investlib-data/tests/{contract,integration}
mkdir -p investlib-quant/investlib_quant investlib-quant/tests/{contract,integration}
mkdir -p investlib-advisors/investlib_advisors/prompts investlib-advisors/tests/{contract,integration}
mkdir -p investapp/investapp/{pages,components} investapp/tests/integration
mkdir -p tests/integration data/cache
```

### [X] T002 [P] - Create Top-Level Configuration Files

**Story**: Setup
**Files**: `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
**Action**:
1. Create `requirements.txt` with dependencies:
   ```
   streamlit>=1.28.0
   tushare>=1.2.85
   akshare>=1.11.0
   plotly>=5.17.0
   pandas>=2.1.0
   sqlalchemy>=2.0.0
   click>=8.1.0
   pytest>=7.4.0
   pytest-cov>=4.1.0
   python-dotenv>=1.0.0
   ```
2. Create `.env.example`:
   ```
   TUSHARE_TOKEN=your_token_here
   DATABASE_URL=sqlite:///data/myinvest.db
   CACHE_DIR=data/cache
   ```
3. Create `.gitignore` (exclude .env, data/, __pycache__, *.pyc)
4. Create basic README.md with project description

### [X] T003 [P] - Create investlib-data Package Setup

**Story**: Setup
**Files**: `investlib-data/setup.py`, `investlib-data/README.md`, `investlib-data/investlib_data/__init__.py`
**Action**:
1. Create `setup.py` with package metadata, dependencies (sqlalchemy, pandas, click)
2. Create README with library description and CLI examples
3. Create `__init__.py` with version `__version__ = "0.1.0"`

### [X] T004 [P] - Create investlib-quant Package Setup

**Story**: Setup
**Files**: `investlib-quant/setup.py`, `investlib-quant/README.md`, `investlib-quant/investlib_quant/__init__.py`
**Action**:
1. Create `setup.py` with dependencies (pandas, pandas_ta, numpy)
2. Create README with strategy description
3. Create `__init__.py` with version

### [X] T005 [P] - Create investlib-advisors Package Setup

**Story**: Setup
**Files**: `investlib-advisors/setup.py`, `investlib-advisors/README.md`, `investlib-advisors/investlib_advisors/__init__.py`
**Action**:
1. Create `setup.py` with minimal dependencies
2. Create README with advisor architecture description
3. Create `__init__.py` with version

### [X] T006 [P] - Create investapp Package Setup

**Story**: Setup
**Files**: `investapp/requirements.txt`, `investapp/README.md`, `investapp/investapp/__init__.py`
**Action**:
1. Create `requirements.txt` referencing local investlib-* packages
2. Create README with setup and launch instructions
3. Create `__init__.py` with version

### [X] T007 - Create investapp Configuration

**Story**: Setup
**Files**: `investapp/investapp/config.py`
**Action**:
1. Load environment variables (TUSHARE_TOKEN, DATABASE_URL, CACHE_DIR)
2. Define constants (MAX_POSITION_SIZE_PCT=20, CACHE_RETENTION_DAYS=7)
3. Streamlit page config (title, icon, layout)

### [X] T008 - Verify Setup and Dependencies

**Story**: Setup
**Files**: All setup files
**Action**:
1. Run `pip install -r requirements.txt`
2. Run `pip install -e investlib-data -e investlib-quant -e investlib-advisors`
3. Verify all imports work
4. Verify .env.example can be copied to .env
**Checkpoint**: ✅ Project structure initialized, all dependencies installed

---

## Phase 2: Foundational Prerequisites (BLOCKING)

**Goal**: Implement shared database schema and base library infrastructure required by ALL user stories

**Duration Estimate**: 1 day

**Note**: These tasks MUST complete before any user story implementation begins

### [X] T009 - Write Contract Tests for investlib-data CLI

**Story**: Foundation | **Test-First**: ✅ RED PHASE
**Files**: `investlib-data/tests/contract/test_cli.py`
**Action**:
1. Test `investlib-data --help` returns usage
2. Test `investlib-data init-db --help` shows init-db help
3. Test `investlib-data init-db --dry-run` shows preview
4. Test CLI exits with code 0 on success, 1 on error
**Expected**: Tests FAIL (commands don't exist yet)

### [X] T010 - Create Database Models (All 5 Entities)

**Story**: Foundation
**Files**: `investlib-data/investlib_data/models.py`
**Action**:
1. Implement all 5 SQLAlchemy models from data-model.md:
   - InvestmentRecord
   - MarketDataPoint (with 7-day cache_expiry)
   - InvestmentRecommendation
   - OperationLog (with append-only enforcement)
   - CurrentHolding
2. Add validation methods for each model
3. Add `__repr__` for debugging
**Depends**: T009 (tests written first)

### [X] T011 - Create Database Initialization CLI

**Story**: Foundation
**Files**: `investlib-data/investlib_data/cli.py`
**Action**:
1. Implement Click CLI with `init-db` command
2. Create all tables using SQLAlchemy models
3. Add triggers for OperationLog append-only enforcement
4. Support `--dry-run` flag
5. Add `--help` documentation
**Depends**: T010
**Validates**: T009 (tests should now PASS)

### [X] T012 [P] - Write Integration Tests for Database Init

**Story**: Foundation | **Test-First**: ✅ GREEN PHASE
**Files**: `investlib-data/tests/integration/test_database_init.py`
**Action**:
1. Test database creation with init-db command
2. Test all 5 tables exist with correct schema
3. Test OperationLog triggers prevent updates/deletes
4. Use in-memory SQLite (sqlite:///:memory:) for speed
**Depends**: T011
**Expected**: Tests PASS (validates T010-T011 implementation)

### [X] T013 - Create Tushare API Wrapper

**Story**: Foundation
**Files**: `investlib-data/investlib_data/market_api.py`
**Action**:
1. Implement `TushareClient` class with token from config
2. Method `fetch_daily_data(symbol, start_date, end_date)` → pandas DataFrame
3. Add retry logic (3 attempts with exponential backoff)
4. Return data with metadata (api_source="Tushare v1.2.85", retrieval_timestamp)
5. Raise `TushareAPIError` on failure
**Depends**: T010

### [X] T014 - Create AKShare API Wrapper (Fallback)

**Story**: Foundation
**Files**: `investlib-data/investlib_data/market_api.py` (add `AKShareClient` class)
**Action**:
1. Implement `AKShareClient` class (no token needed)
2. Same interface as TushareClient
3. Return data with metadata (api_source="AKShare v1.11.0")
**Depends**: T013

### [X] T015 - Create Market Data Cache Manager

**Story**: Foundation
**Files**: `investlib-data/investlib_data/cache_manager.py`
**Action**:
1. Implement `CacheManager` class
2. Method `save_to_cache(market_data_points)` → insert into database with 7-day expiry
3. Method `get_from_cache(symbol, date_range)` → query cache, filter by expiry
4. Method `cleanup_expired()` → delete records where cache_expiry_date < now
5. Mark data_freshness as HISTORICAL for cached data
**Depends**: T010, T013

### [X] T016 [P] - Write Integration Tests for Market Data APIs

**Story**: Foundation | **Test-First**: ✅ VALIDATE
**Files**: `investlib-data/tests/integration/test_market_api.py`
**Action**:
1. Test TushareClient fetches real data for 600519.SH (requires API token)
2. Test retry logic (mock API failure, verify 3 retries)
3. Test fallback to AKShare when Tushare fails
4. Test cache saves data with 7-day expiry
5. Test cache retrieval returns valid data within expiry
6. Mark as `@pytest.mark.slow` (real API calls)
**Depends**: T013, T014, T015
**Expected**: Tests PASS (validates API integration)

### [X] T017 - Create Base CLI for investlib-quant

**Story**: Foundation
**Files**: `investlib-quant/investlib_quant/cli.py`
**Action**:
1. Create Click CLI structure
2. Add `--help` command
3. Placeholder for future commands (analyze, signals)
**Depends**: None

### [X] T018 - Create Base CLI for investlib-advisors

**Story**: Foundation
**Files**: `investlib-advisors/investlib_advisors/cli.py`
**Action**:
1. Create Click CLI structure
2. Add `--help` command
3. Add `list-advisors` command → returns ["livermore"]
**Depends**: None

### [X] T019 - Create Livermore Advisor Prompt Template v1.0

**Story**: Foundation
**Files**: `investlib-advisors/investlib_advisors/prompts/livermore-v1.0.md`
**Action**:
1. Create markdown template with strategy rules from research.md:
   - Buy signal: 120-day MA breakout + volume spike + MACD golden cross
   - Stop-loss: 2x ATR below entry
   - Position size: Risk 2% of capital
   - Take-profit: 3x risk (1:3 ratio)
2. Include explanation template structure
3. Document version and creation date
**Depends**: None

### [X] T020 - Verify Foundational Prerequisites Complete

**Story**: Foundation
**Files**: All foundation files
**Action**:
1. Run all contract tests (`pytest investlib-data/tests/contract -v`)
2. Run all integration tests (`pytest tests/integration -v`)
3. Verify database can be initialized
4. Verify market data APIs connect (with token)
5. Verify all CLIs show --help
**Checkpoint**: ✅ Foundation complete, ready for user story implementation

---

## Phase 3: User Story 1 (P1) - Import and View Investment History

**Goal**: Users can import historical investment records and view portfolio performance overview

**Independent Test Criteria**:
- Import CSV with 10+ records → all valid records appear in table
- View dashboard → see total assets, profit/loss curve, asset pie chart, holdings list
- Import invalid data → validation errors displayed, no auto-correction
- Switch curve timeframes → daily/weekly/monthly views work

**Duration Estimate**: 2-3 days

### [X] T021 - Write Contract Tests for CSV Import CLI

**Story**: US1 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-data/tests/contract/test_import_csv_cli.py`
**Action**:
1. Test `investlib-data import-csv --help` shows usage
2. Test `investlib-data import-csv --file data.csv --dry-run` previews import
3. Test `--output json` returns structured output
4. Test missing --file argument returns error code 1
**Expected**: Tests FAIL (command doesn't exist)
**Depends**: T020 (foundation complete)

### [X] T022 - Write Integration Tests for CSV Import Logic

**Story**: US1 | **Test-First**: ✅ GREEN PHASE
**Files**: `investlib-data/tests/integration/test_import_csv.py`
**Action**:
1. Test valid CSV → all records inserted into database
2. Test mixed valid/invalid CSV → valid records inserted, invalid records rejected with specific errors
3. Test duplicate detection → warning displayed
4. Test checksum calculation → SHA256 hash matches
5. Create test fixture CSV files (valid.csv, invalid.csv, mixed.csv)
**Expected**: Tests FAIL (import logic doesn't exist)
**Depends**: T021

### [X] T023 - Implement CSV Import Logic

**Story**: US1
**Files**: `investlib-data/investlib_data/import_csv.py`
**Action**:
1. Create `CSVImporter` class
2. Method `parse_csv(file_path)` → pandas DataFrame with validation
3. Validation: price > 0, quantity > 0, date <= today, valid symbol format
4. Method `save_to_database(records, session)` → insert InvestmentRecord models
5. Calculate checksum: SHA256(symbol + date + price + quantity)
6. Return summary: {imported: N, rejected: M, errors: [list]}
**Depends**: T022
**Validates**: T022 (integration tests should now PASS)

### [X] T024 - Implement CSV Import CLI Command

**Story**: US1
**Files**: `investlib-data/investlib_data/cli.py` (add `import-csv` command)
**Action**:
1. Add Click command `import-csv --file FILE --dry-run --output FORMAT`
2. Call CSVImporter logic
3. Display results (text or JSON format)
4. Return exit code 0 on success, 1 on validation errors
**Depends**: T023
**Validates**: T021 (contract tests should now PASS)

### [X] T025 [P] - Write Integration Tests for Holdings Calculation

**Story**: US1 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-data/tests/integration/test_holdings.py`
**Action**:
1. Test holdings calculation from investment records
2. Test average cost calculation for multiple purchases
3. Test holdings update when new records added
4. Test holdings exclude sold positions
**Expected**: Tests FAIL (holdings logic doesn't exist)
**Depends**: T020

### [X] T026 - Implement Holdings Calculator

**Story**: US1
**Files**: `investlib-data/investlib_data/holdings.py`
**Action**:
1. Create `HoldingsCalculator` class
2. Method `calculate_holdings(session)` → query unsold InvestmentRecords, aggregate by symbol
3. Calculate avg_purchase_price = SUM(quantity * price) / SUM(quantity)
4. Create/update CurrentHolding models
5. Add current_price from latest market data (or 0 if no data)
6. Calculate profit_loss
**Depends**: T025
**Validates**: T025 (tests should now PASS)

### [X] T027 - Write Integration Tests for investapp Dashboard Backend

**Story**: US1 | **Test-First**: ✅ RED PHASE
**Files**: `investapp/tests/integration/test_dashboard_backend.py`
**Action**:
1. Test `get_dashboard_data()` returns total_assets, holdings, profit_loss_history
2. Test empty database → returns zeros/empty lists
3. Test with sample data → correct calculations
**Expected**: Tests FAIL (dashboard backend doesn't exist)
**Depends**: T026

### [X] T028 - Create Dashboard Backend Logic

**Story**: US1
**Files**: `investapp/investapp/components/dashboard_backend.py`
**Action**:
1. Function `get_dashboard_data(session)` → calls investlib-data functions
2. Calculate total_assets from CurrentHolding
3. Get profit_loss_history from InvestmentRecords (daily/weekly/monthly aggregation)
4. Get asset_distribution by symbol
5. Return structured dict
**Depends**: T027
**Validates**: T027 (tests should now PASS)

### [X] T029 - Create Chart Renderer Component

**Story**: US1
**Files**: `investapp/investapp/components/chart_renderer.py`
**Action**:
1. Function `render_profit_loss_curve(data, timeframe)` → Plotly line chart
2. Function `render_asset_distribution(data)` → Plotly pie chart
3. Add Chinese labels and formatting
4. Support daily/weekly/monthly timeframe switching
5. Return Plotly figure objects
**Depends**: T028

### [X] T030 - Create Records Management Page

**Story**: US1
**Files**: `investapp/investapp/pages/2_records.py`
**Action**:
1. Create Streamlit page "Investment Records"
2. Display InvestmentRecords in st.dataframe (sortable, filterable)
3. Add "Import CSV" file uploader → calls investlib-data CLI
4. Display import results (success count, errors)
5. Add "Manual Entry" form → single record input
6. Show validation errors prominently
**Depends**: T024, T029

### [X] T031 - Create Dashboard Page (Part 1: Data Loading)

**Story**: US1
**Files**: `investapp/investapp/pages/1_dashboard.py`
**Action**:
1. Create Streamlit page "Dashboard"
2. Load dashboard data using `get_dashboard_data()`
3. Display total assets (large metric at top)
4. Handle empty state → show "No data yet, import records to get started"
**Depends**: T028

### [X] T032 - Create Dashboard Page (Part 2: Charts)

**Story**: US1
**Files**: `investapp/investapp/pages/1_dashboard.py` (continue)
**Action**:
1. Add profit/loss curve chart with timeframe selector (daily/weekly/monthly)
2. Add asset distribution pie chart
3. Add holdings table with columns: symbol, quantity, avg_cost, current_price, P&L
4. Use chart_renderer for Plotly charts
**Depends**: T031

### [X] T033 - Create Main App Entry Point

**Story**: US1
**Files**: `investapp/investapp/app.py`
**Action**:
1. Create Streamlit main app
2. Set page config (title="MyInvest", icon, layout="wide")
3. Display "Current Mode: Simulated Trading" banner (st.info with green background)
4. Add navigation instructions
5. Set default page to Dashboard
**Depends**: T032

### [X] T034 - End-to-End Test for User Story 1

**Story**: US1 | **Test-First**: ✅ VALIDATE
**Files**: `tests/integration/test_us1_import_and_view.py`
**Action**:
1. Full workflow test:
   - Initialize database
   - Import sample CSV (10 records)
   - Verify records in database
   - Calculate holdings
   - Generate dashboard data
   - Verify total_assets calculation
   - Verify profit/loss curve has data points
2. Test with empty database → verify zero state
**Depends**: T033
**Expected**: Tests PASS (validates complete US1 implementation)

### [X] T035 - User Story 1 Acceptance Testing

**Story**: US1 | **Manual Test**
**Files**: None (manual verification)
**Action**:
1. Launch app: `streamlit run investapp/investapp/app.py`
2. Test Acceptance Scenario 1: Import valid CSV → records appear
3. Test Acceptance Scenario 2: View dashboard → see assets, curve, pie chart, holdings
4. Test Acceptance Scenario 3: Import invalid data → errors displayed
5. Test Acceptance Scenario 4: Switch timeframes → charts update
6. Record test results in checklist
**Depends**: T034
**Checkpoint**: ✅ User Story 1 complete and independently testable

---

## Phase 4: User Story 2 (P2) - Investment Recommendations

**Goal**: Users receive AI-powered investment recommendations with safety checks

**Independent Test Criteria**:
- Click "Generate Recommendations" → recommendation cards display with all mandatory fields
- View detailed explanation → see strategy, signals, historical cases
- System rejects recommendations without stop-loss → error logged
- Recommendations show data freshness indicator

**Duration Estimate**: 3-4 days

### [X] T036 - Write Contract Tests for investlib-quant CLI

**Story**: US2 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-quant/tests/contract/test_cli.py`
**Action**:
1. Test `investlib-quant analyze --help` shows usage
2. Test `investlib-quant analyze --symbol 600519.SH --strategy livermore --dry-run`
3. Test `--output json` returns structured recommendation
4. Test invalid symbol → error code 1
**Expected**: Tests FAIL
**Depends**: T020 (foundation complete)

### [X] T037 - Write Integration Tests for Livermore Strategy

**Story**: US2 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-quant/tests/integration/test_livermore_strategy.py`
**Action**:
1. Test strategy with bullish breakout data → generates BUY signal
2. Test strategy with bearish breakdown → generates SELL signal
3. Test strategy with sideways market → generates HOLD signal
4. Test all signals include: entry, stop_loss, take_profit, position_size
5. Test stop_loss validation (BUY: stop < entry, SELL: stop > entry)
6. Create test market data fixtures
**Expected**: Tests FAIL
**Depends**: T036

### [X] T038 - Implement Livermore Strategy Core

**Story**: US2
**Files**: `investlib-quant/investlib_quant/livermore_strategy.py`
**Action**:
1. Create `LivermoreStrategy` class
2. Method `analyze(market_data)` → calculate indicators:
   - 120-day moving average
   - Volume vs 20-day average
   - MACD (12/26/9)
   - ATR for stop-loss
3. Detect breakout signals (price > MA, volume spike, MACD cross)
4. Return signal: BUY/SELL/HOLD with confidence (HIGH/MEDIUM/LOW)
5. Use pandas_ta for indicator calculations
**Depends**: T037
**Validates**: T037 (tests should now PASS)

### [X] T039 - Implement Risk Calculator

**Story**: US2
**Files**: `investlib-quant/investlib_quant/risk_calculator.py`
**Action**:
1. Create `RiskCalculator` class
2. Method `calculate_position_size(capital, risk_pct, entry, stop_loss)` → position_size
3. Method `calculate_max_loss(position_size, entry, stop_loss)` → max_loss_amount
4. Method `validate_position_limits(position_size, total_capital)` → check ≤20%, ≤100% total
5. Formulas:
   - position_size = (capital * risk_pct) / abs(entry - stop_loss)
   - max_loss = position_size * abs(entry - stop_loss)
**Depends**: T038

### [X] T040 - Implement Signal Generator

**Story**: US2
**Files**: `investlib-quant/investlib_quant/signal_generator.py`
**Action**:
1. Create `SignalGenerator` class
2. Method `generate_trading_signal(symbol, market_data, capital)`:
   - Call LivermoreStrategy.analyze()
   - Calculate ATR-based stop-loss (entry ± 2*ATR)
   - Calculate take-profit (entry ± 3*ATR, 1:3 risk-reward)
   - Call RiskCalculator for position sizing
   - Build structured signal dict
3. Validate stop-loss is present (raise error if missing)
4. Return signal with metadata (strategy_name, confidence, key_factors)
**Depends**: T038, T039

### [X] T041 - Implement investlib-quant CLI Commands

**Story**: US2
**Files**: `investlib-quant/investlib_quant/cli.py` (add commands)
**Action**:
1. Add `analyze --symbol SYMBOL --strategy livermore --capital CAPITAL --dry-run --output json`
2. Fetch market data from investlib-data
3. Call SignalGenerator.generate_trading_signal()
4. Output signal (text or JSON)
**Depends**: T040
**Validates**: T036 (contract tests should now PASS)

### [X] T042 [P] - Write Contract Tests for investlib-advisors CLI

**Story**: US2 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-advisors/tests/contract/test_cli.py`
**Action**:
1. Test `investlib-advisors ask --advisor livermore --context data.json --output json`
2. Test `investlib-advisors list-advisors` returns livermore
3. Test invalid advisor → error code 1
**Expected**: Tests FAIL
**Depends**: T020

### [X] T043 - Write Integration Tests for Livermore Advisor

**Story**: US2 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-advisors/tests/integration/test_livermore_advisor.py`
**Action**:
1. Test advisor generates recommendation from signal + market data
2. Test recommendation includes: reasoning, confidence, key_factors, historical_precedents
3. Test recommendation uses prompt template v1.0
4. Test recommendation logs advisor_version
**Expected**: Tests FAIL
**Depends**: T042

### [X] T044 - Implement Livermore Advisor

**Story**: US2
**Files**: `investlib-advisors/investlib_advisors/livermore_advisor.py`
**Action**:
1. Create `LivermoreAdvisor` class
2. Load prompt template from `prompts/livermore-v1.0.md`
3. Method `generate_recommendation(signal, market_data, capital)`:
   - Use template to format explanation
   - Fill in: entry, stop_loss, take_profit, position, max_loss
   - Add key_factors from signal (breakout, volume, MACD)
   - Query database for historical_precedents (similar signals, outcomes)
   - Build InvestmentRecommendation model
4. Set advisor_name="Livermore", advisor_version="v1.0.0"
5. Return recommendation dict
**Depends**: T043
**Validates**: T043 (tests should now PASS)

### [X] T045 - Implement Response Parser

**Story**: US2
**Files**: `investlib-advisors/investlib_advisors/response_parser.py`
**Action**:
1. Create `ResponseParser` class
2. Method `parse_recommendation(advisor_output)` → validate structure
3. Ensure all mandatory fields present (entry, stop_loss, take_profit, etc.)
4. Validate stop_loss logic (BUY: stop < entry, SELL: stop > entry)
5. Raise `InvalidRecommendationError` if validation fails
**Depends**: T044

### [X] T046 - Implement investlib-advisors CLI Commands

**Story**: US2
**Files**: `investlib-advisors/investlib_advisors/cli.py` (add `ask` command)
**Action**:
1. Add `ask --advisor livermore --context FILE --output json`
2. Load context (signal + market data) from JSON file
3. Call LivermoreAdvisor.generate_recommendation()
4. Parse and validate with ResponseParser
5. Output recommendation (text or JSON)
**Depends**: T045
**Validates**: T042 (contract tests should now PASS)

### [X] T047 - Create Recommendation Card Component

**Story**: US2
**Files**: `investapp/investapp/components/recommendation_card.py`
**Action**:
1. Function `render_recommendation_card(recommendation)` → Streamlit card
2. Display: symbol, action (BUY/SELL/HOLD badge)
3. Display mandatory fields: entry, stop_loss, take_profit, position, max_loss (RED)
4. Add "View Detailed Explanation" expander
5. Add "Confirm Execution" button (placeholder for US3)
6. Display data freshness indicator (green/yellow/gray badge)
**Depends**: T046

### [X] T048 - Update Dashboard Page (Add Recommendation Generation)

**Story**: US2
**Files**: `investapp/investapp/pages/1_dashboard.py` (add section)
**Action**:
1. Add "Generate Recommendations" button
2. On click:
   - Get current holdings (symbols to analyze)
   - For each symbol: call investlib-quant CLI
   - For each signal: call investlib-advisors CLI
   - Save recommendations to database (InvestmentRecommendation table)
3. Display loading spinner during generation
4. Display up to 3 recommendation cards
5. Cache recommendations (don't regenerate on page refresh)
**Depends**: T047

### [X] T049 - Implement Detailed Explanation Display

**Story**: US2
**Files**: `investapp/investapp/components/recommendation_card.py` (extend)
**Action**:
1. In expander "View Detailed Explanation":
   - Section: **Triggering Strategy** (show strategy_name)
   - Section: **Market Signals** (list key_factors as bullets)
   - Section: **Historical Precedents** (table with date, pattern, outcome)
   - Section: **Confidence** (HIGH/MEDIUM/LOW badge)
   - Section: **Data Version** (market_data_timestamp, data_source)
2. Format with clear Chinese labels
**Depends**: T048

### [X] T050 - End-to-End Test for User Story 2

**Story**: US2 | **Test-First**: ✅ VALIDATE
**Files**: `tests/integration/test_us2_recommendations.py`
**Action**:
1. Full workflow test:
   - Fetch market data for test symbol
   - Generate signal with investlib-quant
   - Generate recommendation with investlib-advisors
   - Verify recommendation has all mandatory fields
   - Verify stop-loss validation works
   - Verify recommendation saved to database
2. Test rejection of recommendation without stop-loss
**Depends**: T049
**Expected**: Tests PASS (validates complete US2 implementation)

### [X] T051 - User Story 2 Acceptance Testing

**Story**: US2 | **Manual Test**
**Files**: None (manual verification)
**Action**:
1. Click "Generate Recommendations" button
2. Test Acceptance Scenario 1: Recommendation card displays with all fields
3. Test Acceptance Scenario 2: Click "View Detailed Explanation" → see strategy, signals, historical cases
4. Test Acceptance Scenario 3: Backend validation rejects no-stop-loss → check logs
5. Test Acceptance Scenario 4: Data freshness indicator shows correct status
6. Record test results
**Depends**: T050
**Checkpoint**: ✅ User Story 2 complete and independently testable

---

## Phase 5: User Story 3 (P3) - Simulated Trading

**Goal**: Users execute simulated trades with approval workflow and audit logging

**Independent Test Criteria**:
- Click "Confirm Execution" → second confirmation dialog appears with all details
- Confirm dialog → operation logged to database with timestamp and user_id
- Attempt over-allocation → rejected with clear error
- Executed trade → appears in holdings list
- Simulation mode label visible on all pages

**Duration Estimate**: 2-3 days

### [X] T052 - Write Integration Tests for Operation Logging

**Story**: US3 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-data/tests/integration/test_operation_log.py`
**Action**:
1. Test insert operation to OperationLog → success
2. Test attempt UPDATE → raises error (append-only)
3. Test attempt DELETE → raises error (append-only)
4. Test query operations by timestamp, symbol
5. Test operation includes original_recommendation and user_modification JSON
**Expected**: Tests FAIL (OperationLog enforcement not complete)
**Depends**: T020 (models exist but need enforcement)

### [X] T053 - Implement Operation Logger

**Story**: US3
**Files**: `investlib-data/investlib_data/operation_logger.py`
**Action**:
1. Create `OperationLogger` class
2. Method `log_operation(user_id, operation_type, symbol, recommendation, modification, status)`:
   - Create OperationLog model instance
   - Set timestamp, operation_id (UUID)
   - Serialize recommendation to JSON
   - Serialize modification to JSON (if any)
   - Insert to database (no update/delete allowed)
3. Method `get_operations(user_id, filters)` → query logs
4. Enforce append-only at SQLAlchemy event level
**Depends**: T052
**Validates**: T052 (tests should now PASS)

### [X] T054 - Write Integration Tests for Position Validation

**Story**: US3 | **Test-First**: ✅ RED PHASE
**Files**: `investapp/tests/integration/test_position_validator.py`
**Action**:
1. Test validate_position with available capital → PASS
2. Test position > 20% single limit → FAIL with error
3. Test total allocation > 100% → FAIL with error
4. Test position calculation includes existing holdings
**Expected**: Tests FAIL (validator doesn't exist)
**Depends**: T020

### [X] T055 - Implement Position Validator

**Story**: US3
**Files**: `investapp/investapp/components/position_validator.py`
**Action**:
1. Create `PositionValidator` class
2. Method `validate_position(recommendation, current_holdings, total_capital)`:
   - Check position_size_pct ≤ 20% (configurable)
   - Calculate total_allocation = current + new position
   - Check total_allocation ≤ 100%
   - Return ValidationResult(valid=bool, errors=[])
3. Return clear error messages
**Depends**: T054
**Validates**: T054 (tests should now PASS)

### [X] T056 - Create Confirmation Dialog Component

**Story**: US3
**Files**: `investapp/investapp/components/confirmation_dialog.py`
**Action**:
1. Function `render_confirmation_dialog(recommendation)` using st.dialog()
2. Display all details:
   - Symbol, action (BUY/SELL)
   - Entry price, stop-loss, take-profit
   - Position size (% and amount)
   - **Max possible loss** (RED, large font)
3. Add "Modify" option:
   - Allow adjust stop-loss (slider)
   - Allow adjust position size (slider)
   - Recalculate max loss on change
4. Add "Cancel" and "Confirm Execution" buttons
5. Return user action (confirm/cancel) and modifications
**Depends**: T055

### [X] T057 - Update Recommendation Card (Add Execution Button)

**Story**: US3
**Files**: `investapp/investapp/components/recommendation_card.py` (extend)
**Action**:
1. Make "Confirm Execution" button functional
2. On click:
   - Validate position with PositionValidator
   - If invalid: display error (st.error)
   - If valid: open confirmation dialog
3. On dialog confirm:
   - Log operation with OperationLogger
   - Update CurrentHolding (add position)
   - Display success message
4. On dialog cancel: close dialog, no action
**Depends**: T056

### [X] T058 - Implement Holdings Updater

**Story**: US3
**Files**: `investlib-data/investlib_data/holdings.py` (extend)
**Action**:
1. Method `update_holdings_from_operation(operation, session)`:
   - If BUY: add to CurrentHolding (or update quantity + avg cost)
   - If SELL: reduce CurrentHolding (or remove if fully sold)
   - Recalculate avg_purchase_price
   - Update last_update_timestamp
2. Handle fractional shares/contracts
**Depends**: T057

### [X] T059 - Create Operation Logs Page

**Story**: US3
**Files**: `investapp/investapp/pages/4_logs.py`
**Action**:
1. Create Streamlit page "Operation Logs"
2. Query OperationLog table (most recent first)
3. Display in st.dataframe with columns:
   - timestamp, symbol, operation_type, execution_status
   - max_loss_amount (from original_recommendation)
4. Add filters: date range, symbol, operation_type
5. Add "View Details" expander for each row:
   - Show full original_recommendation JSON
   - Show user_modification JSON (if any)
**Depends**: T058

### [X] T060 - Update Main App (Add Simulation Mode Banner)

**Story**: US3
**Files**: `investapp/investapp/app.py` (extend)
**Action**:
1. Verify "Current Mode: Simulated Trading" banner exists (from T033)
2. Make banner prominent: green background, large font, top of every page
3. Add icon (info circle)
4. Ensure banner persists across page navigation
**Depends**: T059

### [X] T061 - End-to-End Test for User Story 3

**Story**: US3 | **Test-First**: ✅ VALIDATE
**Files**: `tests/integration/test_us3_execution.py`
**Action**:
1. Full workflow test:
   - Generate recommendation
   - Validate position (should pass)
   - Simulate confirm button click
   - Verify confirmation dialog data
   - Simulate user confirmation
   - Verify operation logged to database
   - Verify holdings updated
   - Query operation logs → verify entry exists
2. Test over-allocation rejection
**Depends**: T060
**Expected**: Tests PASS (validates complete US3 implementation)

### [X] T062 - User Story 3 Acceptance Testing

**Story**: US3 | **Manual Test**
**Files**: None (manual verification)
**Action**:
1. Click "Confirm Execution" on recommendation card
2. Test Acceptance Scenario 1: Confirmation dialog appears with all details
3. Test Acceptance Scenario 2: Confirm → operation logged (check logs page)
4. Test Acceptance Scenario 3: Attempt over-allocation → rejected with error
5. Test Acceptance Scenario 4: Executed trade → appears in holdings
6. Test Acceptance Scenario 5: Simulation banner visible on all pages
7. Record test results
**Depends**: T061
**Checkpoint**: ✅ User Story 3 complete and independently testable

### [X] T063 - Test Append-Only Log Enforcement

**Story**: US3 | **Test-First**: ✅ VALIDATE
**Files**: `tests/integration/test_append_only_enforcement.py`
**Action**:
1. Create operation log entry
2. Attempt to modify entry via SQLAlchemy → verify exception raised
3. Attempt to delete entry via SQLAlchemy → verify exception raised
4. Attempt direct SQL UPDATE → verify trigger blocks (if using SQLite triggers)
5. Verify logs remain immutable
**Depends**: T053
**Expected**: Tests PASS (validates Constitution Principle VIII enforcement)

---

## Phase 6: User Story 4 (P4) - Market Data Visualization

**Goal**: Users access market data with K-line charts and quality indicators

**Independent Test Criteria**:
- Search symbol → K-line chart displays with daily candlesticks for 1 year
- View chart → freshness indicator shows correct status (green/yellow/gray)
- API failure → retries 3 times, falls back to cache, displays warning
- View metadata → see API source, timestamp, adjustment method

**Duration Estimate**: 2-3 days

### [X] T064 - Write Integration Tests for Market Data Fetcher

**Story**: US4 | **Test-First**: ✅ RED PHASE
**Files**: `investlib-data/tests/integration/test_market_data_fetcher.py`
**Action**:
1. Test fetch with Tushare → returns OHLCV data with metadata
2. Test fetch with API failure → retries 3 times, falls back to AKShare
3. Test fallback to cache when all APIs fail → returns cached data with HISTORICAL freshness
4. Test cache stores data with 7-day expiry
5. Test freshness calculation: <5s=REALTIME, 5s-15min=DELAYED, >15min=HISTORICAL
**Expected**: Tests FAIL (complete fetcher logic doesn't exist)
**Depends**: T020 (base API wrappers exist)

### [X] T065 - Implement Market Data Fetcher (with Retry and Fallback)

**Story**: US4
**Files**: `investlib-data/investlib_data/market_api.py` (extend with `MarketDataFetcher`)
**Action**:
1. Create `MarketDataFetcher` class
2. Method `fetch_with_fallback(symbol, start_date, end_date)`:
   - Try TushareClient (3 retries with exponential backoff)
   - On failure: try AKShareClient (3 retries)
   - On failure: try CacheManager.get_from_cache()
   - Calculate data_freshness based on retrieval_timestamp
   - Return data with metadata (api_source, freshness, retrieval_timestamp)
3. Return `MarketDataResult` with data + metadata
**Depends**: T064
**Validates**: T064 (tests should now PASS)

### [X] T066 - Implement Market Data CLI Command

**Story**: US4
**Files**: `investlib-data/investlib_data/cli.py` (add `fetch-market` command)
**Action**:
1. Add `fetch-market --symbol SYMBOL --start DATE --end DATE --output json`
2. Call MarketDataFetcher.fetch_with_fallback()
3. Output data with metadata (JSON or text)
4. Display warning if using cached data
**Depends**: T065

### [X] T067 - Create K-Line Chart Renderer

**Story**: US4
**Files**: `investapp/investapp/components/chart_renderer.py` (extend)
**Action**:
1. Function `render_kline_chart(market_data, timeframe)` → Plotly candlestick chart
2. Use `plotly.graph_objects.Candlestick` for OHLC data
3. Support timeframe: daily/weekly/monthly (aggregate data)
4. Add volume bars below candlesticks
5. Add 120-day MA overlay (from Livermore strategy)
6. Chinese labels and formatting
7. Return Plotly figure
**Depends**: T066

### [X] T068 - Create Data Freshness Indicator Component

**Story**: US4
**Files**: `investapp/investapp/components/data_freshness.py`
**Action**:
1. Function `render_freshness_indicator(data_freshness, retrieval_timestamp)` → Streamlit badge
2. Display badge:
   - REALTIME: green badge with "实时" label
   - DELAYED: yellow badge with "延迟 15 分钟" label
   - HISTORICAL: gray badge with "历史数据" label
3. Add timestamp below badge
4. Return Streamlit component
**Depends**: T067

### [X] T069 - Create Market Data Page

**Story**: US4
**Files**: `investapp/investapp/pages/3_market.py`
**Action**:
1. Create Streamlit page "Market Data"
2. Add symbol search box (text input)
3. Add "Fetch Data" button
4. On click:
   - Call investlib-data fetch-market CLI
   - Display loading spinner
   - Render K-line chart with chart_renderer
   - Display freshness indicator
   - Display metadata table (API source, timestamp, adjustment method)
5. Add timeframe selector (daily/weekly/monthly radio buttons)
6. Handle errors gracefully (display st.error)
**Depends**: T068

### [X] T070 - Implement API Failure Warning Display

**Story**: US4
**Files**: `investapp/investapp/pages/3_market.py` (extend)
**Action**:
1. Check if data.api_source == "Cache" or data_freshness == HISTORICAL
2. If true: display prominent warning banner:
   - "Currently using historical data, updated at [timestamp]"
   - Yellow background, warning icon
   - Position above chart
3. If API call failed completely: display error with retry button
**Depends**: T069

### [X] T071 - End-to-End Test for User Story 4

**Story**: US4 | **Test-First**: ✅ VALIDATE
**Files**: `tests/integration/test_us4_market_data.py`
**Action**:
1. Full workflow test:
   - Fetch market data for test symbol
   - Verify K-line chart data has OHLCV
   - Verify freshness calculated correctly
   - Test API failure scenario (mock):
     - Verify 3 retries attempted
     - Verify fallback to cache
     - Verify warning displayed
   - Verify metadata includes API source, timestamp
2. Test cache expiry cleanup
**Depends**: T070
**Expected**: Tests PASS (validates complete US4 implementation)

### [X] T072 - User Story 4 Acceptance Testing

**Story**: US4 | **Manual Test**
**Files**: None (manual verification)
**Action**:
1. Navigate to Market Data page
2. Test Acceptance Scenario 1: Search "600519.SH" → K-line chart displays with 1 year daily data
3. Test Acceptance Scenario 2: View chart → freshness indicator shows correct status
4. Test Acceptance Scenario 3: Disconnect network → API fails → retries → cache fallback → warning displays
5. Test Acceptance Scenario 4: View metadata → see API source, timestamp, adjustment method
6. Record test results
**Depends**: T071
**Checkpoint**: ✅ User Story 4 complete and independently testable

### [X] T073 - Test Graceful Degradation Path

**Story**: US4 | **Test-First**: ✅ VALIDATE
**Files**: `tests/integration/test_api_failure_recovery.py`
**Action**:
1. Test complete API failure path:
   - Mock all APIs to fail
   - Verify cache fallback works
   - Verify warning displayed
   - Verify system remains functional (doesn't crash)
2. Test cache expiry:
   - Set cache data with expiry in past
   - Verify data not returned from cache
3. Test retry backoff timing
**Depends**: T071
**Expected**: Tests PASS (validates Constitution Principle X: Graceful Degradation)

---

## Phase 7: Polish & Integration

**Goal**: Cross-cutting concerns, documentation, final testing

**Duration Estimate**: 1 day

### [X] T074 [P] - Create Project README

**Story**: Polish
**Files**: `README.md`
**Action**:
1. Write comprehensive README:
   - Project description
   - Features list (4 user stories)
   - Prerequisites (Python 3.10+, Tushare token)
   - Quick start (copy from quickstart.md)
   - Project structure overview
   - Constitution compliance badge
   - License (if applicable)
2. Add screenshots (optional for v0.1)
**Depends**: T073

### [X] T075 [P] - Create Library Documentation

**Story**: Polish
**Files**: `investlib-data/README.md`, `investlib-quant/README.md`, `investlib-advisors/README.md`
**Action**:
1. For each library:
   - Purpose and features
   - CLI commands with examples
   - API usage examples (import and use as Python library)
   - Data models/entities
   - Testing instructions
2. Ensure --help documentation is complete
**Depends**: T073

### [X] T076 - Run Full Test Suite

**Story**: Polish | **Test-First**: ✅ FINAL VALIDATION
**Files**: All test files
**Action**:
1. Run all contract tests: `pytest */tests/contract -v`
2. Run all integration tests: `pytest */tests/integration tests/integration -v`
3. Run with coverage: `pytest --cov=investlib_data --cov=investlib_quant --cov=investlib_advisors --cov-report=html`
4. Verify coverage >80% for all libraries
5. Fix any failing tests
6. Generate coverage report
**Depends**: T073

### [X] T077 - Constitution Compliance Final Check

**Story**: Polish
**Files**: All source files
**Action**:
1. Verify all 10 Constitution principles:
   - [x] I. Library-First: All business logic in investlib-*
   - [x] II. CLI Interface: All libraries have --help, --dry-run, JSON output
   - [x] III. Test-First: All tests written before implementation
   - [x] IV. Simplicity: 5 projects (within limit)
   - [x] V. Anti-Abstraction: Direct API usage
   - [x] VI. Integration-First: Real APIs in tests
   - [x] VII. Data Integrity: All data includes source, timestamp, validation
   - [x] VIII. Investment Safety: Mandatory stop-loss, approval workflow, append-only logs
   - [x] IX. AI Advisor: Versioned prompts (livermore-v1.0.md)
   - [x] X. Graceful Degradation: Retry + fallback + cache tested
2. Document compliance in plan.md
**Depends**: T076

### [X] T078 - Final End-to-End Test (All User Stories)

**Story**: Polish | **Test-First**: ✅ COMPLETE SYSTEM VALIDATION
**Files**: `tests/integration/test_complete_system.py`
**Action**:
1. Test complete user workflow across all 4 stories:
   - US1: Import records → view dashboard
   - US2: Generate recommendations → view explanations
   - US3: Execute trade → view operation log
   - US4: View market data → verify chart displays
2. Test cross-story integration:
   - Recommendations use imported holdings
   - Executed trades update holdings displayed in dashboard
   - Market data used for recommendations is traceable
3. Test error scenarios across stories
4. Verify all Quality Gates from spec.md
**Depends**: T077
**Expected**: Tests PASS (validates complete system)
**Checkpoint**: ✅ MyInvest v0.1 complete and production-ready

---

## Dependencies & Execution Order

### Story-Level Dependencies

```
Setup (Phase 1) → Foundation (Phase 2) → US1 (Phase 3)
                                       ↓
                                    US2 (Phase 4) [depends on US1 for holdings]
                                       ↓
                                    US3 (Phase 5) [depends on US2 for recommendations]
                                       ↓
                                    US4 (Phase 6) [independent, can run parallel to US2-US3]
                                       ↓
                                  Polish (Phase 7)
```

### Critical Path

1. **Setup** (T001-T008) → 3 hours
2. **Foundation** (T009-T020) → 1 day [BLOCKING]
3. **US1** (T021-T035) → 2-3 days
4. **US2** (T036-T051) → 3-4 days [depends on US1]
5. **US3** (T052-T063) → 2-3 days [depends on US2]
6. **US4** (T064-T073) → 2-3 days [can parallelize with US2-US3 after Foundation]
7. **Polish** (T074-T078) → 1 day

**Total Duration**: ~14-18 days (2-3 weeks)

### Parallel Execution Opportunities

**Within Setup (Phase 1)**: T001-T006 can all run in parallel (6 tasks)

**Within Foundation (Phase 2)**:
- T013, T014, T015 can run in parallel (3 API tasks)
- T017, T018, T019 can run in parallel (3 CLI setup tasks)

**Cross-Story Parallelization**:
- After Foundation complete: US1 (T021-T035) starts
- After US1 complete: US2 (T036-T051) and US4 (T064-T073) can run in parallel (different files)
- US3 (T052-T063) starts after US2 complete

**Within Polish (Phase 7)**: T074, T075 can run in parallel (2 documentation tasks)

---

## MVP Scope Recommendation

**MVP = User Story 1 Only** (T001-T035)

This delivers a complete, independently testable feature:
- Users can import historical investment records
- Users can view portfolio performance with charts
- Data validation and error handling
- All safety and data integrity requirements met

**Duration**: ~4-5 days

**Incremental Delivery Sequence**:
1. MVP Release (US1): Import and view portfolio - Week 1
2. Enhancement 1 (US2): Add recommendations - Week 2
3. Enhancement 2 (US3): Add trading execution - Week 2-3
4. Enhancement 3 (US4): Add market data charts - Week 3

---

## Implementation Strategy

### Test-First Workflow (Constitution Principle III)

**For every feature**:
1. Write contract tests (CLI interface) → RED phase
2. Write integration tests (business logic) → RED phase
3. Get project owner approval
4. Verify all tests FAIL
5. Implement feature
6. Verify all tests PASS → GREEN phase
7. Refactor for simplicity

### Development Iteration Pattern

**Per User Story**:
1. **Sprint Planning**: Review user story acceptance scenarios
2. **Test Writing**: Write all tests for the story (1-2 days)
3. **Test Approval**: Get project owner sign-off on tests
4. **Implementation**: Build features until tests pass (2-3 days)
5. **Story Demo**: Manually verify acceptance scenarios
6. **Checkpoint**: Mark story complete before moving to next

### Quality Gates

**Before marking any user story complete**:
- ✅ All story tests pass (contract + integration)
- ✅ Coverage >80% for story-specific code
- ✅ Manual acceptance testing complete
- ✅ Independent test criteria verified
- ✅ CLI interfaces functional (--help, --dry-run work)
- ✅ Constitution principles validated for story

---

**Tasks Ready for Implementation**: Proceed with T001 (Setup) → T035 (US1 Complete) for MVP delivery