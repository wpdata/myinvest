# Feature Specification: MyInvest v0.2 - Multi-Strategy System with Real Market Data Integration

**Feature Branch**: `002-myinvest-v0-2`
**Created**: 2025-10-16
**Status**: Draft
**Depends On**: v0.1 (User Stories 1-4 completed)

---

## Executive Summary

V0.2 focuses on **transitioning from prototype to production-ready system** by:

1. **完整集成真实市场数据** - Ensuring ALL components use real Tushare/AKShare APIs (not test data)
2. **多策略系统** - Adding Kroll strategy and multi-advisor fusion engine
3. **历史回测验证** - Implementing backtest engine with 3+ years of real historical data
4. **自动化运营** - Daily automated recommendation generation with real market data
5. **策略审批流程** - Strategy approval workflow for risk management

**Key Principle**: All strategies, backtests, and recommendations MUST use real market data from Day 1 of V0.2.

---

## Problem Statement

### Current State (V0.1)
- ✅ Market data APIs implemented (TushareClient, AKShareClient)
- ✅ Basic Livermore strategy logic exists
- ⚠️ **But most components still use test/mock data**
- ⚠️ No real end-to-end data flow from Tushare → Strategy → Recommendation
- ⚠️ Only single strategy (Livermore), no validation through backtesting
- ⚠️ Manual recommendation generation only

### Target State (V0.2)
- ✅ **100% real data integration** - Every component fetches from Tushare/AKShare
- ✅ Two validated strategies (Livermore + Kroll) using real historical data
- ✅ Multi-strategy fusion with configurable weights
- ✅ Backtest engine validates strategies on 3+ years of real data
- ✅ Automated daily data refresh and recommendation generation
- ✅ Strategy approval workflow ensures only validated strategies go live

---

## User Scenarios & Testing *(mandatory)*

### User Story 5 (P0) - Complete Real Data Integration (FOUNDATIONAL)

**Priority Rationale**: This is the FOUNDATION for all other V0.2 features. Without real data flowing through the system, backtesting and multi-strategy are meaningless.

**As** a system architect, **I want** ALL system components to use real Tushare/AKShare data, **so that** recommendations are based on actual market conditions, not test fixtures.

**Acceptance Scenarios**:

1. **Given** user triggers "Generate Recommendations" for symbol 600519.SH, **When** the system analyzes, **Then** it fetches latest data from Tushare API (not test data), displays API source "Tushare v1.2.85" and fresh timestamp
2. **Given** Livermore strategy runs analysis, **When** it calculates indicators (MA120, MACD), **Then** calculations use real OHLCV data from Tushare with data_freshness="realtime"
3. **Given** Tushare API fails (rate limit or network error), **When** system retries 3 times, **Then** it falls back to AKShare and displays warning "Using AKShare fallback, Tushare unavailable"
4. **Given** both APIs fail, **When** system checks cache, **Then** it uses cached data (if within 7-day retention) and displays prominent warning "Using cached data from [timestamp]"
5. **Given** user views market data page, **When** K-line chart loads, **Then** chart displays real daily data for past 12 months with data source badge

**Technical Requirements**:
- FR-101: Livermore strategy MUST call `MarketDataFetcher.fetch_with_fallback()` for real data
- FR-102: Kroll strategy MUST use same real data pipeline
- FR-103: All strategy analysis MUST log data source (Tushare/AKShare/Cache) and timestamp
- FR-104: Dashboard MUST display data freshness indicator for every recommendation
- FR-105: System MUST track API call success rate (target: >95% for Tushare)

**Success Metrics**:
- 100% of recommendations display "Data Source: Tushare v1.2.85 | Retrieved: 2025-10-16 15:32"
- 0 test fixtures used in production recommendation flow
- API fallback works: Tushare fail → AKShare success within 5 seconds

---

### User Story 6 (P1) - Kroll Strategy with Real Data Validation

**As** a conservative investor, **I want** a risk-focused Kroll strategy that analyzes real market data, **so that** I get recommendations with tighter risk controls than Livermore.

**Kroll Strategy Characteristics**:
- **Philosophy**: 风险优先，稳健增长（Risk-first, steady growth）
- **Position Sizing**: Max 12% per position (vs Livermore 20%)
- **Stop-Loss**: Tighter stop at entry - 2.5% (vs Livermore -3.5%)
- **Entry Signal**: Price > MA60 + Volume > 1.5x average + RSI < 70 (avoid overbought)
- **Take-Profit**: Conservative +5% (vs Livermore +7%)

**Acceptance Scenarios**:

1. **Given** real market data shows 600519.SH price at 1650, MA60 at 1600, volume 1.6x average, RSI at 65, **When** Kroll strategy analyzes, **Then** it generates BUY signal with entry=1650, stop_loss=1608.75 (-2.5%), take_profit=1732.50 (+5%), position=12%
2. **Given** real market data shows RSI > 70 (overbought), **When** Kroll analyzes, **Then** it returns HOLD signal with reasoning "Market overbought, wait for pullback"
3. **Given** Kroll generates recommendation, **When** user views explanation, **Then** they see "Risk Level: LOW | Max Loss: 1.5% of portfolio | Kroll Confidence: HIGH"
4. **Given** market shows high volatility (ATR > 3%), **When** Kroll analyzes, **Then** it reduces position size to 8% and displays warning "High volatility, reduced position"

**Technical Requirements**:
- FR-106: Kroll strategy MUST fetch real data via `MarketDataFetcher`
- FR-107: Kroll MUST calculate RSI(14), MA60, ATR from real OHLCV data
- FR-108: Kroll MUST enforce stop_loss = entry * 0.975 (mandatory -2.5%)
- FR-109: Kroll MUST log advisor_version="kroll-v1.0.0" in all recommendations
- FR-110: Kroll prompt template MUST be version-controlled at `investlib-advisors/prompts/kroll-v1.0.0.md`

**Data Requirements**:
- Minimum 60 trading days of real historical data for MA60 calculation
- Real-time or delayed (<15 min) data for entry signal generation

---

### User Story 7 (P1) - Multi-Strategy Fusion with Configurable Weights

**As** an investor, **I want** to configure weights between Kroll and Livermore strategies, **so that** I can balance risk and return based on my preferences.

**Fusion Logic**:
```
Final Recommendation = (Kroll Output × Kroll Weight) + (Livermore Output × Livermore Weight)

Confidence Adjustment:
- Both advisors agree (both BUY or both SELL): Confidence *= 1.3
- One BUY, one HOLD: Confidence *= 1.0 (neutral)
- One BUY, one SELL: Confidence *= 0.5, display ⚠️ CONFLICT WARNING
```

**Acceptance Scenarios**:

1. **Given** user sets weights to 60% Kroll + 40% Livermore, **When** system generates recommendations, **Then** UI displays three cards: "Kroll Recommendation", "Livermore Recommendation", "Fused Recommendation (60K/40L)"
2. **Given** Kroll says BUY (12% position) and Livermore says BUY (20% position), **When** fusion calculates with 60/40 weights, **Then** fused recommendation shows BUY with position=14.8% (12×0.6 + 20×0.4) and Confidence=HIGH×1.3
3. **Given** Kroll says HOLD and Livermore says BUY, **When** fusion calculates, **Then** fused recommendation shows BUY with lower confidence and note "Kroll advises caution"
4. **Given** Kroll says SELL and Livermore says BUY, **When** fusion calculates, **Then** UI displays prominent warning "⚠️ ADVISOR CONFLICT: Kroll recommends SELL, Livermore recommends BUY. Review carefully before acting."
5. **Given** user adjusts weight slider to 80% Kroll + 20% Livermore, **When** they click "Save Configuration", **Then** system saves to database and displays "Weights updated. Next recommendations will use 80/20 split."

**Technical Requirements**:
- FR-111: Fusion engine MUST call both Kroll and Livermore with SAME real market data
- FR-112: Fused position size = (kroll_pos × kroll_weight) + (livermore_pos × livermore_weight)
- FR-113: Fused stop_loss = weighted average of both stop losses
- FR-114: System MUST detect conflicts (|action_kroll - action_livermore| > threshold) and flag warnings
- FR-115: Weight configuration MUST be persisted in `strategy_config` table

---

### User Story 8 (P1) - Historical Backtest with Real Data

**As** an investor, **I want** to backtest strategies on 3 years of real historical data, **so that** I can validate performance before using them for live recommendations.

**Backtest Engine Requirements**:
- Use **real historical data** from Tushare (minimum 3 years = 2022-01-01 to 2024-12-31)
- Simulate daily signal generation and trade execution
- Calculate realistic transaction costs (0.03% commission, 0.1% slippage)
- Generate comprehensive performance metrics

**Acceptance Scenarios**:

1. **Given** user selects "Backtest Livermore Strategy" with period 2022-01-01 to 2024-12-31 and initial capital ¥100,000, **When** backtest runs, **Then** system fetches 3 years of real daily data from Tushare for configured symbols, displays progress bar "Fetching data: 600519.SH [1/10]"
2. **Given** backtest completes, **When** user views report, **Then** it displays metrics: Total Return +25.3%, Annualized Return +12.1%, Max Drawdown -15.8%, Sharpe Ratio 1.8, Win Rate 68% (34/50 trades)
3. **Given** backtest shows all trades, **When** user scrolls table, **Then** each row shows: Date | Symbol | Action | Entry Price | Exit Price | P&L | Data Source "Tushare"
4. **Given** backtest generates equity curve, **When** user views chart, **Then** chart shows daily portfolio value over 3 years with drawdown periods shaded in red
5. **Given** user wants to compare strategies, **When** they run backtest for both Kroll and Livermore with same period, **Then** system displays side-by-side comparison table: Livermore (Return +25%, Drawdown -15%) vs Kroll (Return +18%, Drawdown -8%)

**Technical Requirements**:
- FR-116: Backtest engine MUST fetch real historical data via `MarketDataFetcher` (no synthetic data)
- FR-117: Backtest MUST verify data completeness (no gaps > 5 trading days) before running
- FR-118: Backtest MUST log every trade with data_source and data_timestamp for audit
- FR-119: Backtest MUST calculate: total_return, annualized_return, max_drawdown, sharpe_ratio, sortino_ratio, win_rate, profit_factor
- FR-120: Backtest results MUST be saved to `backtest_results` table with metadata (strategy_version, data_period, initial_capital)

**Data Requirements**:
- 3+ years of daily OHLCV data from Tushare (≈730 trading days per symbol)
- Data adjustment method: qfq (前复权) for accurate historical analysis
- Minimum data quality: no more than 5 consecutive missing days

---

### User Story 9 (P2) - Automated Daily Recommendation Generation

**As** an investor, **I want** the system to automatically fetch real market data and generate recommendations every trading day after market close, **so that** I have fresh insights ready the next morning.

**Scheduler Requirements**:
- **Trigger Time**: Every weekday at 15:35 (5 minutes after China A-share market close)
- **Data Source**: Fetch latest real data from Tushare for all watchlist symbols
- **Tasks**: Generate Kroll + Livermore + Fused recommendations
- **Notification**: Store results in database, mark as "unread"

**Acceptance Scenarios**:

1. **Given** scheduled task runs at 15:35 on 2025-10-16, **When** task executes, **Then** system fetches real closing data for all symbols in user's watchlist from Tushare API, logs "Fetched 600519.SH: close=1680, volume=123456, source=Tushare v1.2.85"
2. **Given** real data fetched successfully, **When** task generates recommendations, **Then** it runs both Kroll and Livermore analysis using fresh data, saves 3 recommendation cards (Kroll, Livermore, Fused) to database with status="unread"
3. **Given** user logs in on 2025-10-17 morning, **When** they open dashboard, **Then** system displays banner "3 new recommendations from yesterday's close (2025-10-16 15:00)" with unread badge
4. **Given** scheduled task encounters API failure, **When** Tushare returns 429 (rate limit), **Then** system waits 60 seconds, retries with AKShare, logs error to `scheduler_log` table with details "Tushare rate limit, fallback to AKShare successful"
5. **Given** user views scheduler log page, **When** they filter by date 2025-10-16, **Then** table shows: execution_time=15:35:12, status=SUCCESS, symbols_processed=8, recommendations_generated=24, data_source=Tushare

**Technical Requirements**:
- FR-121: Scheduler MUST use APScheduler with CronTrigger "0 35 15 * * mon-fri"
- FR-122: Each execution MUST fetch real data via `MarketDataFetcher` for ALL watchlist symbols
- FR-123: Recommendations MUST include generation_time, data_timestamp, data_source in metadata
- FR-124: Failed executions MUST log error details and retry with exponential backoff (max 3 attempts)
- FR-125: Scheduler MUST update `scheduler_log` table with execution summary (success/failure, symbol count, duration)

---

### User Story 10 (P3) - Strategy Approval Workflow

**As** a portfolio manager, **I want** to approve backtested strategies before they're used for live recommendations, **so that** only validated strategies generate actionable signals.

**Approval Flow**:
1. Strategy completes backtest with satisfactory metrics
2. User clicks "Submit for Approval"
3. Approval page shows full backtest report + risk assessment
4. Approver reviews and adds notes, clicks "Approve" or "Reject"
5. Approved strategies can be used in live recommendation generation

**Acceptance Scenarios**:

1. **Given** Livermore backtest shows Sharpe > 1.5 and Max Drawdown < 20%, **When** user clicks "Submit for Approval", **Then** strategy status changes to "PENDING_APPROVAL" and appears in approval queue
2. **Given** approver opens approval page, **When** they review Livermore strategy, **Then** page displays: backtest metrics, equity curve chart, trade history, risk assessment "Medium Risk: Max Drawdown -15.8%"
3. **Given** approver adds note "Approved for 10% max position size" and clicks "Approve", **When** approval submits, **Then** strategy status changes to "APPROVED", approval record saved with timestamp/approver_id/notes, strategy available in live mode
4. **Given** strategy is approved, **When** daily scheduler generates recommendations, **Then** only APPROVED strategies are used, unapproved strategies are skipped with log "Skipped Kroll: status=PENDING_APPROVAL"

**Technical Requirements**:
- FR-126: Approval workflow MUST be enforced: only strategies with status="APPROVED" can generate live recommendations
- FR-127: Approval record MUST include: approver_id, approval_time, backtest_id, decision (APPROVED/REJECTED), notes
- FR-128: Approval page MUST display full backtest report from `backtest_results` table
- FR-129: Rejected strategies MUST log rejection reason and be excluded from live use

---

## Requirements *(mandatory)*

### Functional Requirements (FR-101 to FR-129 already defined above)

**Real Data Integration**:
- FR-130: ALL strategy analysis MUST start with `MarketDataFetcher.fetch_with_fallback()` call
- FR-131: System MUST track and display data source (Tushare/AKShare/Cache) for every recommendation
- FR-132: Data freshness MUST be calculated: realtime (<5s), delayed (5s-15min), historical (>15min)
- FR-133: Cache retention MUST be 7 days (from v0.1), expired cache auto-deleted
- FR-134: API failure rate MUST be monitored: log every failure with timestamp/symbol/error_message

**Strategy Implementation**:
- FR-135: Kroll strategy prompt MUST be version-controlled at `prompts/kroll-v1.0.0.md`
- FR-136: Kroll signal generation MUST require: price > MA60, volume > 1.5x, RSI < 70
- FR-137: Kroll position sizing MUST enforce: max 12% per position, total allocation ≤ 100%
- FR-138: Both strategies MUST log execution time and data timestamp for audit

**Backtest Engine**:
- FR-139: Backtest MUST use real historical data (minimum 3 years) from Tushare
- FR-140: Backtest MUST validate data quality: no gaps > 5 consecutive days
- FR-141: Backtest MUST simulate transaction costs: 0.03% commission + 0.1% slippage
- FR-142: Backtest MUST generate metrics: return, annualized_return, max_drawdown, sharpe_ratio, win_rate
- FR-143: Backtest MUST save complete trade log with entry/exit prices and data timestamps

**Automated Scheduler**:
- FR-144: Scheduler MUST run weekdays at 15:35 (after market close)
- FR-145: Scheduler MUST fetch real closing data for all watchlist symbols
- FR-146: Scheduler MUST generate Kroll + Livermore + Fused recommendations
- FR-147: Scheduler MUST handle API failures with retry and fallback logic
- FR-148: Scheduler MUST log execution summary to `scheduler_log` table

---

## Key Entities (Data Model Extensions)

### New Tables for V0.2

**1. strategy_config**
- id (UUID, PK)
- user_id (FK, default "default_user")
- kroll_weight (FLOAT, 0-1)
- livermore_weight (FLOAT, 0-1)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

**2. backtest_results**
- id (UUID, PK)
- strategy_name (VARCHAR: "livermore" | "kroll" | "fused")
- strategy_version (VARCHAR: "v1.0.0")
- start_date (DATE)
- end_date (DATE)
- initial_capital (DECIMAL)
- final_capital (DECIMAL)
- total_return (FLOAT)
- annualized_return (FLOAT)
- max_drawdown (FLOAT)
- sharpe_ratio (FLOAT)
- win_rate (FLOAT)
- total_trades (INT)
- trade_log (JSONB: array of trades)
- created_at (TIMESTAMP)

**3. strategy_approval**
- id (UUID, PK)
- backtest_id (FK → backtest_results)
- status (ENUM: "PENDING_APPROVAL", "APPROVED", "REJECTED")
- approver_id (VARCHAR, default "default_user")
- approval_time (TIMESTAMP)
- rejection_reason (TEXT, nullable)
- notes (TEXT)

**4. scheduler_log**
- id (UUID, PK)
- execution_time (TIMESTAMP)
- status (ENUM: "SUCCESS", "FAILURE", "PARTIAL")
- symbols_processed (INT)
- recommendations_generated (INT)
- data_source (VARCHAR: "Tushare" | "AKShare" | "Cache")
- error_message (TEXT, nullable)
- duration_seconds (FLOAT)

### Extended Tables from V0.1

**investment_recommendation** (add columns):
- data_source (VARCHAR: "Tushare v1.2.85" | "AKShare v1.11.0")
- data_timestamp (TIMESTAMP: when market data was retrieved)
- data_freshness (ENUM: "realtime", "delayed", "historical")
- advisor_weights (JSONB: {"kroll": 0.6, "livermore": 0.4})
- is_automated (BOOLEAN: true if generated by scheduler)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Real Data Integration (P0 - CRITICAL)**:
- SC-201: 100% of live recommendations display data source badge (e.g., "Tushare v1.2.85 | 2025-10-16 15:32")
- SC-202: 0 test fixtures used in production recommendation pipeline
- SC-203: API fallback success rate > 98% (when Tushare fails, AKShare succeeds within 5s)
- SC-204: Data freshness correctly displayed: <5s = realtime (green), 5s-15min = delayed (yellow), >15min = historical (gray)

**Strategy Performance**:
- SC-205: Kroll strategy generates valid recommendations with required fields (entry, stop_loss, take_profit, position ≤ 12%)
- SC-206: Multi-strategy fusion correctly calculates weighted averages (test with 60/40, 80/20, 50/50 splits)
- SC-207: Conflict detection works: when Kroll=SELL and Livermore=BUY, system displays warning

**Backtest Validation**:
- SC-208: Backtest engine successfully runs 3-year test (2022-2024) using real Tushare data
- SC-209: Backtest report displays all required metrics (return, drawdown, sharpe, win_rate)
- SC-210: Trade log shows 100% real data timestamps (no synthetic/mock timestamps)

**Automation**:
- SC-211: Scheduler executes successfully for 5 consecutive days without manual intervention
- SC-212: Daily recommendations are generated within 10 minutes of market close (15:35-15:45)
- SC-213: Scheduler handles API failures gracefully (logs error, retries with fallback, continues execution)

**Approval Workflow**:
- SC-214: Only APPROVED strategies generate live recommendations (test by submitting unapproved strategy)
- SC-215: Approval records are immutable (append-only, cannot be modified after creation)

---

## Assumptions

- Tushare API token is available and has sufficient quota (recommend 200+ API calls/day)
- Market data APIs (Tushare/AKShare) provide at least 3 years of historical data
- China A-share market close time is 15:00, system can fetch data by 15:30
- Single user mode sufficient for V0.2 (user_id = "default_user")
- Backtest runs locally (no distributed computing needed for 3-year daily data)
- Strategy weights sum to 1.0 (enforced by UI sliders)
- Approval workflow uses simple approve/reject (no multi-level approval)

---

## Scope Boundaries

### In Scope for V0.2

**MUST HAVE (P0)**:
- Complete real data integration for ALL components
- Kroll strategy implementation with real data validation
- Multi-strategy fusion with configurable weights
- Historical backtest engine (3+ years real data)
- Automated daily scheduler with real data refresh

**SHOULD HAVE (P1)**:
- Strategy approval workflow
- API call monitoring and alerting
- Backtest comparison tool (side-by-side strategy comparison)

**COULD HAVE (P2)**:
- Email/SMS notifications for daily recommendations
- Advanced backtest metrics (Sortino ratio, Calmar ratio)
- Parameter optimization for strategies (grid search)

### Out of Scope for V0.2

- ❌ Real brokerage API integration (still simulated trading)
- ❌ Live trading mode (still simulation mode only)
- ❌ Multi-user support (single user sufficient)
- ❌ Intraday (minute-level) data (daily data only)
- ❌ Options/Futures strategies (stocks only)
- ❌ Machine learning strategy models
- ❌ Mobile app
- ❌ Real-time push notifications to mobile devices

---

## Dependencies

**From V0.1 (MUST BE COMPLETE)**:
- User Story 1: Investment record management and dashboard
- User Story 2: Livermore strategy (refactor to use real data)
- User Story 3: Simulated trading execution
- User Story 4: Market data visualization with K-line charts
- Foundation: TushareClient, AKShareClient, MarketDataFetcher

**External Dependencies**:
- Tushare API (primary) - requires active token with sufficient quota
- AKShare API (fallback) - free, no token required
- APScheduler 3.10+ for automated scheduling
- pandas_ta or ta-lib for technical indicators (RSI, ATR)
- Python 3.10+

**Data Dependencies**:
- Historical data: 3 years minimum (2022-01-01 to 2024-12-31) from Tushare
- Data quality: maximum 5 consecutive missing trading days allowed
- Data format: OHLCV + volume, qfq (前复权) adjustment

---

## Constraints

- Single user mode only (no concurrent users)
- Simulated trading only (no real money at risk)
- Daily data granularity only (no intraday/tick data)
- Backtest limited to 10 symbols max per run (performance constraint)
- Scheduler runs on local machine (not distributed)
- API rate limits: Tushare ~200 calls/day, AKShare no limit
- Database: SQLite for V0.2 (upgrade to PostgreSQL in V0.3)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Tushare API quota exhausted** | High | Medium | Implement aggressive caching (7 days), use AKShare fallback, monitor daily quota usage |
| **Historical data gaps** | High | Medium | Pre-validate data completeness before backtest, reject if gaps > 5 days, log warnings |
| **Strategy overfitting on 3-year data** | High | High | Use walk-forward validation, test on out-of-sample period (2025 data), require 3+ market conditions |
| **Scheduler fails silently** | Medium | Medium | Add health check endpoint, log all executions, send alert if no execution in 24h |
| **Real data reveals strategy flaws** | High | High | Start with paper trading only, require manual review of all signals, implement kill switch |

---

## Implementation Phases

### Phase 1: Real Data Integration (Week 1) - P0 CRITICAL
- Refactor Livermore strategy to use `MarketDataFetcher`
- Add data source logging to all recommendation cards
- Implement data freshness indicators
- Test end-to-end: Tushare → Strategy → Recommendation with real data

### Phase 2: Kroll Strategy (Week 1-2)
- Implement Kroll strategy logic (MA60, RSI, volume)
- Create Kroll prompt template v1.0.0
- Validate Kroll with real market data
- Integration tests with real API calls

### Phase 3: Multi-Strategy Fusion (Week 2)
- Build fusion engine with weight configuration
- Implement conflict detection
- Create strategy config UI
- Test with real data from both advisors

### Phase 4: Backtest Engine (Week 2-3)
- Implement backtest core engine
- Fetch 3-year historical data from Tushare
- Calculate performance metrics
- Generate backtest reports with charts

### Phase 5: Automation & Approval (Week 3)
- Implement APScheduler for daily runs
- Build strategy approval workflow
- Add scheduler monitoring and logs
- End-to-end testing with real market schedule

---

## Quality Gates

**Before marking V0.2 complete**:
- ✅ All recommendations show real data source (not "test_data")
- ✅ Kroll strategy passes 10+ test cases with real data
- ✅ Backtest runs successfully on 3 years real data (2022-2024)
- ✅ Fusion engine correctly handles 60/40, 80/20, 50/50 weight splits
- ✅ Scheduler runs successfully for 5 consecutive days
- ✅ API fallback tested: Tushare fails → AKShare succeeds
- ✅ Data freshness indicators display correctly (realtime/delayed/historical)
- ✅ All integration tests pass with real API calls (no mocks)

---

**Document Version**: v1.0
**Last Updated**: 2025-10-16
**Status**: ✅ Ready for Planning Phase
