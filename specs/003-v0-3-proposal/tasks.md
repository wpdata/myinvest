# Implementation Tasks: MyInvest V0.3 - Production-Ready Enhancement

**Feature Branch**: `003-v0-3-proposal`
**Generated**: 2025-10-22
**Based on**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md)

## Task Summary

- **Total Tasks**: 94
- **Priority P0 Tasks**: 24 (US1: Watchlist + US2: Parallel Backtest)
- **Priority P1 Tasks**: 58 (US3-7: Optimization, Export, Derivatives, Risk, Combination)
- **Priority P2 Tasks**: 12 (US8-9: Multi-timeframe, Indicators)
- **Parallel Opportunities**: 47 tasks marked [P] for concurrent execution
- **MVP Scope**: User Story 1 (Watchlist Management) - 12 tasks

---

## Phase 0 Research: ✅ COMPLETE

**Research Status**: All technical decisions documented in `research.md` (2025-10-22)

**Key Decisions**:
1. ✅ **UI Framework**: Continue with Streamlit + streamlit-autorefresh + streamlit-gettext
2. ✅ **Parallel Backtesting**: SharedMemory + ProcessPoolExecutor with adaptive scaling
3. ✅ **Database Migrations**: Alembic with batch mode for SQLite
4. ✅ **Options Greeks**: py_vollib_vectorized with historical volatility fallback
5. ✅ **Risk Metrics**: Historical simulation VaR + rolling correlation (60-day window)
6. ✅ **Report Generation**: ReportLab (PDF) + openpyxl (Excel) + python-docx (Word)
7. ✅ **Configuration**: Pydantic BaseSettings with nested structure + .env file

**Implementation Ready**: All architectural decisions made, code examples provided in research.md

---

## Phase 1: Setup & Infrastructure (Days 1-2) ✅ COMPLETE

### T001 [X] [P] - Install V0.3 Dependencies
**Story**: Setup
**File**: `requirements.txt`
**Description**: Add new dependencies for V0.3 features (based on research.md decisions)
```bash
# Phase 0 Research Decisions (research.md)
# UI Framework: Continue Streamlit with enhancements
streamlit>=1.28.0
streamlit-autorefresh>=0.0.1
streamlit-gettext>=0.1.0
plotly>=5.17.0
mplfinance>=0.12.10

# Database Migrations: Alembic
alembic>=1.12.0
pytest-alembic  # For migration testing

# Configuration: Pydantic
pydantic[dotenv]>=2.0.0

# Report Generation: ReportLab + openpyxl + python-docx
reportlab>=3.6.0
openpyxl>=3.1.0
python-docx>=0.8.11
matplotlib>=3.7.0

# Options Greeks: py_vollib_vectorized
py_vollib_vectorized>=0.1.0

# Risk Metrics & Parallel Processing
scipy>=1.11.0
psutil  # Memory monitoring
```

### T002 [X] [P] - Initialize Alembic for Database Migrations
**Story**: Setup
**File**: `investlib-data/alembic/`
**Description**: Set up Alembic migration framework
- Run `alembic init alembic` in investlib-data
- Configure `alembic.ini` with SQLite database URL
- Configure `env.py` with `render_as_batch=True` for SQLite
- Add PRAGMA foreign_keys disable/enable hooks
- Test: `alembic check` succeeds

### T003 [X] [P] - Create Pydantic Configuration Module
**Story**: Setup
**File**: `myinvest-app/src/myinvest_app/config/settings.py`
**Description**: Implement centralized configuration with Pydantic BaseSettings
- Create nested settings classes (DataSourceSettings, FuturesSettings, OptionsSettings, RiskSettings)
- Add custom validators (e.g., force_close_margin_rate < default_margin_rate)
- Configure .env file loading with `__` delimiter
- Create `.env.example` template
- Test: Settings load correctly with validation

### T003b [X] [P] - Setup Chinese Localization Infrastructure
**Story**: Setup (BLOCKS ALL UI TASKS - MUST complete before T010)
**File**: `myinvest-app/src/myinvest_app/locales/`
**Description**: Establish Chinese-first UI infrastructure (Constitution Principle I enforcement, based on research.md Decision 1)
- Install and configure streamlit-gettext (per research.md recommendation)
- Create Chinese translation dictionary (zh_CN.json or .po file)
- Configure Chinese font for matplotlib charts (SimHei, Microsoft YaHei, or Noto Sans CJK per research.md)
- Register Chinese font for ReportLab (SimSun.ttf or Noto Sans CJK per research.md Decision 6)
- Create translation helper function: `from streamlit_gettext import gettext as _`
- Test Chinese font rendering in both Streamlit UI and generated reports
- **GATE**: This task MUST complete before ANY UI page implementation (T010, T024, T030, T048, T055, T060, T066)
- Test: Chinese characters display correctly in Streamlit UI and PDF reports

### T004 [X] - Create V0.3 Database Backup Script
**Story**: Setup
**File**: `scripts/backup_database.py`
**Description**: Implement safe database backup before migrations
- Create timestamped backup in `./data/backups/`
- Verify backup integrity with `PRAGMA integrity_check`
- Test backup restoration
- Test: Backup and restore preserves all data

---

## Phase 2: Foundational Tasks (Days 3-4) ✅ COMPLETE

### T005 [X] - Migration 001: Add Watchlist Table
**Story**: Foundation (blocks US1)
**File**: `investlib-data/alembic/versions/20251022_add_watchlist_table.py`
**Description**: Create watchlist database table
- Table: watchlist (id, symbol, group_name, contract_type, status, created_at, updated_at)
- Indexes: ix_watchlist_symbol, ix_watchlist_group, ix_watchlist_status
- Write upgrade() and downgrade()
- Test: Run migration up/down cycle preserves schema

### T006 [X] - Migration 002: Add Contract Info Table
**Story**: Foundation (blocks US5)
**File**: `investlib-data/alembic/versions/20251023_add_contract_info_table.py`
**Description**: Create contract info table for futures/options
- Table: contract_info (contract_code PK, contract_type, underlying, multiplier, margin_rate, tick_size, expire_date, delivery_method, option_type, strike_price, created_at)
- Index: ix_contract_type
- Test: Table supports futures and options metadata

### T007 [X] - Migration 003: Extend Tables for Multi-Asset
**Story**: Foundation (blocks US5)
**File**: `investlib-data/alembic/versions/20251024_extend_tables_multi_asset.py`
**Description**: Add asset_type, direction, margin_used columns to existing tables
- Alter: current_holdings (add asset_type, direction, margin_used with defaults)
- Alter: investment_records (add asset_type, direction, margin_used with defaults)
- Backfill asset_type='stock', direction='long', margin_used=0.0 for existing rows
- Test: Existing V0.1/V0.2 data preserved and accessible

### T008 [X] - Apply All Migrations to Database
**Story**: Foundation
**File**: Database
**Description**: Execute migration workflow
- Backup database (T004 script)
- Run `alembic upgrade head`
- Verify schema with `sqlite3 .schema`
- Verify data integrity with test queries
- Test: All tables exist, no data loss

### T008b [X] - Test Migration Rollback
**Story**: Foundation
**File**: Database
**Description**: Verify rollback capability for all migrations
- Test downgrade for T007 (multi-asset extension): verify columns removed, data preserved
- Test downgrade for T006 (contract_info): verify table dropped
- Test downgrade for T005 (watchlist): verify table dropped
- Test re-upgrade: verify schema restored correctly
- Test: All migrations can be safely rolled back and re-applied

---

## Phase 3: User Story 1 - Watchlist Management (Priority P0, Days 5-6) ✅ COMPLETE

**Story Goal**: Enable UI-based watchlist management to eliminate hardcoded stock lists

**Independent Test Criteria**:
- ✅ Add stock "600519.SH" via UI → appears in watchlist
- ✅ Create group "Core Holdings" with 3 stocks → grouped correctly
- ✅ Upload CSV with 10 stocks → all imported
- ✅ Pause a stock → scheduler skips it
- ✅ Modify watchlist → scheduler updates without restart

### T009 [X] [P] - Create Watchlist Database Access Layer
**Story**: US1
**File**: `investlib-data/src/investlib_data/watchlist_db.py`
**Description**: Implement CRUD operations for watchlist
- add_symbol(symbol, group_name, contract_type='stock', status='active')
- remove_symbol(symbol)
- update_symbol_group(symbol, new_group)
- set_symbol_status(symbol, status)  # 'active' or 'paused'
- get_all_symbols(status='active')
- get_symbols_by_group(group_name)
- batch_import_from_csv(file_path)
- Test: All CRUD operations work

### T010 [X] [P] - Create Streamlit Watchlist Management Page
**Story**: US1
**File**: `myinvest-app/src/myinvest_app/ui/9_watchlist.py`
**Dependencies**: T003b (Chinese localization setup), T009 (watchlist database layer)
**Description**: Build watchlist management UI (Chinese-first interface - Constitution Principle I)
- **MANDATORY**: Use translation helper `_()` for ALL user-facing text from Day 1
- Chinese page title: `st.title(_("watchlist.title"))` → "监视列表管理"
- Add stock form with Chinese labels:
  - Symbol input: `st.text_input(_("watchlist.symbol_input"))` → "股票代码"
  - Group selector: `st.selectbox(_("watchlist.group_selector"))` → "分组"
  - Add button: `st.button(_("watchlist.add_button"))` → "添加"
- Display watchlist table with Chinese column headers: "代码", "分组", "状态", "操作"
- Group management buttons: "创建分组", "重命名", "删除"
- Bulk actions: "暂停", "激活"
- CSV upload widget: `st.file_uploader(_("watchlist.csv_upload"))` → "批量导入CSV"
- All error messages in Chinese: "代码格式错误", "分组已存在" etc.
- Test: UI displays ALL text in Chinese, no English labels visible

### T011 [X] - Integrate Watchlist with Scheduler
**Story**: US1
**File**: `myinvest-app/src/myinvest_app/scheduler.py`
**Description**: Modify scheduler to read from watchlist database (addresses FR-078, FR-079)
- Replace hardcoded symbol list with `watchlist_db.get_all_symbols(status='active')`
- Add asset type detection (stock/futures/options) from watchlist
- Apply asset-specific timing rules:
  - Stocks: 9:30-15:00 market hours
  - Futures: Extended hours (e.g., 9:00-15:15, 21:00-02:30 for CFFEX)
  - Options: Align with underlying asset hours + expiry date awareness
- Skip paused symbols
- Test: Scheduler picks up watchlist changes without restart
- **Note**: This task addresses FR-078 (scheduler upgrade for multi-asset) and FR-079 (asset-specific timing rules)

### T012 [X] - Implement CSV Batch Import
**Story**: US1
**File**: `investlib-data/src/investlib_data/csv_importer.py`
**Description**: CSV parser for bulk watchlist import
- Parse CSV format: symbol, group_name (optional), contract_type (optional)
- Validate symbols format
- Handle duplicates (skip or update)
- Return import summary (success count, error list)
- Test: Import 10 stocks from CSV succeeds

**🔹 Checkpoint US1**: ✅ COMPLETE - Watchlist management fully functional, scheduler reads from database

---

## Phase 4: User Story 2 - Parallel Backtesting (Priority P0, Days 7-9) ✅ COMPLETE

**Story Goal**: Reduce 10-stock backtest time from 10+ minutes to <3 minutes

**Independent Test Criteria**:
- ✅ Backtest 10 stocks completes in <3 minutes on 8-core CPU
- ✅ Progress indicator shows "3/10 stocks completed" in real-time
- ✅ Single stock failure doesn't crash other backtests
- ✅ Consolidated report compares all stocks' Sharpe ratios
- ✅ Auto-detects CPU cores and uses 8 parallel workers

### T013 [X] [P] - Create Shared Memory Market Data Cache
**Story**: US2
**File**: `investlib-backtest/src/investlib_backtest/shared_cache.py`
**Description**: Implement zero-copy shared memory for market data (INTER-PROCESS cache for parallel backtest)
- SharedMarketDataCache class
- create_shared_cache(symbol, dataframe) → stores NumPy array in shared_memory
- attach_to_shared_cache(symbol, metadata) → returns DataFrame
- cleanup() → unlinks all shared memory blocks
- **Scope clarification**: This is for sharing market data BETWEEN parallel worker processes (not API response caching)
- **Not to be confused with**: T073 (TTL-based API response cache)
- Test: Data shared across processes without serialization overhead

### T014 [X] [P] - Refactor BacktestRunner for Single-Stock Execution
**Story**: US2
**File**: `investlib-backtest/src/investlib_backtest/engine/backtest_runner.py`
**Description**: Extract single-stock backtest method
- Add run_single_stock(symbol, data, start_date, end_date) method
- Accept pre-fetched market data (no API calls inside)
- Return isolated result dict
- Ensure no shared state between runs
- Test: run_single_stock executes independently

### T015 [X] - Implement ParallelBacktestOrchestrator
**Story**: US2
**File**: `investlib-backtest/src/investlib_backtest/parallel_backtest.py`
**Dependencies**: T013 (SharedMemoryCache), T014 (single-stock runner), T016 (memory monitor)
**Description**: ProcessPoolExecutor-based parallel execution
- Load market data for all symbols → SharedMemoryCache
- Initialize ProcessPoolExecutor with dynamic worker count:
  - Start with `psutil.cpu_count()` workers
  - Adjust dynamically using T016 MemoryMonitor
  - Algorithm: reduce by 1 worker for each 10% memory usage above 75%; minimum 2 workers
- Submit tasks with `executor.submit(backtest_single_stock, symbol, ...)`
- Track progress with `as_completed()` + tqdm
- Isolate errors per symbol (catch exceptions, continue other stocks)
- Generate consolidated report
- Test: 10 stocks complete in <3 minutes

### T016 [X] [P] - Add Memory Monitoring and Adaptive Scaling
**Story**: US2
**File**: `investlib-backtest/src/investlib_backtest/memory_monitor.py`
**Description**: Monitor memory and adjust worker count (clarified algorithm)
- MemoryMonitor class with psutil
- get_memory_usage() → current % of total RAM
- get_available_workers(base_workers) → adjusted count based on algorithm:
  - If memory_usage < 75%: return base_workers
  - If memory_usage >= 75%: return max(2, base_workers - floor((memory_usage - 75) / 10))
  - Example: 85% usage with 8 base workers → 8 - 1 = 7 workers; 95% usage → 8 - 2 = 6 workers
- Test: Workers reduced when memory >85%, minimum 2 workers enforced

### T017 [X] [P] - Implement Progress Tracking with tqdm
**Story**: US2
**File**: `investlib-backtest/src/investlib_backtest/parallel_backtest.py`
**Description**: Real-time progress display
- Use `as_completed()` to process results as they arrive
- tqdm progress bar with total=len(symbols)
- Display current symbol and status
- Test: Progress bar updates correctly

### T018 [X] - Update Streamlit Backtest Page for Parallel Execution
**Story**: US2
**File**: `myinvest-app/src/myinvest_app/ui/4_backtest.py`
**Description**: Integrate parallel backtest into UI
- Replace sequential BacktestRunner with ParallelBacktestOrchestrator
- Display progress (use st.progress + st.empty() for updates)
- Show consolidated results table (symbol, Sharpe, max_drawdown, return)
- Chinese labels: "并行回测", "进度", "完成"
- Test: UI shows progress and results

**🔹 Checkpoint US2**: ✅ COMPLETE - Parallel backtesting operational, <3 min for 10 stocks

---

## Phase 5: User Story 3 - Parameter Optimization (Priority P1, Days 10-13) ✅ COMPLETE

**Story Goal**: Automated grid search with walk-forward validation

**Independent Test Criteria**:
- ✅ Grid search tests 392 parameter combinations
- ✅ Heatmap shows Sharpe ratio across stop-loss/take-profit
- ✅ Walk-forward validation shows training vs testing Sharpe
- ✅ Overfitting warning when training/testing Sharpe diverges
- ✅ Optimal parameters saved to strategy config

### T019 [X] [P] - Create investlib-optimizer Library Structure
**Story**: US3
**File**: `investlib-optimizer/`
**Description**: Initialize new library for parameter optimization
- Create package structure (src/investlib_optimizer/, tests/)
- Add `__init__.py`, `pyproject.toml`
- Dependencies: numpy, pandas, plotly
- Test: Import investlib_optimizer succeeds

### T020 [X] [P] - Implement Grid Search Engine
**Story**: US3
**File**: `investlib-optimizer/src/investlib_optimizer/grid_search.py`
**Description**: Grid search parameter space exploration
- GridSearchOptimizer class
- define_parameter_space(param_ranges) → dict of ranges
- run_grid_search(strategy, symbol, data, param_space) → results DataFrame
- Leverage ParallelBacktestOrchestrator for parallel evaluation
- Test: 7×8×7=392 combinations executed

### T021 [X] [P] - Implement Walk-Forward Validation
**Story**: US3
**File**: `investlib-optimizer/src/investlib_optimizer/walk_forward.py`
**Description**: Walk-forward validation with rolling windows
- WalkForwardValidator class
- split_data(data, train_period, test_period) → train/test sets
- run_walk_forward(strategy, data, param_combo) → train_metrics, test_metrics
- Detect overfitting (training_sharpe - test_sharpe > threshold)
- Test: 2-year train / 1-year test validation works

### T022 [X] [P] - Implement Overfitting Detection
**Story**: US3
**File**: `investlib-optimizer/src/investlib_optimizer/overfitting.py`
**Description**: Overfitting detection algorithm (implements FR-017 with threshold=0.5)
- calculate_overfitting_score(train_metrics, test_metrics) → sharpe_divergence = train_sharpe - test_sharpe
- is_overfitted(train_sharpe, test_sharpe, threshold=0.5) → returns True if divergence > 0.5
- generate_warning_message(train_sharpe, test_sharpe) → Chinese warning:
  - "警告：检测到过拟合风险！训练集夏普比率 {train_sharpe:.2f}，测试集夏普比率 {test_sharpe:.2f}，差距 {divergence:.2f} 超过阈值 0.5"
- Test: Detects overfitting when train=2.5, test=0.8 (divergence=1.7 > 0.5)

### T023 [X] [P] - Implement Heatmap Visualization
**Story**: US3
**File**: `investlib-optimizer/src/investlib_optimizer/visualizer.py`
**Description**: Plotly heatmap for parameter results
- generate_heatmap(results_df, x='stop_loss', y='take_profit', z='sharpe_ratio')
- Highlight optimal point
- Chinese labels: "止损%", "止盈%", "夏普比率"
- Test: Heatmap renders correctly

### T024 [X] - Create Streamlit Parameter Optimizer Page
**Story**: US3
**File**: `myinvest-app/src/myinvest_app/ui/10_optimizer.py`
**Description**: Parameter optimization UI
- Chinese title: "参数优化器"
- Strategy selector + symbol selector
- Parameter range inputs (stop_loss, take_profit, position_size)
- Run button → triggers grid search
- Display heatmap + optimal parameters
- "应用参数" button → saves to strategy config
- Test: UI displays optimization results

**🔹 Checkpoint US3**: ✅ COMPLETE - Parameter optimization functional with heatmaps

---

## Phase 6: User Story 4 - Report Export (Priority P1, Days 14-16) ✅ COMPLETE

**Story Goal**: Export backtest reports in PDF/Excel/Word formats

**Independent Test Criteria**:
- ✅ PDF generated with cover, metrics, charts, trade history
- ✅ Charts (equity curve, drawdown) properly formatted
- ✅ Excel has 3 sheets with conditional formatting
- ✅ Word includes holdings table + risk metrics
- ✅ All reports contain Chinese disclaimer

### T025 [X] [P] - Create investlib-export Library Structure
**Story**: US4
**File**: `investlib-export/`
**Description**: Initialize export library
- Package structure (src/investlib_export/, tests/)
- Dependencies: reportlab, openpyxl, python-docx, matplotlib
- Test: Import investlib_export succeeds

### T026 [X] [P] - Register Chinese Fonts for ReportLab
**Story**: US4
**File**: `investlib-export/src/investlib_export/font_setup.py`
**Description**: Configure Chinese font support
- Download/bundle SimSun.ttf or Noto Sans CJK
- Register font with pdfmetrics.registerFont()
- Create ParagraphStyle with Chinese font
- Test: PDF renders Chinese characters correctly

### T027 [X] [P] - Implement PDF Report Generator
**Story**: US4
**File**: `investlib-export/src/investlib_export/pdf_generator.py`
**Description**: PDF export using ReportLab
- PDFReportGenerator class
- generate_backtest_report(backtest_result, output_path)
- Cover page with strategy name, date
- Page 1: Performance metrics table (Sharpe, drawdown, return)
- Page 2: Equity curve chart (embed matplotlib PNG)
- Page 3: Drawdown chart
- Page 4: Trade history table (first 50 trades)
- Footer: Chinese disclaimer
- Test: PDF generated with all sections

### T028 [X] [P] - Implement Excel Report Generator
**Story**: US4
**File**: `investlib-export/src/investlib_export/excel_generator.py`
**Description**: Excel export with openpyxl
- ExcelReportGenerator class
- generate_trading_records(trades, output_path)
- Sheet 1: Trade Details (date, symbol, action, price, quantity, profit/loss)
- Sheet 2: Monthly Summary (month, total_return, win_rate)
- Sheet 3: Position Analysis (symbol, holding_period, profit/loss)
- Conditional formatting: profit=green, loss=red
- Test: Excel has 3 sheets with formatting

### T029 [X] [P] - Implement Word Report Generator
**Story**: US4
**File**: `investlib-export/src/investlib_export/word_generator.py`
**Description**: Word export with python-docx
- WordReportGenerator class
- generate_holdings_report(holdings, risk_metrics, output_path)
- Holdings table (symbol, quantity, price, value)
- Risk metrics section (VaR, concentration, correlation)
- Recommended actions
- Test: Word document generated

### T030 [X] - Integrate Export into Streamlit UI
**Story**: US4
**File**: `myinvest-app/src/myinvest_app/ui/4_backtest.py`
**Description**: Add export buttons to backtest results page
- "导出PDF" button → generates PDF download
- "导出Excel" button → generates Excel download
- "导出Word" button → generates Word download
- Unique filenames with timestamp
- Test: All three formats download successfully

**🔹 Checkpoint US4**: ✅ COMPLETE - Report export functional in all three formats

---

## Phase 7: User Story 5 - Futures & Options Support (Priority P1, Days 17-24)

**Story Goal**: Multi-asset trading with margin, Greeks, forced liquidation

**Independent Test Criteria**:
- ✅ Add futures "IF2506.CFFEX" to watchlist with badge
- ✅ Backtest futures with margin calculation + forced liquidation
- ✅ Short position profit/loss calculated correctly
- ✅ Option backtest includes Greeks (Delta, Gamma, Vega, Theta)
- ✅ Watchlist shows asset type badges
- ✅ efinance→AkShare fallback works
- ✅ Futures contract rollover maintains continuous data
- ✅ Option missing data warning displayed

### T031 [X] [P] - Create investlib-margin Library
**Story**: US5
**File**: `investlib-margin/`
**Description**: Margin calculation library for futures/options
- MarginCalculator class
- calculate_margin(contract_type, quantity, price, multiplier, margin_rate)
- calculate_liquidation_price(entry_price, direction, margin_rate, force_close_margin_rate)
- is_forced_liquidation(current_price, liquidation_price, direction) → bool
- Test: Margin calculations accurate (±1%)

### T032 [X] [P] - Create investlib-greeks Library
**Story**: US5
**File**: `investlib-greeks/`
**Description**: Options Greeks calculation using py_vollib_vectorized
- OptionsGreeksCalculator class
- calculate_greeks(S, K, T, r, sigma, option_type) → delta, gamma, vega, theta, rho
- calculate_greeks_dataframe(options_df) → DataFrame with Greeks columns
- VolatilityManager class with HV fallback
- Test: Greeks calculations match py_vollib reference values

### T033 [P] - Extend MarketDataFetcher for Futures/Options
**Story**: US5
**File**: `investlib-data/src/investlib_data/market_api.py`
**Description**: Add futures/options data fetching (implements FR-032 - data source upgrade)
- detect_asset_type(symbol) → 'stock'|'futures'|'option'
- fetch_futures_data(symbol, start, end) → efinance primary → AkShare fallback
- fetch_options_data(symbol, start, end) → efinance primary → AkShare fallback
- **Data Source Migration**: Upgrade V0.2's Tushare→AkShare fallback to efinance→AkShare for all asset types
- handle_continuous_contract(futures_symbol) → continuous price series for rollover
- validate_options_data_completeness(data) → warn if Greeks inputs (IV, expiry) missing
- Test: Fetches IF2506.CFFEX data successfully with efinance, falls back to AkShare on failure

### T034 [P] - Create BaseStrategy Subclasses
**Story**: US5
**File**: `investlib-advisors/src/investlib_advisors/base.py`
**Description**: Split strategy base classes by asset type
- BaseStrategy (abstract, existing)
- StockStrategy extends BaseStrategy (move Livermore/Kroll here)
- FuturesStrategy extends BaseStrategy (add margin awareness)
- OptionsStrategy extends BaseStrategy (add Greeks tracking)
- Test: All three subclasses instantiate correctly

### T035 [P] - Implement FuturesStrategy: Trend Following
**Story**: US5
**File**: `investlib-advisors/src/investlib_advisors/futures/trend_following.py`
**Description**: Futures-specific trend following strategy
- FuturesTrendFollowing extends FuturesStrategy
- generate_signal() with futures-specific rules (bidirectional)
- calculate_position_size() using margin (not full capital)
- handle_rollover() for contract expiry
- Test: Generates long/short signals for IF2506

### T036 [P] - Implement OptionsStrategy: Covered Call
**Story**: US5
**File**: `investlib-advisors/src/investlib_advisors/options/covered_call.py`
**Description**: Covered call option strategy
- CoveredCallStrategy extends OptionsStrategy
- generate_signal() for covered call setup (long stock + short call)
- calculate_greeks() for position
- handle_expiry() for option expiration
- Test: Generates covered call position

### T037 - Upgrade BacktestEngine for Multi-Asset
**Story**: US5
**File**: `investlib-backtest/src/investlib_backtest/engine.py`
**Description**: Polymorphic dispatch for different asset types
- detect_strategy_type(strategy) → use isinstance checks
- route_to_engine(strategy) → StockEngine | FuturesEngine | OptionsEngine
- StockBacktestEngine (T+1, full capital)
- FuturesBacktestEngine (T+0, margin-based, forced liquidation)
- OptionsBacktestEngine (expiry handling, Greeks tracking)
- Test: Backtests stock, futures, options correctly

### T038 - Implement Forced Liquidation Logic
**Story**: US5
**File**: `investlib-backtest/src/investlib_backtest/futures_engine.py`
**Description**: Forced liquidation simulation for futures
- check_liquidation_on_each_bar(position, current_price, margin_account)
- trigger_liquidation() if margin_ratio < force_close_threshold
- Record liquidation event in backtest results
- Test: Forced liquidation triggered correctly

### T039 - Implement Option Expiry Handling
**Story**: US5
**File**: `investlib-backtest/src/investlib_backtest/options_engine.py`
**Description**: Option expiry logic (European-style, expiry-only exercise)
- check_expiry(option_position, current_date)
- exercise_if_itm() for in-the-money options
- expire_worthless() for out-of-money options
- Test: Options exercised/expired correctly on expiry date

### T040 - Update Watchlist UI for Multi-Asset
**Story**: US5
**File**: `myinvest-app/src/myinvest_app/ui/9_watchlist.py`
**Description**: Add asset type selector to watchlist UI
- Asset type dropdown: "股票" | "期货" | "期权"
- Display asset type badge in watchlist table
- Filter by asset type
- Test: Futures/options display with correct badges

**🔹 Checkpoint US5**: Futures & options fully supported with margin/Greeks

---

## Phase 8: User Story 6 - Risk Dashboard (Priority P1, Days 25-29)

**Story Goal**: Real-time risk monitoring with VaR, margin, correlation

**Independent Test Criteria**:
- ✅ Heatmap shows stocks/futures/options with different icons
- ✅ VaR displays "95% VaR (1 day) = ¥3,200, 3.2% of assets"
- ✅ Margin usage shows "65%, Safety buffer: 35%"
- ✅ Forced liquidation warning: "IF2506 3% to liquidation" (yellow)
- ✅ Stop-loss warning: "000001.SZ 1.5% to stop-loss" (red)
- ✅ Option Greeks: "Total Delta: +125, Total Theta: -50/day"
- ✅ Correlation matrix: "600519 vs IF2506 correlation: -0.45"
- ✅ Auto-refreshes every 5 seconds

### T041 [P] - Create investlib-risk Library
**Story**: US6
**File**: `investlib-risk/`
**Description**: Risk metrics calculation library
- RiskMetricsCalculator class
- Test: Library imports successfully

### T042 [P] - Implement VaR Calculator (Historical Simulation)
**Story**: US6
**File**: `investlib-risk/src/investlib_risk/var.py`
**Description**: Historical simulation VaR
- calculate_var_historical(returns, confidence=0.95, horizon=1) → VaR value
- calculate_cvar_historical(returns, confidence=0.95) → CVaR value
- calculate_portfolio_returns_with_futures(positions) → handles leverage
- Test: VaR calculation within 5% of expected

### T043 [P] - Implement Correlation Matrix Calculator
**Story**: US6
**File**: `investlib-risk/src/investlib_risk/correlation.py`
**Description**: Rolling correlation with caching
- CorrelationCalculator class
- calculate_correlation_matrix(prices_df, window=60) → correlation matrix
- Cache results for 5 seconds
- highlight_high_correlation(corr_matrix, threshold=0.7) → list of pairs
- Test: Correlation matrix calculated correctly

### T044 [P] - Implement Concentration Risk Calculator
**Story**: US6
**File**: `investlib-risk/src/investlib_risk/concentration.py`
**Description**: Position concentration analysis
- calculate_concentration(positions) → max_single_position_pct
- calculate_industry_concentration(positions, industry_map) → dict
- Test: Identifies max concentration correctly

### T045 [P] - Implement Margin Risk Calculator
**Story**: US6
**File**: `investlib-risk/src/investlib_risk/margin_risk.py`
**Description**: Futures/options margin risk assessment
- calculate_margin_usage_rate(positions, account_balance) → percentage
- calculate_liquidation_distance(position, current_price) → percentage
- generate_liquidation_warnings(positions) → list of warnings
- Test: Margin risk calculated correctly

### T046 [P] - Implement Greeks Aggregator
**Story**: US6
**File**: `investlib-greeks/src/investlib_greeks/aggregator.py`
**Description**: Aggregate Greeks across positions
- aggregate_position_greeks(positions) → total_delta, total_gamma, etc.
- Sign handling: long=+1, short=-1
- Multiply by quantity and multiplier
- Test: Aggregation sums correctly

### T047 - Implement Risk Dashboard Orchestrator
**Story**: US6
**File**: `investlib-risk/src/investlib_risk/dashboard.py`
**Description**: Coordinate all risk calculations
- RiskDashboardOrchestrator class
- calculate_all_metrics(portfolio) → VaR, CVaR, correlation, concentration, margin, Greeks
- start_background_updates() → thread for 5-second refresh
- Cache results to avoid recalculation
- Test: All metrics calculated in <200ms

### T048 - Create Streamlit Risk Dashboard Page
**Story**: US6
**File**: `myinvest-app/src/myinvest_app/ui/12_risk.py`
**Description**: Real-time risk dashboard UI
- Chinese title: "风险监控仪表盘"
- Position heatmap (bubble chart: size=weight, color=profit/loss)
- VaR/CVaR display
- Margin usage gauge
- Stop-loss/liquidation warning table
- Option Greeks summary
- Correlation heatmap
- Auto-refresh with streamlit-autorefresh (5 seconds)
- Test: Dashboard displays all metrics and refreshes

**🔹 Checkpoint US6**: Risk dashboard operational with real-time updates

---

## Phase 9: User Story 7 - Combination Strategy Builder (Priority P1, Days 30-34)

**Story Goal**: UI-driven multi-leg strategy construction

**Independent Test Criteria**:
- ✅ "Calendar Spread" template populates buy near/sell far legs
- ✅ Drag-and-drop builds butterfly spread (3 legs)
- ✅ P&L chart shows profit/loss vs underlying price
- ✅ Backtest shows combination Sharpe ratio + margin
- ✅ Positions page shows "Combination View" with expandable legs

### T049 [P] - Migration 004: Add Combination Strategy Table
**Story**: US7
**File**: `investlib-data/alembic/versions/20251025_add_combination_strategy.py`
**Description**: Database table for multi-leg strategies
- Table: combination_strategy (strategy_id, strategy_name, strategy_type, legs JSON, status, created_at, updated_at)
- Test: Table stores multi-leg structure

### T050 [P] - Create Combination Strategy Data Models
**Story**: US7
**File**: `investlib-advisors/src/investlib_advisors/combination_models.py`
**Description**: Data structures for multi-leg strategies
- Leg class (contract, direction, quantity, greeks)
- CombinationStrategy class (name, type, legs list)
- Pre-defined templates: COVERED_CALL, BUTTERFLY_SPREAD, CALENDAR_SPREAD, STRADDLE
- Test: Templates instantiate correctly

### T051 [P] - Implement Combination Margin Calculator
**Story**: US7
**File**: `investlib-margin/src/investlib_margin/combination_margin.py`
**Description**: Margin for multi-leg positions (consider hedge effects)
- calculate_combination_margin(legs) → total_margin (reduced vs sum)
- detect_hedge_pairs(legs) → list of offsetting positions
- Test: Margin reduced by 20%+ for hedged positions

### T052 [P] - Implement Combination Greeks Aggregator
**Story**: US7
**File**: `investlib-greeks/src/investlib_greeks/combination_greeks.py`
**Description**: Aggregate Greeks for option combinations
- calculate_combination_greeks(legs) → total_delta, total_gamma, etc.
- Test: Butterfly spread has near-zero delta

### T053 [P] - Implement Combination P&L Chart Generator
**Story**: US7
**File**: `investlib-advisors/src/investlib_advisors/pnl_chart.py`
**Description**: Profit/loss visualization for combinations
- generate_pnl_chart(combination, underlying_price_range) → Plotly figure
- X-axis: underlying price, Y-axis: profit/loss
- Show breakeven points
- Test: Butterfly spread shows characteristic shape

### T054 - Implement Combination Backtest Engine
**Story**: US7
**File**: `investlib-backtest/src/investlib_backtest/combination_backtest.py`
**Description**: Backtest multi-leg strategies
- CombinationBacktestEngine class
- Execute all legs together
- Track combined P&L
- Calculate combined Sharpe ratio and margin
- Test: Covered call backtest executes correctly

### T055 - Create Streamlit Combination Strategy Builder Page
**Story**: US7
**File**: `myinvest-app/src/myinvest_app/ui/11_builder.py`
**Description**: Interactive strategy builder UI
- Chinese title: "组合策略构建器"
- Template selector: dropdown with pre-defined strategies
- Drag-and-drop leg builder (use streamlit components or manual form)
- Real-time P&L chart display
- "回测组合" button → runs combination backtest
- Save combination to database
- Test: UI builds and backtests butterfly spread

### T056 - Add Combination View to Holdings Page
**Story**: US7
**File**: `myinvest-app/src/myinvest_app/ui/holdings.py`
**Description**: Display multi-leg positions
- Toggle: "单腿视图" | "组合视图"
- In combination view: Group legs by strategy_id
- Expandable rows show individual legs
- "平仓组合" button → closes all legs
- Test: Combination positions displayed correctly

**🔹 Checkpoint US7**: Combination strategy builder functional

---

## Phase 10: User Story 8 - Multi-Timeframe Strategy (Priority P2, Days 35-37)

**Story Goal**: Weekly trend + daily timing signal combination

**Independent Test Criteria**:
- ✅ Strategy detects "weekly uptrend + daily breakout" → BUY
- ✅ Comparative backtest: "Daily Sharpe: 1.5, Weekly+Daily: 1.8"
- ✅ UI selector: "Daily" | "Weekly" | "Daily+Weekly Combination"
- ✅ Recommendation card shows "Weekly trend: ↑ Upward"

### T057 [P] - Implement Weekly Data Resampling
**Story**: US8
**File**: `investlib-data/src/investlib_data/resample.py`
**Description**: Convert daily data to weekly
- resample_to_weekly(daily_df) → weekly_df
- Aggregation: OHLC resampling
- Test: Daily data correctly resampled to weekly

### T058 [P] - Implement Weekly Indicator Calculator
**Story**: US8
**File**: `investlib-advisors/src/investlib_advisors/weekly_indicators.py`
**Description**: Calculate indicators on weekly data
- calculate_weekly_ma(weekly_df, period=120)
- calculate_weekly_macd(weekly_df)
- detect_weekly_trend(weekly_df) → 'up' | 'down' | 'sideways'
- Test: Weekly MA and MACD calculated correctly

### T059 - Implement Multi-Timeframe Strategy
**Story**: US8
**File**: `investlib-advisors/src/investlib_advisors/multi_timeframe.py`
**Description**: Combine weekly trend + daily signals
- MultiTimeframeStrategy extends StockStrategy
- check_weekly_trend(weekly_data) → trend
- generate_daily_signal(daily_data) → signal
- combine_signals(weekly_trend, daily_signal) → final_signal (only if aligned)
- Test: Generates BUY only when weekly up + daily breakout

### T060 - Add Multi-Timeframe UI Selector
**Story**: US8
**File**: `myinvest-app/src/myinvest_app/ui/3_recommendations.py`
**Description**: Add timeframe selector to recommendations page
- Radio button: "日线" | "周线" | "日线+周线组合"
- Display weekly trend indicator
- Test: UI switches between timeframes

**🔹 Checkpoint US8**: Multi-timeframe strategy operational

---

## Phase 11: User Story 9 - Technical Indicators Expansion (Priority P2, Days 38-40)

**Story Goal**: Add MACD, KDJ, Bollinger Bands, volume patterns

**Independent Test Criteria**:
- ✅ MACD crossover generates bullish signal
- ✅ Bollinger Band touch identifies oversold
- ✅ KDJ K-line cross D-line in oversold → buy signal
- ✅ Indicator selector shows all options
- ✅ Backtest shows multi-indicator performance

### T061 [P] - Implement MACD Indicator
**Story**: US9
**File**: `investlib-advisors/src/investlib_advisors/indicators/macd.py`
**Description**: MACD calculation and signal generation
- calculate_macd(df, fast=12, slow=26, signal=9) → macd_line, signal_line, histogram
- detect_macd_crossover(macd_line, signal_line) → 'bullish' | 'bearish' | None
- Test: MACD crossover detected correctly

### T062 [P] - Implement KDJ Indicator
**Story**: US9
**File**: `investlib-advisors/src/investlib_advisors/indicators/kdj.py`
**Description**: KDJ (Stochastic Oscillator) calculation
- calculate_kdj(df, period=9) → k_line, d_line, j_line
- detect_kdj_signal(k_line, d_line, zone) → 'buy' | 'sell' | None
- Test: KDJ oversold buy signal detected

### T063 [P] - Implement Bollinger Bands Indicator
**Story**: US9
**File**: `investlib-advisors/src/investlib_advisors/indicators/bollinger.py`
**Description**: Bollinger Bands calculation
- calculate_bollinger_bands(df, period=20, std=2) → upper, middle, lower
- detect_bollinger_signal(price, upper, lower) → 'overbought' | 'oversold' | None
- Test: Price at lower band detected as oversold

### T064 [P] - Implement Volume Pattern Analysis
**Story**: US9
**File**: `investlib-advisors/src/investlib_advisors/indicators/volume.py`
**Description**: Volume pattern recognition
- calculate_volume_ma(df, period=20)
- detect_volume_spike(volume, volume_ma, threshold=1.5) → bool
- detect_volume_divergence(price, volume) → bool
- Test: Volume spike detected correctly

### T065 - Create Multi-Indicator Combination Strategy
**Story**: US9
**File**: `investlib-advisors/src/investlib_advisors/multi_indicator.py`
**Description**: Combine multiple indicators
- MultiIndicatorStrategy extends StockStrategy
- Add indicators: MACD, KDJ, Bollinger Bands
- generate_signal() → combine all indicators (voting or weighted)
- Test: Multi-indicator strategy generates signals

### T066 - Add Indicator Selector to Strategy Config UI
**Story**: US9
**File**: `myinvest-app/src/myinvest_app/ui/strategy_config.py`
**Description**: UI for selecting indicators
- Chinese checkboxes: "MACD", "KDJ", "布林带", "成交量分析"
- Save indicator selection to strategy config
- Test: Indicator selection saved and loaded

**🔹 Checkpoint US9**: Technical indicators expanded

---

## Phase 12: Polish & Cross-Cutting Concerns (Days 41-43)

### T067 [P] - Add Streamlit Auto-Refresh for Risk Dashboard
**Story**: Polish
**File**: `myinvest-app/src/myinvest_app/ui/12_risk.py`
**Description**: 5-second auto-refresh
- Import streamlit-autorefresh
- Add `st_autorefresh(interval=5000, key="risk_refresh")`
- Test: Dashboard refreshes every 5 seconds

### T068 [DEPRECATED] - Chinese Localization Enforcement Audit
**Story**: Polish (NOTE: Core localization moved to T003b in Phase 1)
**File**: `myinvest-app/src/myinvest_app/ui/*.py`
**Description**: Constitution Principle I compliance audit (NOT initial implementation)
- **NOTE**: This task is now a VERIFICATION step, not initial implementation
- **Primary Chinese localization established in T003b (Phase 1)**
- Audit all UI pages for missed English text:
  - Date pickers: verify Chinese month/day names
  - Dropdown selectors: verify Chinese option labels
  - Streamlit built-in widgets: verify locale configuration
- Search codebase for hardcoded English strings: `grep -r "st\.(title|header|button|text_input)" --include="*.py" | grep -v "_("`
- Test: Zero hardcoded English strings found in user-facing UI
- **This is now a quality gate, not a retrofitting task**

### T069 [P] - Add Data Source Freshness Indicators
**Story**: Polish
**File**: `myinvest-app/src/myinvest_app/ui/`
**Description**: Display data source and timestamp
- Add badge: "数据源: efinance | 更新: 2025-10-22 15:32"
- Show data freshness: "实时" (green) | "延迟15分钟" (yellow) | "历史数据" (gray)
- Test: Data source displayed on all relevant pages

### T070 [P] - Implement Configuration Validation Tests
**Story**: Polish
**File**: `tests/unit/test_config_validation.py`
**Description**: Unit tests for Pydantic config
- Test: force_close_margin_rate < default_margin_rate
- Test: Invalid values rejected (e.g., margin_rate=1.5)
- Test: .env file loads correctly
- Test: All validators pass

### T071 [P] - Add Error Logging for All Modules
**Story**: Polish
**File**: All modules
**Description**: Comprehensive error logging
- Add Python logging.getLogger(__name__)
- Log errors with context (symbol, operation, error message)
- Chinese error messages where user-facing
- Test: Errors logged to file

### T072 [P] - Create End-to-End Integration Test Suite
**Story**: Polish
**File**: `tests/integration/`
**Description**: Integration tests for critical flows
- test_watchlist_to_scheduler_sync.py
- test_parallel_backtest_10_stocks.py
- test_multi_asset_data_pipeline.py
- test_report_export_all_formats.py
- Test: All integration tests pass

### T073 - Performance Optimization: Cache Frequently Accessed Data
**Story**: Polish
**File**: `investlib-data/src/investlib_data/cache.py`
**Description**: Implement TTL-based API response caching layer (SINGLE-PROCESS cache for API calls)
- Cache market data API responses with 5-minute TTL (avoid redundant efinance/AkShare calls)
- Cache Greeks calculations with 60-second TTL (avoid recalculating Black-Scholes)
- Cache risk metrics with 5-second TTL (support dashboard auto-refresh without full recalc)
- **Scope clarification**: This is for caching API responses and computed results (not inter-process data sharing)
- **Not to be confused with**: T013 (SharedMemoryCache for parallel backtest workers)
- Test: Cache hit rate >80% for repeated queries within TTL window

### T074 - Memory Profiling and Optimization
**Story**: Polish
**File**: N/A
**Description**: Profile memory usage and optimize
- Use memory_profiler to identify leaks
- Optimize SharedMemoryCache cleanup
- Fix memory leaks in parallel backtest
- Test: 10-stock backtest uses <500MB RAM

### T075 - Create V0.3 User Documentation
**Story**: Polish
**File**: `docs/v0.3_user_guide.md`
**Description**: User guide in Chinese
- Watchlist management guide
- Parallel backtest guide
- Parameter optimization tutorial
- Report export instructions
- Futures/options trading guide
- Risk dashboard interpretation
- Test: Documentation covers all features

### T076 - Create V0.3 Developer Documentation
**Story**: Polish
**File**: `docs/v0.3_developer_guide.md`
**Description**: Developer documentation
- Architecture overview
- Database migration guide
- Adding new strategies guide
- Configuration management guide
- Test: Documentation complete

---

## Task Dependencies

### Parallel Execution Opportunities

**Phase 1 Setup** (All parallel):
- T001 [P], T002 [P], T003 [P], T004 [P] can run simultaneously

**Phase 2 Foundation** (Mostly sequential due to database dependencies):
- T005 → T008 (sequential: migrations must be ordered)
- T006, T007 can be written in parallel, applied sequentially in T008

**Phase 3 US1** (Mostly parallel):
- T009 [P] + T010 [P] can run in parallel
- T011 depends on T009 (needs database layer)
- T012 [P] can run in parallel with T011

**Phase 4 US2** (High parallelism):
- T013 [P] + T014 [P] + T016 [P] + T017 [P] can all run in parallel
- T015 depends on T013 + T014 (needs shared cache + refactored runner)
- T018 depends on T015 (needs orchestrator)

**Phase 5 US3** (High parallelism):
- T019 [P] + T020 [P] + T021 [P] + T022 [P] + T023 [P] can all run in parallel
- T024 depends on T020 + T023 (needs grid search + visualizer)

**Phase 6 US4** (High parallelism):
- T025 [P] + T026 [P] + T027 [P] + T028 [P] + T029 [P] can all run in parallel
- T030 depends on T027 + T028 + T029 (needs all generators)

**Phase 7 US5** (High parallelism):
- T031 [P] through T036 [P] can all run in parallel (different files)
- T037 depends on T034 (needs base classes)
- T038 depends on T031 + T037 (needs margin calc + engines)
- T039 depends on T032 + T037 (needs Greeks + engines)
- T040 depends on T031 + T032 (needs new data types)

**Phase 8 US6** (High parallelism):
- T041 [P] through T046 [P] can all run in parallel (different modules)
- T047 depends on T042 through T046 (needs all calculators)
- T048 depends on T047 (needs orchestrator)

**Phase 9 US7** (High parallelism):
- T049 [P] + T050 [P] + T051 [P] + T052 [P] + T053 [P] can all run in parallel
- T054 depends on T050 + T051 + T052 (needs models + calculators)
- T055 depends on T050 + T053 + T054 (needs models + chart + backtest)
- T056 depends on T050 (needs models)

**Phase 10 US8** (Moderate parallelism):
- T057 [P] + T058 [P] can run in parallel
- T059 depends on T057 + T058
- T060 depends on T059

**Phase 11 US9** (High parallelism):
- T061 [P] through T064 [P] can all run in parallel
- T065 depends on T061-T064 (needs all indicators)
- T066 depends on T065

**Phase 12 Polish** (High parallelism):
- T067 [P] through T072 [P] can all run in parallel
- T073, T074, T075, T076 can run in parallel

### Critical Path

Longest sequential dependency chain (critical path):
1. T002 (Alembic setup)
2. T005 (Migration 001: Watchlist table)
3. T008 (Apply migrations)
4. T009 (Watchlist database layer)
5. T011 (Scheduler integration)
6. T034 (BaseStrategy subclasses)
7. T037 (Upgraded BacktestEngine)
8. T047 (Risk dashboard orchestrator)
9. T048 (Risk dashboard UI)

**Critical Path Duration**: ~15 days (if executed sequentially without parallelism)

**With Optimal Parallelism**: ~35-43 days for full V0.3 implementation

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Recommended MVP**: User Story 1 only (Watchlist Management)
- Tasks: T001-T004 (Setup) + T005-T008 (Foundation) + T009-T012 (US1)
- **Total**: 16 tasks
- **Duration**: 6 days
- **Value**: Eliminates hardcoded watchlists, enables dynamic stock management

### Incremental Delivery Phases

**Phase 1 MVP (Days 1-6)**: US1 - Watchlist Management
- Delivers: UI-based watchlist CRUD, scheduler integration
- Tests: Independent test criteria for US1

**Phase 2 Performance (Days 7-9)**: US2 - Parallel Backtesting
- Delivers: 10x performance improvement in backtesting
- Tests: 10 stocks in <3 minutes

**Phase 3 Advanced Features (Days 10-29)**: US3-7 (P1 Stories)
- Delivers: Parameter optimization, report export, futures/options, risk dashboard, combination strategies
- Tests: Each story independently testable

**Phase 4 Enhancements (Days 30-40)**: US8-9 (P2 Stories)
- Delivers: Multi-timeframe strategies, technical indicators
- Tests: Optional enhancements

**Phase 5 Polish (Days 41-43)**: Cross-cutting concerns
- Delivers: Performance optimization, documentation, final testing

### Test-First Development (TDD) Approach

**MANDATORY per Constitution Principle III**: Test-First Development is NON-NEGOTIABLE.

**Implementation**:
- While individual test task IDs are not listed, TDD workflow MUST be followed for EVERY implementation task
- Before implementing ANY task: Write contract/unit test → Get user approval → Run test (RED) → Implement code (GREEN) → Refactor
- Contract tests required before new library implementation: test_margin_calculator.py (before T031), test_greeks_engine.py (before T032), test_risk_metrics.py (before T041), test_optimizer.py (before T019)
- Integration tests required after each user story phase: test_watchlist_scheduler_sync.py (after US1), test_parallel_backtest_10_stocks.py (after US2), etc.
- `/speckit.implement` will enforce TDD gates at each task execution