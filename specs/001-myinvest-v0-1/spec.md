# Feature Specification: MyInvest v0.1 - Intelligent Investment Analysis System

**Feature Branch**: `001-myinvest-v0-1`
**Created**: 2025-10-14
**Status**: Draft
**Input**: User description: "MyInvest v0.1 - Intelligent Investment Analysis System with Livermore Strategy"

## Clarifications

### Session 2025-10-14

- Q: How long should the system retain cached market data for fallback when APIs are unavailable? → A: 7 days (weekly analysis window)
- Q: When should the system generate investment recommendations? → A: On-demand only (user clicks "Generate Recommendations" button)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import and View Investment History (Priority: P1)

As an individual investor, I want to import my historical investment records and view my investment performance overview, so I can understand my past investment behavior and track my portfolio performance over time.

**Why this priority**: This is the foundation of the system. Without historical data, no analysis or recommendations can be generated. This story delivers immediate value by providing investment tracking and performance visualization.

**Independent Test**: Can be fully tested by importing a CSV file with 10+ investment records and verifying that the system displays a complete investment overview including total assets, profit/loss curve, and current holdings list. No other features need to be implemented.

**Acceptance Scenarios**:

1. **Given** the user has a CSV file with investment records, **When** they click "Import Investment Records" and select the file, **Then** the system validates the data and displays all successfully imported records in the investment records table
2. **Given** the user has imported investment records, **When** they view the dashboard, **Then** they see total assets, cumulative profit/loss curve (line chart), asset distribution pie chart, and current holdings list
3. **Given** the imported data contains validation errors (negative price, invalid date), **When** the system processes the data, **Then** it displays specific warning messages for each error and does not auto-correct the data
4. **Given** the user has investment records, **When** they click on the profit/loss curve, **Then** they can switch between daily, weekly, and monthly views

---

### User Story 2 - Receive Investment Recommendations with Safety Checks (Priority: P2)

As an individual investor using the Livermore trend-following strategy, I want to receive actionable investment recommendations with clear entry/exit points and risk parameters, so I can make informed investment decisions with proper risk management.

**Why this priority**: This is the core value proposition - providing data-driven, explainable investment recommendations. It builds on the foundation of Story 1 (historical data) and delivers the intelligence layer.

**Independent Test**: Can be tested by providing the system with market data for a specific stock, verifying that it generates a recommendation card with all mandatory fields (entry price, stop-loss, take-profit, position size, max loss), and confirming that recommendations without stop-loss are rejected.

**Acceptance Scenarios**:

1. **Given** market data shows a trend breakout signal for a stock, **When** the user clicks "Generate Recommendations" and the Livermore strategy analyzes the data, **Then** the system displays a "Today's Recommendation" card with symbol, action (BUY/SELL/HOLD), entry price, stop-loss price, take-profit price, position size percentage, and max loss amount
2. **Given** a recommendation is generated, **When** the user clicks "View Detailed Explanation", **Then** they see the triggering strategy, market signals (price breakout, volume change, indicators), and historical similar cases with success rates
3. **Given** the strategy attempts to generate a recommendation without stop-loss, **When** the system validates it, **Then** it rejects the recommendation and logs an error "Stop-loss missing"
4. **Given** recommendations are displayed, **When** the user views them, **Then** each recommendation shows data freshness indicator (real-time/delayed 15min/historical) and data timestamp

---

### User Story 3 - Execute Simulated Trades with Approval Workflow (Priority: P3)

As an individual investor, I want to execute simulated trades with explicit approval workflow and operation logging, so I can practice investment strategies safely before risking real capital.

**Why this priority**: This completes the feedback loop by allowing users to act on recommendations and see results. The simulation mode provides a safe environment for testing strategies and building confidence.

**Independent Test**: Can be tested by generating a recommendation, clicking "Confirm Execution", verifying the second confirmation dialog appears with all details, confirming the operation, and checking that the operation log records the complete transaction with timestamp and user ID.

**Acceptance Scenarios**:

1. **Given** the user views a recommendation card, **When** they click "Confirm Execution", **Then** a second confirmation dialog appears showing all details (symbol, entry price, stop-loss, position size, max possible loss) with "Cancel" and "Confirm Execution" buttons
2. **Given** the user confirms execution in the dialog, **When** the system processes it, **Then** it records the operation to the operation_log table with timestamp, user ID, operation type, original recommendation, and execution status
3. **Given** the user attempts to execute a position that would exceed 100% total allocation, **When** the system validates it, **Then** it rejects the operation and displays "Position limit exceeded, insufficient available capital"
4. **Given** the user has executed a simulated trade, **When** they view the holdings list, **Then** the new position appears with purchase price, current price, quantity, and profit/loss
5. **Given** the system is in simulation mode, **When** the user views any page, **Then** a prominent label "Current Mode: Simulated Trading" appears at the top of the interface with green background

---

### User Story 4 - Access Market Data with Quality Indicators (Priority: P4)

As an individual investor, I want to access market data (K-line charts, historical prices) for stocks with clear data quality indicators, so I can analyze market trends and verify the data freshness supporting my investment decisions.

**Why this priority**: This provides the data foundation for manual analysis and builds trust through transparency about data sources and freshness. It's lower priority because the core recommendation flow (Stories 1-3) can work with backend data without UI charts.

**Independent Test**: Can be tested by searching for a stock symbol, verifying the system displays a K-line chart with daily data, and confirming that the data freshness indicator shows the correct status (real-time/delayed/historical) based on the data age.

**Acceptance Scenarios**:

1. **Given** the user enters a stock symbol in the search box, **When** they search, **Then** the system displays a K-line chart with daily candlesticks for the most recent year
2. **Given** the market data is displayed, **When** the user views it, **Then** they see a data freshness indicator showing "Real-time" (green, <5s delay), "Delayed 15min" (yellow, 5s-15min delay), or "Historical" (gray, >15min delay)
3. **Given** the primary market data API fails, **When** the system attempts to fetch data, **Then** it automatically retries up to 3 times, then falls back to cached historical data and displays a prominent warning "Currently using historical data, updated at [timestamp]"
4. **Given** market data is displayed, **When** the user checks the data metadata, **Then** they see the API source (e.g., "Tushare v1.2.85"), retrieval timestamp, and price adjustment method (forward/backward/unadjusted)

---

### Edge Cases

- **What happens when the user imports a CSV file with mixed valid and invalid records?**
  System imports valid records, displays them in the table, and shows specific warning messages for each invalid record (e.g., "Row 5: Price must be positive"). Invalid records are not imported.

- **What happens when the user tries to execute a trade that would result in negative available capital?**
  System rejects the operation before execution and displays error message: "Position limit exceeded, current available capital: [amount], required: [amount]".

- **What happens when all market data APIs are unavailable and no cached data exists?**
  System displays a prominent error message: "Market data unavailable, cannot generate recommendations. Please try again later." Core functionality (viewing historical records) remains available.

- **What happens when a recommendation's stop-loss price is higher than entry price for a BUY order?**
  System validates logic constraints and rejects the recommendation with error: "Invalid stop-loss: must be below entry price for BUY orders".

- **What happens when the user manually enters investment records with duplicate entries (same symbol, same date)?**
  System detects potential duplicates and displays warning: "Possible duplicate: [symbol] on [date] already exists. Proceed anyway?" with Yes/No options.

- **What happens when the user switches to a different page while the system is loading market data?**
  The loading operation continues in the background. When the user returns to the page, they see the loaded data or an error message if the operation failed.

## Requirements *(mandatory)*

### Functional Requirements

**Data Management**:

- **FR-001**: System MUST allow users to import investment records via CSV file upload or manual form entry
- **FR-002**: System MUST validate each investment record for data integrity (price > 0, quantity > 0, date <= today, valid symbol format)
- **FR-003**: System MUST record data source for each investment record (manual_entry, broker_statement, api_import)
- **FR-004**: System MUST record ingestion timestamp for all imported data using ISO 8601 format
- **FR-005**: System MUST display validation errors to the user without auto-correcting invalid data
- **FR-006**: System MUST support viewing investment overview including total assets, cumulative profit/loss curve, asset distribution chart, and current holdings list

**Market Data Integration**:

- **FR-007**: System MUST integrate with at least one market data API for stock and futures historical and real-time data
- **FR-008**: System MUST record API source name and version for all market data (e.g., "Tushare v1.2.85")
- **FR-009**: System MUST record data retrieval timestamp for all market data
- **FR-010**: System MUST display data freshness indicator (Real-time <5s, Delayed 15min 5s-15min, Historical >15min)
- **FR-011**: System MUST retry failed API calls up to 3 times before falling back to cached historical data
- **FR-011a**: System MUST retain cached market data for 7 days to support weekly analysis during API outages
- **FR-012**: System MUST display prominent warning when using cached historical data instead of real-time data
- **FR-013**: System MUST display K-line charts for selected stocks with daily candlesticks for most recent year
- **FR-014**: System MUST allow users to switch K-line chart timeframes (daily/weekly/monthly)

**Investment Recommendations**:

- **FR-015**: System MUST generate investment recommendations on-demand when user explicitly requests them via "Generate Recommendations" button
- **FR-015a**: System MUST use the Livermore trend-following strategy for generating recommendations
- **FR-016**: System MUST include mandatory fields in all recommendations: symbol, action (BUY/SELL/HOLD), entry price, stop-loss price, take-profit price, position size percentage, max loss amount
- **FR-017**: System MUST reject any recommendation that lacks a stop-loss price (backend validation)
- **FR-018**: System MUST calculate max loss amount as: position_size * abs(entry_price - stop_loss)
- **FR-019**: System MUST validate stop-loss logic (for BUY: stop_loss < entry_price, for SELL: stop_loss > entry_price)
- **FR-020**: System MUST display up to 3 recommendation cards on the "Today's Recommendations" panel
- **FR-021**: System MUST provide detailed explanation for each recommendation including triggering strategy, market signals, and historical similar cases

**Investment Safety**:

- **FR-022**: System MUST display max loss amount prominently in large red text on recommendation cards
- **FR-023**: System MUST validate that single position size does not exceed 20% of total capital (configurable)
- **FR-024**: System MUST validate that total allocated capital (current holdings + new position) does not exceed 100%
- **FR-025**: System MUST reject operations that violate position limits with clear error messages
- **FR-026**: System MUST require explicit user confirmation before executing any trade operation
- **FR-027**: System MUST display second confirmation dialog showing all operation details before execution
- **FR-028**: System MUST support "modify before execution" allowing users to adjust stop-loss and position size
- **FR-029**: System MUST display prominent "Current Mode: Simulated Trading" label at top of all pages

**Operation Logging**:

- **FR-030**: System MUST record all investment operations to operation_log table with fields: operation_id (UUID), timestamp (ISO 8601), user_id, operation_type, symbol, original_recommendation (JSON), user_modification (JSON), execution_status, notes
- **FR-031**: System MUST make operation log append-only (no modifications or deletions allowed)
- **FR-032**: System MUST provide operation log viewing page with filters by date and symbol
- **FR-033**: System MUST update holdings list immediately after successful operation execution

**User Interface**:

- **FR-034**: System MUST provide web-based user interface accessible via web browser with core operations requiring no more than 3 clicks (see FR-035 for click count requirement)
- **FR-034a**: System MUST provide a "Generate Recommendations" button on the main dashboard to trigger on-demand recommendation generation
- **FR-035**: System MUST ensure core operations (view recommendation → confirm execution) require no more than 3 clicks
- **FR-036**: System MUST display loading indicators during data fetching operations
- **FR-037**: System MUST display error messages in clear Chinese with suggested solutions
- **FR-038**: System MUST load the homepage (investment overview + recommendations) in under 3 seconds

### Key Entities

- **Investment Record**: Represents a historical investment transaction. Key attributes: symbol (stock/futures code), purchase_amount (capital invested), purchase_price, purchase_date, quantity, sale_date (if sold), sale_price (if sold), profit_loss, data_source (manual/broker/api), ingestion_timestamp, checksum (data validation hash)

- **Market Data Point**: Represents market data for a specific symbol at a specific time. Key attributes: symbol, timestamp, open_price, high_price, low_price, close_price, volume, api_source, api_version, retrieval_timestamp, data_freshness (realtime/delayed/historical), adjustment_method (forward/backward/unadjusted), cache_expiry_date (timestamp + 7 days for fallback retention)

- **Investment Recommendation**: Represents an investment suggestion generated by the system. Key attributes: recommendation_id, symbol, action (BUY/SELL/HOLD), entry_price, stop_loss, take_profit, position_size_pct, max_loss_amount, expected_return_pct, advisor_name (Livermore), advisor_version, strategy_name, reasoning (why), confidence (HIGH/MEDIUM/LOW), key_factors, historical_precedents, market_data_timestamp, data_source, created_timestamp

- **Operation Log**: Represents a user investment operation (simulated or real). Key attributes: operation_id (UUID), timestamp, user_id, operation_type (BUY/SELL/MODIFY/CANCEL), symbol, original_recommendation (JSON), user_modification (JSON), execution_status (PENDING/EXECUTED/CANCELLED), execution_mode (SIMULATED/LIVE), notes. Relationships: references Investment Recommendation (many-to-one)

- **Current Holdings**: Represents a user's current investment position. Key attributes: symbol, quantity, purchase_price (average cost), current_price (latest market price), profit_loss_amount, profit_loss_pct, purchase_date (initial), last_update_timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully import at least 10 historical investment records and view them in the investment records table within 30 seconds
- **SC-002**: System generates at least 1 investment recommendation for a trending stock with all mandatory fields (entry, stop-loss, take-profit, position size, max loss) present
- **SC-003**: Users can complete the full workflow (view recommendation → confirm execution → view operation log) in under 3 clicks and 2 minutes
- **SC-004**: Homepage loads in under 3 seconds showing investment overview and recommendations (or appropriate error message if no data available)
- **SC-005**: System displays data freshness indicator correctly (green for real-time <5s, yellow for delayed 5s-15min, gray for historical >15min) on all market data displays
- **SC-006**: System successfully rejects 100% of recommendations that lack stop-loss price (validated through test cases)
- **SC-007**: System successfully rejects 100% of operations that would exceed 100% capital allocation with clear error messages
- **SC-008**: System displays cumulative profit/loss curve chart correctly for imported historical records spanning at least 3 months
- **SC-009**: All executed operations appear in operation log with complete details (timestamp, symbol, price, status) within 1 second of execution
- **SC-010**: System degrades gracefully when market data API fails, falling back to cached data and displaying prominent warning within 5 seconds
- **SC-011**: K-line charts render correctly for searched stocks showing daily candlesticks for the most recent year

### Quality Gates for v0.1

- **QG-001**: All recommendation cards must pass manual verification that max loss amount is prominently displayed in red
- **QG-002**: Second confirmation dialog must be tested for all operation types and verified to show complete details
- **QG-003**: Data validation logic must be tested with at least 20 invalid input cases (negative prices, future dates, malformed symbols, missing required fields)
- **QG-004**: API failure scenarios must be tested to verify graceful degradation and appropriate error messages
- **QG-005**: Operation log must be verified as append-only by attempting modifications and deletions (all should fail)

## Assumptions

- Users have basic understanding of investment concepts (stocks, futures, stop-loss, position sizing)
- Users will primarily use desktop or tablet web browsers (responsive mobile design is out of scope for v0.1)
- Market data API (Tushare or equivalent) is accessible and provides at least 1 year of historical daily data
- Single user mode is sufficient for v0.1 (user_id can be hardcoded as "default_user")
- Simulated trading mode does not need to account for realistic order execution (market impact, slippage, partial fills)
- Users will manually execute real trades through their brokerage account (v0.1 does not integrate with brokerage APIs)
- Data retention is permanent for v0.1 (no automatic deletion or archiving)
- Users understand that "Livermore strategy" refers to trend-following principles and not direct trading advice from Jesse Livermore
- CSV import format follows standard structure: symbol, purchase_date, purchase_price, quantity, sale_date (optional), sale_price (optional)
- System operates in single timezone (user's local timezone) for v0.1

## Scope Boundaries

### In Scope for v0.1

- Import historical investment records (CSV or manual entry)
- Display investment overview (total assets, profit/loss curve, holdings list)
- Integrate with one market data API (Tushare or AKShare)
- Display K-line charts with daily data for searched stocks
- Implement Livermore trend-following strategy (single strategy only)
- Generate investment recommendations with mandatory safety fields
- Display recommendation explanations (strategy, signals, historical cases)
- Execute simulated trades with approval workflow
- Record all operations to audit log
- Display data freshness indicators and handle API failures gracefully
- Web-based user interface using framework compatible with Google ADK

### Out of Scope for v0.1

- Multiple strategy support (Kroll strategy deferred to v0.2)
- Strategy weighting and fusion logic (deferred to v0.2)
- Historical backtesting engine and performance metrics (Sharpe ratio, max drawdown - deferred to v0.2)
- Real brokerage API integration and live trading mode (deferred to future versions)
- Multi-user support, user authentication, and permissions (single user sufficient for v0.1)
- Real-time minute-level market data (daily data sufficient for v0.1)
- Mobile-specific UI optimizations (responsive web UI acceptable)
- Automated scheduled recommendation generation (on-demand only for v0.1, scheduled tasks deferred to v0.2)
- Push notifications for trade alerts
- A/B testing of different advisor prompt versions
- Data anomaly auto-correction (warnings only, no auto-fix)
- Strategy approval workflow for backtesting (no backtest in v0.1)

## Dependencies

- Market data API availability (Tushare, AKShare, or equivalent) with at least 1 year historical daily data
- Python 3.10+ runtime environment
- Google ADK framework for agent coordination (or compatible alternative like Streamlit for v0.1 prototyping)
- Database system (SQLite for v0.1, PostgreSQL for future production)
- Visualization library for charts (Plotly, ECharts, or equivalent)
- User has investment records available for import (CSV format or manual entry data)

## Constraints

- v0.1 is a prototype/MVP focused on core functionality validation
- Single user mode only (no concurrent users)
- Simulated trading only (no real brokerage integration)
- Single strategy implementation (Livermore only)
- Historical daily data only (no real-time tick data)
- Chinese language UI (internationalization out of scope)
- Desktop/tablet web browsers only (mobile optimization out of scope)
- Development timeline target: suitable for rapid prototyping and validation
