# Research: MyInvest v0.1 Technology Decisions

**Date**: 2025-10-14
**Feature**: MyInvest v0.1 - Intelligent Investment Analysis System
**Purpose**: Document technology research, decisions, rationale, and alternatives

## Overview

This document captures the technology research and decisions made for MyInvest v0.1 implementation. All decisions prioritize:
- Rapid prototyping for v0.1 MVP
- Clear migration path to production-ready architecture (v0.2+)
- Constitution compliance (Library-First, CLI Interface, Test-First, etc.)
- Investment safety and data integrity

---

## 1. Market Data APIs

### Decision

**Primary**: Tushare (tushare) 1.2.85+
**Fallback**: AKShare (akshare) 1.11+

### Rationale

**Tushare chosen as primary** because:
- Comprehensive Chinese stock and futures data coverage
- Well-documented Python SDK with pandas integration
- Free tier sufficient for personal use (daily data, no real-time for v0.1)
- Proven reliability in quantitative trading community
- ISO 8601 timestamp support for data traceability
- Explicit version tracking (meets Constitution Principle VII: Data Integrity)

**AKShare as fallback** because:
- Completely free, no registration required
- Similar data coverage to Tushare
- Different data sources (redundancy for reliability)
- Simpler API but less consistent data quality
- Good for graceful degradation per Constitution Principle X

### Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| yfinance | Free, popular, global markets | US-focused, unreliable for Chinese stocks | Rejected |
| Baostock | Free, Chinese markets | Limited maintenance, older data format | Rejected |
| Wind / Bloomberg | Professional-grade data | Expensive, overkill for MVP | Deferred to production |

### Implementation Notes

- Tushare requires free token (register at tushare.pro)
- Store token in `.env` file (not committed to git)
- Wrap API calls in retry logic (3 attempts) before fallback to AKShare
- Cache all fetched data for 7 days (per clarification session)
- Record `api_source` field in all market data: `"Tushare v1.2.85"` or `"AKShare v1.11.0"`

### Rate Limits

- Tushare free tier: 200 API calls/minute, 2000/day (sufficient for v0.1)
- AKShare: No explicit rate limits (best-effort)
- Implement exponential backoff for both APIs

---

## 2. Web UI Framework

### Decision

**v0.1**: Streamlit 1.28+
**v0.2+**: Migrate to Google ADK

### Rationale

**Streamlit for v0.1** because:
- Fastest path to working prototype (hours, not days)
- Built-in multi-page app structure (`pages/` directory)
- Native session state management (no complex state libraries)
- Excellent Plotly/Pandas integration for charts
- Hot-reloading during development
- Single command deployment: `streamlit run app.py`
- Well-documented Chinese UI patterns (st.markdown for labels)

**Google ADK deferred to v0.2** because:
- Learning curve would slow MVP development
- Agent coordination complexity not needed for single Livermore advisor
- Streamlit provides sufficient orchestration for v0.1
- Clear migration path: Streamlit UI → Google ADK agents + UI

### Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Gradio | Similar to Streamlit, ML-focused | Less mature multi-page support | Rejected |
| Flask + React | Full control, production-ready | Weeks of frontend development | Deferred to production |
| Jupyter Notebook | Great for analysis | Poor for application UI | Rejected |
| Google ADK immediately | Constitution-aligned | Steep learning curve, slows MVP | Deferred to v0.2 |

### Implementation Notes

- Use Streamlit multi-page app structure:
  - `app.py` → Main entry point
  - `pages/1_dashboard.py` → Investment overview + recommendations
  - `pages/2_records.py` → Records management
  - `pages/3_market.py` → Market data charts
  - `pages/4_logs.py` → Operation logs
- Implement confirmation dialogs using `st.dialog()` decorator (Streamlit 1.28+)
- Use `st.session_state` for user confirmation workflow
- Display "Current Mode: Simulated Trading" using `st.info()` banner

### Migration Path to Google ADK (v0.2)

1. Refactor Livermore advisor to Google ADK agent
2. Keep investlib-* libraries unchanged (already library-first)
3. Replace Streamlit UI with Google ADK UI components
4. Preserve CLI interfaces (Constitution Principle II)

---

## 3. Livermore Strategy Implementation

### Decision

Implement trend-following strategy using:
- **Primary indicator**: 120-day moving average breakout
- **Confirmation**: Volume spike (>20% above 20-day average)
- **Secondary**: MACD golden cross (12/26/9 parameters)
- **Risk management**: ATR-based stop-loss (2x Average True Range)

### Rationale

**120-day MA chosen** because:
- Represents ~6 months of trading data (substantial trend)
- Well-known in Livermore's "pivot point" methodology
- Less noisy than shorter periods (50-day)
- Aligns with v0.1's daily data granularity

**Volume confirmation required** because:
- Reduces false breakouts
- Livermore emphasized "line of least resistance" = volume confirmation
- Easy to calculate from OHLCV data

**MACD as secondary** because:
- Momentum confirmation for trend
- Standard indicator (pandas_ta library)
- Explainable to users

**ATR for stop-loss** because:
- Adapts to stock volatility (volatile stocks get wider stops)
- Prevents premature stop-outs
- Industry-standard approach

### Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Fixed % stop-loss (5%) | Simple, easy to understand | Ignores volatility differences | Rejected |
| Support/resistance levels | Technically sound | Subjective, hard to automate | Deferred to v0.2 |
| Machine learning signals | Sophisticated | Black box, hard to explain | Out of scope for v0.1 |

### Implementation Notes

- Use `pandas_ta` library for technical indicators
- Calculate indicators in `investlib-quant/livermore_strategy.py`
- Historical precedent matching: Store last 50 breakouts with outcomes in database
- Explanation generation: Template-based (not LLM) for deterministic output

### Explainability Format

```python
{
    "signal": "BUY",
    "triggers": [
        "Price broke above 120-day MA (1650 → 1680)",
        "Volume 30% above average (confirms breakout)",
        "MACD golden cross formed"
    ],
    "historical_precedents": [
        {
            "date": "2023-03-15",
            "pattern": "Similar breakout at 1650",
            "outcome": "+12% over 15 days"
        }
    ],
    "confidence": "HIGH"  # Based on number of confirming signals
}
```

---

## 4. Database and ORM

### Decision

**v0.1**: SQLite 3.40+ with SQLAlchemy 2.0+
**v0.2+**: Migrate to PostgreSQL 15+

### Rationale

**SQLite for v0.1** because:
- Zero configuration (single file database)
- Sufficient for single-user local application
- Fast for <1000 records (expected data volume)
- Easy backup (copy .db file)
- Meets v0.1 scope (single user, local instance)

**SQLAlchemy 2.0+** because:
- Constitution Principle V: Use frameworks directly (no custom ORM)
- Modern declarative syntax (Mapped[], mapped_column())
- Built-in migration path to PostgreSQL (same ORM code)
- Type hints for IDE support
- Well-documented append-only log patterns

**PostgreSQL deferred to v0.2** because:
- Overkill for single-user v0.1
- Requires installation/setup (slows getting started)
- SQLite → PostgreSQL migration is straightforward with SQLAlchemy

### Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| PostgreSQL immediately | Production-ready, ACID | Overengineered for v0.1 | Deferred |
| MongoDB | Flexible schema | Not relational, overkill | Rejected |
| CSV files | Simple | No ACID, no relations | Rejected |
| DuckDB | Fast analytics | Less mature ecosystem | Considered for v0.2 |

### Implementation Notes

**5 SQLAlchemy Models** (one per entity from spec.md):

1. `InvestmentRecord` - Historical transactions
2. `MarketDataPoint` - OHLCV + metadata + cache_expiry
3. `InvestmentRecommendation` - AI-generated suggestions
4. `OperationLog` - Append-only audit trail (insert-only, no update/delete)
5. `CurrentHolding` - Portfolio positions

**Append-Only Log Implementation**:
```python
class OperationLog(Base):
    __tablename__ = "operation_log"

    # Prevent updates/deletes at ORM level
    __mapper_args__ = {"confirm_deleted_rows": False}

    # UUID primary key (not auto-increment for distributed future)
    operation_id = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    # Immutable created timestamp
    created_at = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # No updated_at field (append-only)
```

**Migration Strategy**:
- Use Alembic for schema migrations
- Initial migration creates all 5 tables
- Add indexes for query performance: symbol, timestamp, user_id

---

## 5. Visualization Library

### Decision

**Plotly 5.17+** for all charts (K-lines, profit/loss curves, asset distribution)

### Rationale

**Plotly chosen** because:
- Native Streamlit integration (`st.plotly_chart()`)
- Interactive charts (zoom, pan, hover tooltips)
- Built-in candlestick chart for K-lines (`go.Candlestick`)
- Responsive design (works on desktop/tablet)
- Professional appearance (important for investment UI)
- Extensive Chinese community examples

### Alternatives Considered

| Alternative | Pros | Cons | Decision |
|-------------|------|------|----------|
| Matplotlib | Widely used, simple | Static images, not interactive | Rejected |
| ECharts | Popular in China, beautiful | Requires JavaScript bridge | Deferred |
| Altair | Declarative, elegant | Less feature-rich than Plotly | Rejected |

### Implementation Notes

**Chart Types**:
- K-line chart: `plotly.graph_objects.Candlestick`
- Profit/loss curve: `plotly.express.line` with fill
- Asset distribution: `plotly.express.pie`
- Recommendation confidence: `plotly.graph_objects.Indicator` (gauge)

**Chinese Language Support**:
```python
fig.update_layout(
    title="累计收益曲线",  # Cumulative P&L Curve
    xaxis_title="日期",    # Date
    yaxis_title="收益 (%)", # Profit (%)
    font=dict(family="Microsoft YaHei, SimHei, sans-serif")  # Chinese fonts
)
```

---

## 6. Testing Strategy

### Decision

**Framework**: pytest 7.4+ with pytest-cov
**Approach**: Integration-first (Constitution Principle VI)

### Rationale

**Integration-first because**:
- Constitution Principle VI: "Integration tests MUST take priority over isolated unit tests"
- Real Tushare API calls in tests (no mocks for main flows)
- Real SQLite database (in-memory for speed: `sqlite:///:memory:`)
- Tests cover actual user workflows (import → recommend → execute)

**pytest chosen** because:
- Industry standard for Python
- Excellent fixture system for test data
- Plugin ecosystem (pytest-cov, pytest-xdist for parallel tests)
- Clear output for TDD workflow

### Test Structure

```
tests/
├── contract/            # CLI contract tests (every library)
│   ├── test_data_cli.py        # investlib-data --help, --dry-run
│   ├── test_quant_cli.py       # investlib-quant CLI
│   └── test_advisors_cli.py    # investlib-advisors CLI
├── integration/         # Integration tests (real APIs, real DB)
│   ├── test_import_csv.py      # CSV import with validation
│   ├── test_market_api.py      # Tushare/AKShare integration
│   ├── test_livermore_strategy.py  # Strategy with historical data
│   ├── test_recommendation_flow.py # End-to-end: data → recommend
│   └── test_api_failure.py     # Graceful degradation (retry → fallback)
└── unit/                # Unit tests (only for pure functions)
    ├── test_risk_calculator.py # Position sizing formulas
    └── test_validation.py      # Data validation rules
```

### Implementation Notes

**Test-First Workflow (Constitution Principle III)**:
1. Write contract tests for CLI (verify --help, --dry-run work)
2. Write integration tests with real APIs (expect FAIL)
3. Get approval from project owner
4. Verify tests FAIL (Red phase)
5. Implement feature
6. Verify tests PASS (Green phase)
7. Refactor for simplicity

**Real API Testing**:
- Use real Tushare API with test token (set in CI/CD secrets)
- Cache API responses for faster test runs (pytest-vcr)
- Mark slow tests with `@pytest.mark.slow` (run separately)

**Coverage Target**: >80% for investlib-* libraries

---

## 7. CLI Implementation

### Decision

Use **Click 8.1+** for CLI commands (all investlib-* libraries)

### Rationale

**Click chosen** because:
- Constitution Principle II: CLI Interface Mandate
- Industry-standard Python CLI framework
- Auto-generated --help documentation
- Easy to implement --dry-run flag
- Type validation built-in
- Supports piping (stdin/stdout for JSON)

### CLI Design Pattern

Every investlib-* library provides CLI commands:

```bash
# investlib-data commands
investlib-data init-db                    # Initialize database
investlib-data import-csv --file data.csv --dry-run
investlib-data fetch-market --symbol 600519.SH --output json

# investlib-quant commands
investlib-quant analyze --symbol 600519.SH --strategy livermore --output json
investlib-quant signals --input market_data.json --dry-run

# investlib-advisors commands
investlib-advisors ask --advisor livermore --context data.json --output json
investlib-advisors list-advisors
```

### Implementation Notes

**Required Flags (Constitution Principle II)**:
- `--help`: Auto-generated by Click
- `--dry-run`: Preview actions without executing
- `--output json`: Structured output for piping

**Example Implementation**:
```python
import click
import json

@click.command()
@click.option('--symbol', required=True, help='Stock symbol (e.g., 600519.SH)')
@click.option('--dry-run', is_flag=True, help='Preview without executing')
@click.option('--output', type=click.Choice(['text', 'json']), default='text')
def fetch_market(symbol, dry_run, output):
    """Fetch market data for a stock symbol"""
    if dry_run:
        click.echo(f"[DRY RUN] Would fetch data for {symbol}")
        return

    # Actual implementation...
    data = fetch_data_from_tushare(symbol)

    if output == 'json':
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        click.echo(f"Fetched {len(data)} data points for {symbol}")
```

---

## 8. AI Advisor Implementation

### Decision

**v0.1**: Template-based advisor (no LLM calls for Livermore)
**v0.2+**: Integrate LLM for dynamic reasoning

### Rationale

**Template-based for v0.1** because:
- Livermore strategy is rule-based (indicators + thresholds)
- No need for LLM reasoning in v0.1 (premature optimization)
- Deterministic output = testable, reproducible
- Faster execution (no API calls)
- Lower cost (no LLM API fees)

**Versioned prompts still implemented** because:
- Constitution Principle IX: "Advisor prompts MUST be version controlled"
- Future-proofing for LLM integration in v0.2
- Template versioning provides explainability
- Easy to A/B test template variations

### Implementation Notes

**Prompt Template (v1.0)**:
```markdown
# Livermore Advisor v1.0

## Strategy: Trend Following

### Buy Signal Conditions
1. Price breaks above 120-day MA
2. Volume >20% above 20-day average
3. MACD golden cross (12/26/9)

### Risk Management
- Stop-loss: 2x ATR below entry
- Position size: Risk 2% of capital per trade
- Take-profit: 3x risk (1:3 risk-reward ratio)

### Explanation Template
**Signal**: {action} {symbol}
**Entry**: {entry_price}
**Stop-Loss**: {stop_loss} (2x ATR = {atr_value})
**Take-Profit**: {take_profit}
**Position**: {position_pct}% ({position_amount} shares)
**Max Loss**: {max_loss_amount}

**Market Signals**:
{for signal in triggers}
- {signal}
{endfor}

**Historical Precedents**:
{for precedent in historical_matches}
- {precedent.date}: {precedent.pattern} → {precedent.outcome}
{endfor}

**Confidence**: {confidence} ({num_signals}/3 signals confirmed)
```

**Future LLM Integration (v0.2)**:
- Replace template with Google ADK agent
- Keep same versioning system (prompts/livermore-v2.0.md)
- Preserve structured output schema for compatibility

---

## Summary of Technology Stack

| Component | v0.1 Technology | v0.2+ Migration Path |
|-----------|-----------------|----------------------|
| Language | Python 3.10+ | Same |
| Web UI | Streamlit 1.28+ | Google ADK |
| Market Data | Tushare + AKShare | Same + professional APIs |
| Database | SQLite 3.40+ | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0+ | Same |
| Visualization | Plotly 5.17+ | Same or ECharts |
| Testing | pytest 7.4+ | Same |
| CLI | Click 8.1+ | Same |
| Advisors | Template-based | LLM (Google ADK agents) |

All decisions comply with Constitution Principles and prioritize rapid v0.1 MVP delivery with clear production migration path.

---

**Research Complete**: All technology decisions documented. Proceed to Phase 1: Design Artifacts.
