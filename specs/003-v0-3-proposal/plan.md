# Implementation Plan: MyInvest V0.3 - Production-Ready Enhancement

**Branch**: `003-v0-3-proposal` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-v0-3-proposal/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

V0.3 enhances MyInvest to production-ready status by addressing critical operational pain points and expanding trading capabilities. Key improvements include:

1. **Watchlist UI Management** (P0) - Eliminate hardcoded watchlists with database-backed UI management
2. **Parallel Backtesting** (P0) - 10x performance improvement through multi-core parallelization (10+ min → <3 min for 10 stocks)
3. **Strategy Parameter Optimization** (P1) - Automated grid search with walk-forward validation and overfitting detection
4. **Professional Report Export** (P1) - PDF/Excel/Word export with charts, metrics, and compliance disclaimers
5. **Futures & Options Support** (P1) - Multi-asset trading with margin calculations, Greeks, forced liquidation, and bidirectional positions
6. **Risk Monitoring Dashboard** (P1) - Real-time VaR, CVaR, concentration, margin usage, and correlation analysis
7. **Combination Strategy Builder** (P1) - UI-driven multi-leg strategy construction for spreads and combinations
8. **Multi-Timeframe Strategies** (P2) - Weekly trend + daily timing signal combinations
9. **Technical Indicator Expansion** (P2) - MACD, KDJ, Bollinger Bands, volume patterns

**Architectural Approach**: V0.3 builds on V0.1/V0.2 foundation by upgrading existing components (MarketDataFetcher, BaseStrategy, BacktestEngine, Scheduler) rather than rebuilding. New modules added only for derivatives-specific functionality. Database schema evolution via Alembic migrations preserves existing data. UI framework migration enables complex interactive features (drag-and-drop, real-time updates, heatmaps) while maintaining backward compatibility.

## Technical Context

**Language/Version**: Python 3.10+ (matches V0.1/V0.2)
**Primary Dependencies**:
  - Data: efinance (primary), AkShare (fallback), scipy (Greeks/VaR)
  - Persistence: SQLite + Alembic (schema migrations)
  - Reporting: reportlab/weasyprint (PDF), openpyxl (Excel), python-docx (Word)
  - Configuration: pydantic[dotenv] (type-safe centralized config)
  - Parallelization: ProcessPoolExecutor (built-in)
  - UI Framework: NEEDS CLARIFICATION (migrating from V0.1/V0.2 framework - specific target framework TBD)

**Storage**: SQLite database (existing from V0.1/V0.2, evolved via Alembic migrations)
  - New tables: watchlist, contract_info, combination_strategy
  - Extended tables: positions (asset_type, direction, margin_used), trades (asset_type, direction, margin_used)
  - Preserved: All V0.1/V0.2 data (investment_records, backtest_results, operation_log)

**Testing**: pytest (matches V0.1/V0.2)
  - Contract tests: New library APIs (margin calculator, Greeks engine, risk metrics)
  - Integration tests: Multi-asset data flow, parallel backtest orchestration, scheduler-watchlist sync
  - Unit tests: Parameter optimization algorithms, report generators, combination strategy builders

**Target Platform**: Desktop (macOS/Linux/Windows) - single-user local application

**Performance Goals**:
  - Parallel backtesting: 10 stocks in <3 minutes (current: 10+ minutes) on 8-core CPU
  - UI responsiveness: All operations <1 second
  - Scheduler execution: 20 stocks in <5 minutes
  - Risk dashboard: Auto-refresh every 5 seconds with real-time price updates

**Constraints**:
  - Backward compatibility: V0.1/V0.2 core workflows must remain functional during UI migration
  - Data preservation: Zero data loss during schema migrations, rollback capability required
  - Memory management: Parallel workers must detect and adapt to low-memory conditions
  - API rate limits: efinance primary with automatic fallback to AkShare

**Scale/Scope**:
  - User stories: 9 (2 P0, 5 P1, 2 P2)
  - Functional requirements: 82 (FR-001 to FR-082)
  - Success criteria: 23 measurable outcomes
  - Expected user base: Single user (multi-user deferred to V0.5)
  - Asset coverage: Stocks (existing) + futures + options
  - Strategy count: 2 stock strategies (Livermore, Kroll from V0.2) + new derivative-specific strategies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. 中文优先 (Chinese-First Interface)
**Status**: ✅ PASS (Research complete, implementation plan ready)

**Compliance**:
- All user-facing text in new UI features (watchlist management, parameter optimizer, report export, risk dashboard, combination builder) MUST use Chinese
- Error messages for new features (margin warnings, forced liquidation alerts, data validation) MUST use Chinese
- Exported reports (PDF/Excel/Word) MUST use Chinese for all labels, headers, and disclaimers

**Phase 0 Research COMPLETE** (research.md Decision 1):
- ✅ **GATE 1**: UI framework decision made - Continue with Streamlit (proven Chinese support in V0.1/V0.2)
- ✅ **GATE 2**: Internationalization support confirmed - streamlit-gettext provides i18n capabilities
- ✅ **GATE 3**: Font configuration strategy documented:
  - Streamlit UI: System Chinese fonts (SimHei, Microsoft YaHei, Noto Sans CJK)
  - PDF reports: ReportLab with TTF embedding (SimSun.ttf or Noto Sans CJK)
  - Chart rendering: Matplotlib with fontproperties configuration

**Implementation Plan**:
1. ✅ Research complete (research.md exists with UI framework decision)
2. T003b: Setup Chinese localization infrastructure in Phase 1 (BLOCKS all UI tasks)
3. All UI tasks (T010, T024, T030, T048, T055, T060, T066) mandate Chinese-first from Day 1
4. T068: Final compliance audit before release

### II. Library-First Architecture
**Status**: ✅ PASS

**Compliance**:
- New derivatives functionality organized as separate testable modules:
  - `investlib-margin`: Margin calculation engine (futures/options)
  - `investlib-greeks`: Options Greeks calculator (Black-Scholes)
  - `investlib-risk`: Risk metrics engine (VaR, CVaR, correlation)
  - `investlib-optimizer`: Parameter optimization engine (grid search, walk-forward)
  - `investlib-export`: Report generation library (PDF/Excel/Word)
- All new libraries have clear interfaces, unit tests, and documentation
- Upgrades to existing libraries maintain interface compatibility:
  - `investlib-data`: Extended for futures/options data fetching
  - `investlib-backtest`: Extended for multi-asset support
  - `investlib-advisors`: Extended base classes, new derivative strategies

### III. Test-First Development (NON-NEGOTIABLE)
**Status**: ✅ PASS (MUST enforce during implementation)

**Requirements**:
- Contract tests MUST be written and approved before implementing:
  - Margin calculation accuracy (futures)
  - Greeks calculation accuracy (options)
  - Parallel backtest orchestration
  - Schema migration rollback
- Integration tests MUST cover:
  - End-to-end parallel backtest with error isolation
  - Watchlist-to-scheduler sync without restart
  - Multi-asset data fetching with fallback
  - Report export with all formats (PDF/Excel/Word)
- Walk-forward validation tests MUST detect overfitting correctly

### IV. Integration Testing
**Status**: ✅ PASS

**Focus Areas**:
- **Contract changes**: BaseStrategy extended for FuturesStrategy/OptionsStrategy - test polymorphic backtest engine dispatch
- **Service communication**: Scheduler reads watchlist database - test sync without restart
- **Shared schema**: Database migrations preserve V0.1/V0.2 data - test rollback on failure
- **Multi-asset data pipeline**: MarketDataFetcher extended for futures/options - test fallback (efinance→AkShare, upgrading from V0.2's Tushare→AkShare)

### V. Data Quality & Freshness
**Status**: ✅ PASS (enhanced for derivatives)

**Compliance**:
- All futures/options data MUST display data source label (efinance/AkShare/Cache)
- Data source upgrade: V0.3 migrates from V0.2's Tushare→AkShare fallback to efinance→AkShare fallback for all asset types
- Futures contract rollover MUST maintain continuous data without gaps
- Options data completeness MUST be validated, warnings displayed for missing data
- Risk dashboard MUST show data freshness indicator with auto-refresh timestamp
- Report exports MUST include data retrieval timestamp and source attribution

**Constitution Verdict**: ✅ ALL GATES PASSED - Proceed to Phase 0 research

## Project Structure

### Documentation (this feature)

```
specs/003-v0-3-proposal/
├── spec.md              # Feature specification (COMPLETE)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command - PENDING)
├── data-model.md        # Phase 1 output (/speckit.plan command - PENDING)
├── quickstart.md        # Phase 1 output (/speckit.plan command - PENDING)
├── contracts/           # Phase 1 output (/speckit.plan command - PENDING)
│   ├── margin-calculator.yaml
│   ├── greeks-engine.yaml
│   ├── risk-metrics.yaml
│   ├── parameter-optimizer.yaml
│   └── report-exporter.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
# V0.3 extends existing V0.1/V0.2 structure

# Core libraries (existing from V0.1/V0.2, UPGRADED in V0.3)
investlib-data/
├── src/investlib_data/
│   ├── database.py           # Existing (V0.1) - UPGRADE: Add Alembic migrations
│   ├── market_api.py         # Existing (V0.2) - UPGRADE: Extend for futures/options
│   └── migrations/           # NEW: Alembic migrations for V0.3 schema changes
└── tests/

investlib-backtest/
├── src/investlib_backtest/
│   ├── engine.py            # Existing (V0.2) - UPGRADE: Multi-asset polymorphic dispatch
│   ├── runner.py            # Existing (V0.2) - UPGRADE: Add ParallelBacktestRunner
│   └── report.py            # Existing (V0.2) - EXTEND: Add export format support
└── tests/

investlib-advisors/
├── src/investlib_advisors/
│   ├── base.py              # Existing (V0.2) - UPGRADE: Add StockStrategy/FuturesStrategy/OptionsStrategy
│   ├── livermore.py         # Existing (V0.1) - NO CHANGE (stock-only)
│   ├── kroll.py             # Existing (V0.2) - NO CHANGE (stock-only)
│   ├── futures/             # NEW: Derivative-specific strategies
│   │   ├── trend_following.py
│   │   └── arbitrage.py
│   └── options/             # NEW: Derivative-specific strategies
│       ├── covered_call.py
│       └── protective_put.py
└── tests/

# NEW libraries for V0.3
investlib-margin/            # NEW: Margin and liquidation logic
├── src/investlib_margin/
│   ├── calculator.py        # Margin requirement calculations
│   ├── liquidation.py       # Forced liquidation detection
│   └── config.py            # Margin rate configuration
└── tests/

investlib-greeks/            # NEW: Options Greeks calculations
├── src/investlib_greeks/
│   ├── black_scholes.py     # Black-Scholes model
│   ├── calculator.py        # Delta, Gamma, Vega, Theta
│   └── aggregator.py        # Portfolio Greeks aggregation
└── tests/

investlib-risk/              # NEW: Risk metrics engine
├── src/investlib_risk/
│   ├── var.py               # VaR and CVaR calculations
│   ├── concentration.py     # Position concentration analysis
│   ├── correlation.py       # Correlation matrix
│   └── dashboard.py         # Risk dashboard orchestrator
└── tests/

investlib-optimizer/         # NEW: Parameter optimization
├── src/investlib_optimizer/
│   ├── grid_search.py       # Grid search engine
│   ├── walk_forward.py      # Walk-forward validation
│   ├── overfitting.py       # Overfitting detection
│   └── visualizer.py        # Heatmap generation
└── tests/

investlib-export/            # NEW: Report generation
├── src/investlib_export/
│   ├── pdf_generator.py     # PDF reports (reportlab/weasyprint)
│   ├── excel_generator.py   # Excel reports (openpyxl)
│   ├── word_generator.py    # Word reports (python-docx)
│   └── templates/           # Report templates
└── tests/

# Application layer (existing from V0.1/V0.2, UPGRADED/EXTENDED in V0.3)
myinvest-app/
├── src/myinvest_app/
│   ├── scheduler.py         # Existing (V0.2) - UPGRADE: Multi-asset + watchlist integration
│   ├── ui/                  # UPGRADE: Migrate to new UI framework
│   │   ├── 1_dashboard.py   # Existing (V0.1) - MIGRATE to new framework
│   │   ├── 2_records.py     # Existing (V0.1) - MIGRATE to new framework
│   │   ├── 3_recommendations.py  # Existing (V0.2) - MIGRATE to new framework
│   │   ├── 4_backtest.py    # Existing (V0.2) - MIGRATE to new framework
│   │   ├── 9_watchlist.py   # NEW: Watchlist management UI
│   │   ├── 10_optimizer.py  # NEW: Parameter optimizer UI
│   │   ├── 11_builder.py    # NEW: Combination strategy builder UI
│   │   └── 12_risk.py       # NEW: Risk monitoring dashboard UI
│   └── config/              # NEW: Centralized configuration
│       └── settings.py      # Pydantic BaseSettings
└── tests/

# Database
data/
├── myinvest.db              # Existing (V0.1/V0.2) - EVOLVED via migrations
└── migrations/              # NEW: Alembic migration history
    ├── versions/
    │   ├── v0.1_initial.py
    │   ├── v0.2_backtest_results.py
    │   └── v0.3_multi_asset.py
    └── alembic.ini

# Test organization
tests/
├── contract/                # Contract tests for new libraries
│   ├── test_margin_calculator.py
│   ├── test_greeks_engine.py
│   ├── test_risk_metrics.py
│   └── test_optimizer.py
├── integration/             # Integration tests for workflows
│   ├── test_parallel_backtest.py
│   ├── test_watchlist_scheduler_sync.py
│   ├── test_multi_asset_data_pipeline.py
│   └── test_report_export.py
└── unit/                    # Unit tests for individual modules
    ├── test_combination_builder.py
    ├── test_liquidation_logic.py
    └── test_migration_rollback.py
```

**Structure Decision**: Single project structure (Option 1) maintained from V0.1/V0.2. V0.3 extends with new libraries following library-first architecture. UI migration happens within existing myinvest-app structure. Database evolution managed in-place via Alembic migrations.

**Key Structural Decisions**:
1. **Library separation**: New derivatives functionality isolated in dedicated libraries (margin, greeks, risk) for testability
2. **Strategy isolation**: Livermore/Kroll untouched, new derivative strategies in separate modules
3. **Backward compatibility**: Existing V0.1/V0.2 modules upgraded via extension, not replacement
4. **Migration safety**: Database migrations versioned and reversible

## Complexity Tracking

*No complexity violations detected. V0.3 follows established V0.1/V0.2 patterns with library-first architecture.*

---

## Phase 0: Research & Technical Decisions

**Status**: PENDING

The following research tasks will be executed by specialized agents to resolve all NEEDS CLARIFICATION items and establish best practices:

### Research Tasks

1. **UI Framework Selection** (CRITICAL - blocks FR-080 to FR-082)
   - **Context**: Migrating from V0.1/V0.2 UI framework to support complex interactive features (drag-and-drop, real-time updates, heatmaps)
   - **Requirements**:
     - Chinese language support (i18n/l10n capabilities)
     - Real-time data updates (auto-refresh, WebSocket support)
     - Interactive components (drag-and-drop, dynamic forms)
     - Chart libraries (heatmaps, correlation matrices, P&L curves)
     - Backward compatibility path from V0.1/V0.2
   - **Research Questions**:
     - What are candidate frameworks for Python-based desktop UIs with advanced interactivity?
     - Which frameworks have proven Chinese localization support?
     - What is migration path from existing framework?
     - What are performance characteristics for real-time updates (5-second refresh)?
   - **Output**: Framework recommendation with migration strategy

2. **Parallel Backtesting Best Practices** (HIGH - affects FR-008 to FR-013)
   - **Context**: ProcessPoolExecutor for multi-core backtesting with error isolation
   - **Research Questions**:
     - How to handle shared state (market data cache) across worker processes?
     - What are memory management strategies for parallel workers?
     - How to implement reliable progress tracking with multiprocessing?
     - What are error isolation patterns for independent task failures?
   - **Output**: Parallelization architecture with memory management strategy

3. **Database Migration Strategy** (HIGH - affects FR-074 to FR-075)
   - **Context**: Alembic migrations for SQLite schema evolution with rollback
   - **Research Questions**:
     - What are best practices for SQLite migrations with Alembic?
     - How to test migration rollback scenarios?
     - How to handle data transformation during migrations (e.g., adding asset_type to existing trades)?
     - What are strategies for zero-downtime migrations in single-user desktop app?
   - **Output**: Migration framework setup with rollback testing strategy

4. **Options Greeks Calculation** (MEDIUM - affects FR-030, FR-049, FR-059)
   - **Context**: Black-Scholes model for Delta, Gamma, Vega, Theta
   - **Research Questions**:
     - What are proven Python libraries for Black-Scholes calculations?
     - How to handle missing volatility data (use historical vol)?
     - What are performance considerations for real-time Greeks updates?
     - How to aggregate Greeks across multi-leg option positions?
   - **Output**: Greeks calculation library with fallback strategies

5. **Risk Metrics Implementation** (MEDIUM - affects FR-042 to FR-046)
   - **Context**: VaR, CVaR, correlation matrix for multi-asset portfolios
   - **Research Questions**:
     - What are standard methods for VaR calculation (historical simulation vs parametric)?
     - How to handle futures leverage in VaR calculations?
     - What are efficient algorithms for correlation matrix calculation with auto-refresh?
     - How to calculate CVaR (Conditional VaR) from VaR results?
   - **Output**: Risk metrics algorithms with multi-asset considerations

6. **Report Generation Libraries** (MEDIUM - affects FR-020 to FR-025)
   - **Context**: PDF (reportlab/weasyprint), Excel (openpyxl), Word (python-docx)
   - **Research Questions**:
     - Which PDF library provides better Chinese font support (reportlab vs weasyprint)?
     - How to embed charts in PDF reports (matplotlib integration)?
     - What are best practices for Excel conditional formatting (profit/loss colors)?
     - How to handle large trade history tables in reports (pagination)?
   - **Output**: Report generation library selection with Chinese font configuration

7. **Centralized Configuration Management** (MEDIUM - affects FR-038 to FR-039)
   - **Context**: Pydantic BaseSettings for type-safe configuration
   - **Research Questions**:
     - How to structure nested settings (data_source, futures, options, risk)?
     - What are patterns for custom validators (e.g., forced liquidation < margin rate)?
     - How to support .env file with nested keys (using double underscore delimiter)?
     - How to provide IDE autocomplete for settings access?
   - **Output**: Configuration architecture with validation patterns

**Research Output**: `research.md` document containing all decisions, rationales, and alternatives considered

---

## Phase 1: Design & Contracts

**Status**: PENDING (awaits Phase 0 completion)

### Artifacts to Generate

1. **data-model.md**: Entity relationship diagram and schema definitions
   - Watchlist entity (symbol, group, status, date_added)
   - ContractInfo entity (futures/options specifications)
   - CombinationStrategy entity (multi-leg strategy structure)
   - Extended Position/Trade entities (asset_type, direction, margin_used)
   - Migration scripts (Alembic versions)

2. **contracts/** directory: API specifications for new libraries
   - `margin-calculator.yaml`: Margin calculation API (OpenAPI)
   - `greeks-engine.yaml`: Greeks calculation API (OpenAPI)
   - `risk-metrics.yaml`: Risk dashboard API (OpenAPI)
   - `parameter-optimizer.yaml`: Optimization engine API (OpenAPI)
   - `report-exporter.yaml`: Report generation API (OpenAPI)

3. **quickstart.md**: Developer onboarding guide
   - Environment setup (Python 3.10+, dependencies)
   - Database migration (Alembic commands)
   - Running parallel backtests
   - Generating reports
   - UI framework setup (post-migration)

4. **Agent context update**: Add V0.3 technologies to `.specify/memory/agent-context/`
   - Alembic migrations
   - Selected UI framework
   - New libraries (margin, greeks, risk, optimizer, export)
   - Pydantic configuration

**Phase 1 Output**: Complete design documentation ready for `/speckit.tasks` generation

---

## Implementation Roadmap

**Phase 2 (Post-Planning)**: Task generation via `/speckit.tasks`
- Break down user stories into concrete implementation tasks
- Prioritize P0 (watchlist, parallel backtest) → P1 (optimization, export, derivatives, risk, combination) → P2 (multi-timeframe, indicators)
- Establish dependencies between tasks (e.g., schema migration before watchlist UI)
- Generate acceptance test specifications for each task

**Phase 3 (Implementation)**: Execution via `/speckit.implement`
- Follow Test-First Development (write tests → approve → implement)
- Execute tasks in dependency order
- Validate Constitution compliance (Chinese UI, library-first)
- Run integration tests at each milestone

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| UI migration breaks V0.1/V0.2 workflows | HIGH | Incremental migration with backward compatibility testing; maintain old pages during transition |
| Schema migration data loss | HIGH | Comprehensive rollback tests; database backup before migration; test on copy first |
| Parallel backtest memory exhaustion | MEDIUM | Dynamic worker count based on available memory; progress checkpointing for recovery |
| Options Greeks calculation errors | MEDIUM | Extensive unit tests with known Black-Scholes values; compare against reference implementation |
| Chinese font rendering in PDF reports | LOW | Test font embedding early; select library with proven Chinese support |
| API rate limits during parallel operations | LOW | Implement rate limiting in MarketDataFetcher; use cached data when available |

---

## Success Validation

V0.3 implementation success will be validated through:

1. **Constitution Compliance**: All new UI pages pass Chinese language audit
2. **Performance Benchmarks**: 10-stock parallel backtest completes in <3 minutes on 8-core CPU
3. **Data Integrity**: Schema migrations preserve 100% of V0.1/V0.2 data with successful rollback tests
4. **Test Coverage**: All new libraries have >80% test coverage with contract tests approved
5. **Integration Validation**: End-to-end workflows (watchlist→scheduler→backtest→report) execute without errors
6. **User Acceptance**: V0.1/V0.2 core workflows (import records, view dashboard, generate recommendations) function identically post-migration

---

**Next Steps**:
1. Execute Phase 0 research via specialized agents (output: `research.md`)
2. Generate Phase 1 design artifacts based on research findings (output: `data-model.md`, `contracts/`, `quickstart.md`)
3. Update agent context with V0.3 technologies
4. Invoke `/speckit.tasks` to generate implementation task list
