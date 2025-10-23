# Feature Specification: MyInvest V0.3 - Production-Ready Enhancement

**Feature Branch**: `003-v0-3-proposal`
**Created**: 2025-10-22
**Status**: Draft
**Input**: User description: "@V0.3_PROPOSAL.md"

## Clarifications

### Session 2025-10-22

- Q: Which existing V0.1/V0.2 components should be upgraded versus which new components are needed for V0.3's multi-asset support? → A: Upgrade existing components (data fetcher, strategy base, backtest engine) and add new modules only for derivatives-specific features (margin calculation, Greeks, forced liquidation)
- Q: How should V0.3 handle database schema changes given existing V0.1/V0.2 data? → A: Use migration scripts (e.g., Alembic) to evolve existing schema by adding new tables/columns while preserving V0.1/V0.2 data
- Q: Should existing Livermore/Kroll strategies be adapted for futures/options, or create new derivative-specific strategies? → A: Keep Livermore/Kroll stock-only, create entirely new strategies for futures/options from scratch
- Q: Should V0.3 upgrade V0.2's existing scheduler or create separate schedulers for different asset types? → A: Upgrade V0.2's existing scheduler to handle all asset types by reading from unified watchlist database and applying asset-specific timing rules
- Q: Should V0.3 continue using the same UI framework from V0.1/V0.2 or migrate to a different framework? → A: Migrate to a different UI framework to better support V0.3's complex interactive features

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watchlist Management (Priority: P0)

As an investor, I want to manage my stock watchlist through the UI interface so that I can flexibly adjust the stocks I'm tracking without modifying code.

**Why this priority**: Currently, watchlists are hardcoded, severely limiting usability. This is a blocking issue that affects all other features.

**Independent Test**: Can be fully tested by adding/removing stocks via UI, creating groups, and verifying the scheduler automatically picks up changes without restart. Delivers immediate value by eliminating manual code editing.

**Acceptance Scenarios**:

1. **Given** I am on the watchlist page, **When** I add stock "600519.SH" to my watchlist, **Then** the stock appears in my watchlist and the scheduler begins tracking it
2. **Given** I have stocks in my watchlist, **When** I create a group called "Core Holdings" and assign 3 stocks to it, **Then** those stocks are grouped together and can be managed as a unit
3. **Given** I have a CSV file with 10 stock symbols, **When** I upload the file to batch import, **Then** all 10 stocks are added to my watchlist successfully
4. **Given** I have a stock in my watchlist, **When** I pause that stock, **Then** the scheduler skips that stock in its next run
5. **Given** I modify my watchlist, **When** the scheduler runs, **Then** it automatically uses the latest watchlist without requiring a restart

---

### User Story 2 - Parallel Backtesting (Priority: P0)

As an investor, I want to backtest multiple stocks simultaneously so that I can quickly evaluate my entire portfolio's strategy performance instead of waiting for sequential execution.

**Why this priority**: Current backtest times (10+ minutes for 10 stocks) are unacceptable for production use. This is critical for user experience and system performance.

**Independent Test**: Can be fully tested by running a backtest on 10 stocks and measuring execution time (target: <3 minutes vs current 10+ minutes). Delivers immediate value through dramatic performance improvement.

**Acceptance Scenarios**:

1. **Given** I have 10 stocks in my watchlist, **When** I start a backtest, **Then** the system runs all backtests in parallel and completes in under 3 minutes
2. **Given** backtesting is in progress, **When** I view the status, **Then** I see a real-time progress indicator showing "3/10 stocks completed"
3. **Given** one stock fails during backtesting, **When** the backtest completes, **Then** the other 9 stocks complete successfully and I see an error report for the failed stock
4. **Given** backtesting completes, **When** I view the results, **Then** I see a consolidated report comparing all stocks' Sharpe ratios and drawdowns
5. **Given** my machine has 8 CPU cores, **When** the backtest runs, **Then** the system automatically uses up to 8 parallel workers

---

### User Story 3 - Strategy Parameter Optimization (Priority: P1)

As a strategy developer, I want to automatically search for optimal parameter combinations so that I can find the best stop-loss/take-profit/position configurations instead of relying on guesswork.

**Why this priority**: Manual parameter tuning is time-consuming and suboptimal. Automated optimization significantly improves strategy performance and development efficiency.

**Independent Test**: Can be fully tested by running parameter optimization on a single strategy, viewing the heatmap visualization, and applying the recommended parameters. Delivers value by improving strategy returns.

**Acceptance Scenarios**:

1. **Given** I select a strategy to optimize, **When** I run grid search with stop-loss range 2%-5% (0.5% step), take-profit range 3%-10% (1% step), and position range 8%-20% (2% step), **Then** the system tests all 392 parameter combinations
2. **Given** optimization completes, **When** I view the results, **Then** I see a heatmap showing Sharpe ratio across different stop-loss and take-profit combinations with the optimal point highlighted
3. **Given** I run walk-forward validation with 2-year training and 1-year testing periods, **When** validation completes, **Then** I see training Sharpe of 1.8 and testing Sharpe of 1.5 indicating healthy performance
4. **Given** optimization results show training Sharpe of 2.5 and testing Sharpe of 0.8, **When** I view the report, **Then** the system warns me about potential overfitting
5. **Given** I find optimal parameters, **When** I click "Apply to Strategy", **Then** the parameters are saved to the strategy configuration

---

### User Story 4 - Report Export System (Priority: P1)

As an investor, I want to export backtest reports as PDF and trading records as Excel so that I can review offline, print, or share with my investment advisor.

**Why this priority**: Professional reporting capabilities are essential for serious investors. This enhances credibility and facilitates offline analysis and sharing.

**Independent Test**: Can be fully tested by running a backtest and exporting reports in all three formats (PDF/Excel/Word), then verifying content completeness. Delivers value through professional documentation.

**Acceptance Scenarios**:

1. **Given** I have completed a backtest, **When** I click "Export PDF", **Then** a file named "backtest_report_600519_20251022.pdf" is generated containing cover page, performance metrics, equity curve, drawdown chart, and trade history
2. **Given** I export a PDF report, **When** I open the file, **Then** all charts (equity curve, drawdown) and tables are properly formatted with page numbers and footer disclaimer
3. **Given** I have trading records, **When** I export to Excel, **Then** the file contains 3 sheets: Trade Details, Monthly Summary, and Position Analysis with profit rows in green and loss rows in red
4. **Given** I have current positions, **When** I export a Word report, **Then** the document includes current holdings table, risk metrics (VaR, concentration), and recommended actions
5. **Given** any exported report, **When** I review the footer, **Then** it contains the disclaimer "This report is for reference only and does not constitute investment advice"

---

### User Story 5 - Futures and Options Support (Priority: P1)

As an investor, I want to trade futures (commodity/stock index) and options (stock/ETF options) in the system so that I can implement multi-asset allocation and hedging strategies beyond just stocks.

**Why this priority**: Expanding to derivatives significantly enhances the system's value proposition and enables sophisticated trading strategies like hedging and arbitrage.

**Independent Test**: Can be fully tested by adding a futures contract (IF2506.CFFEX) to watchlist, running a backtest with margin calculations and forced liquidation logic, and verifying results. Delivers value through multi-asset support.

**Acceptance Scenarios**:

1. **Given** I am on the watchlist page, **When** I add futures contract "IF2506.CFFEX" and label it as "Futures", **Then** the contract appears with a "Futures" badge
2. **Given** I backtest a futures strategy, **When** the backtest completes, **Then** the results show correct margin usage calculation and any forced liquidation events
3. **Given** I want to go short, **When** I configure a short position in the strategy, **Then** the backtest correctly calculates profit/loss for the short position
4. **Given** I add an option contract, **When** I view the backtest results, **Then** the report includes Greeks calculations (Delta, Gamma, Vega, Theta) and option expiry handling
5. **Given** I have stocks, futures, and options in my watchlist, **When** I view the watchlist, **Then** each asset type is clearly labeled with appropriate badges
6. **Given** I use efinance as primary data source and it fails, **When** the system retries, **Then** it automatically falls back to AkShare without user intervention
7. **Given** a futures contract approaches expiry, **When** the main contract switches, **Then** the historical data remains continuous without gaps
8. **Given** an option with missing data, **When** the system detects incomplete data, **Then** it displays a warning message and skips that option

---

### User Story 6 - Risk Monitoring Dashboard (Priority: P1)

As an investor, I want to view real-time risk metrics for all my positions (stocks, futures, options) so that I can proactively manage concentration risk, margin risk, and market risk to avoid black swan events and forced liquidations.

**Why this priority**: Risk management is critical for portfolio protection. Real-time monitoring with margin and liquidation alerts prevents catastrophic losses.

**Independent Test**: Can be fully tested by creating a mixed portfolio with stocks, futures, and options, then verifying the dashboard displays all risk metrics correctly and updates in real-time. Delivers value through risk awareness.

**Acceptance Scenarios**:

1. **Given** I have positions across stocks, futures, and options, **When** I open the risk dashboard, **Then** I see a heatmap with bubble sizes representing position weight or margin usage, colored by profit/loss (green for profit, red for loss)
2. **Given** my portfolio has risk exposure, **When** the dashboard calculates VaR, **Then** it displays "95% VaR (1 day) = ¥3,200, representing 3.2% of total assets"
3. **Given** I have futures positions, **When** I view margin metrics, **Then** the dashboard shows "Margin usage: 65%, Safety buffer: 35%"
4. **Given** a futures position is close to forced liquidation, **When** the price moves within 3% of liquidation price, **Then** the position shows a yellow warning indicator
5. **Given** a stock position is close to stop-loss, **When** the price is within 1.5% of stop-loss, **Then** the position shows a red warning indicator
6. **Given** I have option positions, **When** I view the Greeks summary, **Then** the dashboard displays "Total Delta: +125, Total Theta: -50/day"
7. **Given** positions have correlation, **When** I view the correlation matrix, **Then** it shows "600519 vs IF2506 correlation: -0.45, effective hedge"
8. **Given** the dashboard is open, **When** 5 seconds elapse, **Then** the prices and risk metrics automatically refresh

---

### User Story 7 - Combination Strategy Interface (Priority: P1)

As a futures/options trader, I want to build combination strategies through a UI (such as calendar spreads, butterfly spreads) so that I can fully leverage the combination features of derivatives without manually configuring complex JSON files.

**Why this priority**: Combination strategies are the core value of derivatives trading. Without UI support, users must hand-write JSON configurations, creating a barrier to entry that limits the system's utility.

**Independent Test**: Can be fully tested by selecting a "Butterfly Spread" template, constructing a 3-leg option combination via drag-and-drop, viewing the real-time P&L chart, and running a backtest. Delivers value through accessible advanced trading.

**Acceptance Scenarios**:

1. **Given** I want to create a calendar spread, **When** I select the "Calendar Spread" template, **Then** the system automatically populates buy near-month and sell far-month legs
2. **Given** I want to create a custom option combination, **When** I drag option contracts to the builder, specify buy/sell direction, and set quantities, **Then** the system displays a real-time P&L curve showing profit/loss at different underlying prices
3. **Given** I have built a butterfly spread combination, **When** I view the P&L chart, **Then** the X-axis shows underlying price and Y-axis shows combination profit/loss
4. **Given** I have configured a combination strategy, **When** I run a backtest, **Then** the results show overall Sharpe ratio and total margin usage for the entire combination
5. **Given** I have active combination positions, **When** I view the positions page in "Combination View", **Then** I can expand each combination to see individual legs and close the entire combination with one click

---

### User Story 8 - Multi-Timeframe Strategy (Priority: P2)

As a strategy developer, I want to combine weekly trends with daily timing signals so that I can improve entry precision and filter out false breakout signals.

**Why this priority**: Multi-timeframe analysis enhances strategy sophistication and can improve returns, but it's not essential for core functionality.

**Independent Test**: Can be fully tested by configuring a strategy that uses weekly MA direction combined with daily breakout signals, running a backtest, and comparing results against daily-only strategy. Delivers value through refined signal quality.

**Acceptance Scenarios**:

1. **Given** I configure a multi-timeframe strategy, **When** the weekly trend is upward and a daily breakout occurs, **Then** the system generates a BUY signal
2. **Given** I run a comparative backtest, **When** results are displayed, **Then** I see "Daily-only Sharpe: 1.5, Weekly+Daily Sharpe: 1.8"
3. **Given** I am on the strategy configuration page, **When** I select timeframes, **Then** I can choose "Daily", "Weekly", or "Daily+Weekly Combination"
4. **Given** a stock meets entry criteria, **When** I view the recommendation card, **Then** it displays "Weekly trend: ↑ Upward"

---

### User Story 9 - Technical Indicators Expansion (Priority: P2)

As a strategy developer, I want to use additional technical indicators (MACD, KDJ, Bollinger Bands, volume patterns) so that I can create more sophisticated combination strategies.

**Why this priority**: More indicators enable richer strategies, but the existing indicators are sufficient for core functionality.

**Independent Test**: Can be fully tested by creating a strategy using MACD crossover combined with Bollinger Band position, running a backtest, and validating signal generation. Delivers value through strategy diversity.

**Acceptance Scenarios**:

1. **Given** I configure a strategy with MACD, **When** MACD line crosses above signal line, **Then** the system generates a bullish signal
2. **Given** I configure a strategy with Bollinger Bands, **When** price touches the lower band, **Then** the system identifies a potential oversold condition
3. **Given** I configure a strategy with KDJ, **When** K line crosses above D line in oversold zone, **Then** the system generates a buy signal
4. **Given** I want to select indicators, **When** I open the indicator selector, **Then** I can choose from MACD, KDJ, Bollinger Bands, and volume pattern analysis
5. **Given** I create a combination strategy, **When** I backtest it, **Then** the results show performance metrics for the multi-indicator approach

---

### Edge Cases

- What happens when efinance data source fails and AkShare also fails for a specific symbol? System should log the error, skip that symbol, and notify the user of the data failure.
- How does the system handle futures contract rollovers when there are open positions? System should use continuous contract data for backtesting and alert users about rollover dates.
- What happens when an option expires worthless while the user has an open position? System should automatically mark the option as expired, close the position at zero value, and record the loss.
- How does the system handle parallel backtesting when available memory is low? System should detect memory constraints and automatically reduce the number of parallel workers to prevent crashes.
- What happens when a user tries to export a report but no backtest has been run? System should display a message: "No backtest results available. Please run a backtest first."
- How does the system handle parameter optimization when the parameter space is too large (10,000+ combinations)? System should warn the user about long execution time and suggest narrowing the parameter ranges.
- What happens when margin usage exceeds 100% during a futures backtest? System should trigger a forced liquidation event, close the position at the current price, and record the liquidation in the backtest results.
- How does the system calculate Greeks for options when volatility data is missing? System should use a default implied volatility (e.g., 30-day historical volatility) and flag the calculation as estimated.
- What happens when a user creates a watchlist group with duplicate stock symbols? System should detect duplicates and either reject the addition with an error message or automatically deduplicate.
- How does the system handle American option early exercise during backtesting (V0.3 simplified approach)? System should only process exercise at expiry date and document this limitation in reports.

## Requirements *(mandatory)*

### Functional Requirements

**Watchlist Management (US1)**:

- **FR-001**: System MUST allow users to add and remove stocks from their watchlist via UI without code modification
- **FR-002**: System MUST support organizing stocks into groups (Core Holdings, Watchlist, Sector Groups)
- **FR-003**: System MUST allow batch import of stocks via CSV file upload
- **FR-004**: System MUST support pausing individual stocks so the scheduler skips them
- **FR-005**: System MUST automatically sync watchlist changes to V0.2's existing scheduler (upgraded to support multi-asset) without requiring restart, with the scheduler reading from the unified watchlist database
- **FR-006**: System MUST display the status (active/paused) for each stock in the watchlist
- **FR-007**: System MUST persist watchlist data in a new database table with CRUD operations, added via schema migration to preserve existing V0.1/V0.2 data

**Parallel Backtesting (US2)**:

- **FR-008**: System MUST execute backtests in parallel using multiple CPU cores
- **FR-009**: System MUST display real-time progress indicators during parallel backtesting (e.g., "3/10 stocks completed")
- **FR-010**: System MUST isolate errors so that failure of one stock backtest does not prevent others from completing
- **FR-011**: System MUST generate consolidated reports comparing performance metrics across all backtested stocks
- **FR-012**: System MUST automatically detect available CPU cores and configure parallel workers accordingly
- **FR-013**: System MUST complete backtesting of 10 stocks in under 3 minutes on standard hardware (8-core CPU)

**Parameter Optimization (US3)**:

- **FR-014**: System MUST perform grid search across user-defined parameter ranges (stop-loss, take-profit, position size)
- **FR-015**: System MUST support walk-forward validation with configurable training and testing periods
- **FR-016**: System MUST generate heatmap visualizations showing performance metrics across parameter combinations
- **FR-017**: System MUST detect and warn users about potential overfitting when training/testing performance diverges significantly (threshold: training_sharpe - testing_sharpe > 0.5)
- **FR-018**: System MUST allow users to save optimal parameters directly to strategy configurations
- **FR-019**: System MUST support parallel optimization by leveraging the parallel backtesting engine

**Report Export (US4)**:

- **FR-020**: System MUST export backtest reports as PDF files containing cover page, metrics, charts, and trade history
- **FR-021**: System MUST export trading records as Excel files with multiple sheets (Trade Details, Monthly Summary, Position Analysis)
- **FR-022**: System MUST export position reports as Word documents including holdings, risk metrics, and recommendations
- **FR-023**: System MUST apply formatting to exports (colored profit/loss cells, page numbers, footers)
- **FR-024**: System MUST include disclaimer text in all exported reports: "This report is for reference only and does not constitute investment advice"
- **FR-025**: System MUST generate unique filenames for exports including asset symbol and date (e.g., "backtest_report_600519_20251022.pdf")

**Futures and Options Support (US5)**:

- **FR-026**: System MUST support adding futures contracts (commodity and stock index) and options (stock and ETF options) to the watchlist
- **FR-027**: System MUST calculate margin requirements for futures positions based on configurable margin rates
- **FR-028**: System MUST support bidirectional trading (long and short positions) for futures and options
- **FR-029**: System MUST detect and execute forced liquidation when margin usage exceeds threshold during futures backtesting
- **FR-030**: System MUST calculate option Greeks (Delta, Gamma, Vega, Theta) using Black-Scholes model
- **FR-031**: System MUST handle option expiry automatically (exercise in-the-money options, expire worthless out-of-money options)
- **FR-032**: System MUST extend V0.2's MarketDataFetcher to support efinance as primary data source for all asset types (stocks, futures, options) with automatic fallback to AkShare when efinance fails (upgrading V0.2's Tushare→AkShare mechanism to efinance→AkShare)
- **FR-034**: System MUST maintain continuous historical data during futures contract rollovers
- **FR-035**: System MUST validate data completeness for options and warn users when data is missing
- **FR-036**: System MUST extend existing BaseStrategy class (from V0.2) to create specialized subclasses for stocks, futures, and options (StockStrategy, FuturesStrategy, OptionsStrategy) that inherit common logic while adding asset-specific behavior
- **FR-037**: System MUST upgrade existing BacktestEngine (from V0.2) to support multiple asset types through polymorphic strategy handling, with asset-specific trading rules encapsulated in strategy subclasses
- **FR-076**: System MUST keep existing Livermore and Kroll strategies (from V0.1/V0.2) restricted to stock trading only, without modification
- **FR-077**: System MUST create new derivative-specific strategies for futures (e.g., FuturesTrendFollowing, FuturesArbitrage) and options (e.g., CoveredCall, ProtectivePut) that account for margin requirements, leverage, bidirectional trading, and expiry handling
- **FR-038**: System MUST use centralized configuration management (Pydantic BaseSettings) for data sources, margin rates, risk parameters
- **FR-039**: System MUST validate configuration values (e.g., forced liquidation margin rate must be less than default margin rate)
- **FR-040**: System MUST support American options with simplified expiry-only exercise logic (V0.3 limitation)

**Risk Monitoring (US6)**:

- **FR-041**: System MUST display position heatmap with bubble sizes representing weight/margin usage and colors representing profit/loss
- **FR-042**: System MUST calculate Value at Risk (VaR) at 95% confidence level for 1-day horizon
- **FR-043**: System MUST calculate Conditional Value at Risk (CVaR)
- **FR-044**: System MUST calculate and display maximum single position concentration
- **FR-045**: System MUST calculate and display margin usage rate for futures/options positions
- **FR-046**: System MUST assess forced liquidation risk by calculating distance to liquidation price
- **FR-047**: System MUST display stop-loss distance warnings (red if <2%, yellow if 2-5%)
- **FR-048**: System MUST display forced liquidation distance warnings for futures positions
- **FR-049**: System MUST calculate and display aggregated option Greeks for all option positions
- **FR-050**: System MUST calculate and display correlation matrix for all positions
- **FR-051**: System MUST highlight high correlation pairs (>0.7) and suggest diversification
- **FR-052**: System MUST auto-refresh risk metrics every 5 seconds with latest prices
- **FR-053**: System MUST display option expiry warnings for contracts expiring within 30 days

**Combination Strategy Interface (US7)**:

- **FR-054**: System MUST provide pre-configured templates for common futures combinations (calendar spread, inter-commodity spread)
- **FR-055**: System MUST provide pre-configured templates for common options combinations (covered call, protective put, straddle, butterfly spread)
- **FR-056**: System MUST support drag-and-drop UI for building custom multi-leg strategies
- **FR-057**: System MUST display real-time profit/loss curves for combination strategies across different underlying prices
- **FR-058**: System MUST calculate aggregate margin requirements for combination strategies considering hedge effects
- **FR-059**: System MUST calculate aggregate Greeks for option combinations
- **FR-060**: System MUST support backtesting entire combination strategies with all legs
- **FR-061**: System MUST display combination positions with expandable leg details
- **FR-062**: System MUST support one-click closing of entire combination positions

**Multi-Timeframe Strategy (US8)**:

- **FR-063**: System MUST support combining weekly trend analysis with daily timing signals
- **FR-064**: System MUST calculate weekly moving average direction and MACD trend
- **FR-065**: System MUST generate signals only when daily breakout aligns with weekly trend
- **FR-066**: System MUST support comparative backtesting of single-timeframe vs multi-timeframe strategies
- **FR-067**: System MUST display selected timeframe combinations in strategy configuration UI

**Technical Indicators (US9)**:

- **FR-068**: System MUST implement MACD (Moving Average Convergence Divergence) indicator
- **FR-069**: System MUST implement KDJ (Stochastic Oscillator) indicator
- **FR-070**: System MUST implement Bollinger Bands indicator
- **FR-071**: System MUST implement volume pattern analysis
- **FR-072**: System MUST allow users to select and combine multiple indicators in strategy configuration
- **FR-073**: System MUST support backtesting of multi-indicator combination strategies

**Database Schema Evolution (Cross-cutting)**:

- **FR-074**: System MUST use migration scripts (Alembic) to evolve database schema, adding new tables (watchlist, contract_info, combination_strategy) and extending existing tables (positions, trades) with new columns (asset_type, direction, margin_used)
- **FR-075**: System MUST preserve all existing V0.1/V0.2 data during schema migrations, with rollback capability if migration fails

**Scheduler Enhancement (Cross-cutting)**:

- **FR-078**: System MUST upgrade V0.2's existing recommendation scheduler to read from the watchlist database and support all asset types (stocks, futures, options)
- **FR-079**: System MUST apply asset-specific timing rules in the scheduler (e.g., stock market hours 9:30-15:00, futures extended hours, option expiry cycle awareness)

**UI Framework Migration (Cross-cutting)**:

- **FR-080**: System MUST migrate from V0.1/V0.2 UI framework to a new framework that better supports V0.3's interactive features (drag-and-drop strategy builder, real-time P&L curves, heatmaps, auto-refreshing dashboards)
- **FR-081**: System MUST maintain backward compatibility during migration by ensuring V0.1/V0.2 core workflows (import records, view dashboard, generate recommendations) remain functional
- **FR-082**: System MUST preserve existing UI data persistence mechanisms (user preferences, saved configurations) during framework migration

### Key Entities

- **Watchlist**: Represents a collection of financial instruments being monitored. Attributes: stock symbol, group assignment (Core Holdings, Watchlist, Sector Groups), status (active/paused), date added.

- **Stock/Contract**: Represents a tradable financial instrument. Attributes: symbol code, asset type (stock/futures/option), name, exchange, contract details (for derivatives: multiplier, expiry date, strike price for options).

- **Position**: Represents an open investment position. Attributes: symbol, asset type, direction (long/short), quantity, entry price, current price, profit/loss, margin used (for futures/options).

- **Trade**: Represents a completed trade transaction. Attributes: symbol, asset type, direction (buy/sell, open/close), quantity, execution price, timestamp, profit/loss, margin used.

- **Strategy**: Represents a trading strategy configuration. Attributes: strategy name, asset type applicability (stock/futures/options), parameters (stop-loss, take-profit, position size, technical indicators), enabled status. Note: Existing V0.2 strategies (Livermore, Kroll) remain stock-only; new derivative-specific strategies will be created for futures/options.

- **BacktestResult**: Represents the outcome of a strategy backtest. Attributes: strategy name, symbol, date range, performance metrics (Sharpe ratio, max drawdown, total return, win rate), equity curve data, list of trades executed.

- **ParameterOptimization**: Represents a parameter optimization session. Attributes: strategy name, parameter ranges tested, grid search results, heatmap data, optimal parameters identified, walk-forward validation results, overfitting indicators.

- **Report**: Represents an exported report. Attributes: report type (PDF/Excel/Word), generation date, associated backtest or position data, file path.

- **RiskMetric**: Represents calculated risk indicators. Attributes: calculation timestamp, VaR value, CVaR value, maximum position concentration, margin usage rate, correlation matrix, individual position risks (stop-loss distance, liquidation distance).

- **CombinationStrategy**: Represents a multi-leg strategy. Attributes: combination name, strategy type (calendar spread, butterfly, etc.), list of legs (each with symbol, direction, quantity), aggregate margin requirement, aggregate Greeks (for options).

- **ContractInfo**: Represents derivative contract specifications. Attributes: contract code, contract type (futures/option), underlying symbol, multiplier, margin rate, tick size, expiry date, delivery method, option type (call/put), strike price.

- **DataSourceConfig**: Represents data source configuration. Attributes: primary source (efinance), fallback source (AkShare), auto-fallback enabled, cache settings (enabled, directory, expiry days).

- **TradingRuleConfig**: Represents trading rules for different asset types. Attributes: asset type, settlement cycle (T+0/T+1), bidirectional trading allowed, margin-based funding, forced liquidation enabled, liquidation margin threshold.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Performance Metrics**:

- **SC-001**: Backtesting 10 stocks completes in under 3 minutes (compared to current 10+ minutes)
- **SC-002**: All UI operations (excluding data fetching, backtest execution, and report generation) respond within 1 second for user interactions (button clicks, form submissions, page navigation)
- **SC-003**: Scheduler execution for 20 stocks completes in under 5 minutes

**Functional Metrics**:

- **SC-004**: 100% of watchlist management operations are performed through UI with zero code modifications required
- **SC-005**: Parameter optimization identifies parameter combinations that improve Sharpe ratio by at least 10% compared to default parameters
- **SC-006**: Exported PDF and Excel reports meet professional formatting standards and include all required sections (cover, metrics, charts, trade history, disclaimer)
- **SC-007**: Futures backtesting calculates margin usage with 99%+ accuracy and correctly identifies forced liquidation scenarios
- **SC-008**: Options backtesting calculates Greeks with accuracy within 5% of theoretical values
- **SC-009**: Risk monitoring dashboard VaR calculations have error margin less than 5% when tested against historical scenarios

**User Experience Metrics**:

- **SC-010**: New users can complete their first backtest within 15 minutes of starting to use the system
- **SC-011**: All core operations require 3 or fewer clicks to complete (measured from feature entry point to result display; excludes intermediate navigation steps within complex workflows)
- **SC-012**: Error messages are clear and actionable, providing specific solutions for at least 90% of common errors
- **SC-013**: All UI pages are responsive and accessible on mobile devices
- **SC-023**: UI framework migration maintains 100% functionality of V0.1/V0.2 core workflows (import records, view dashboard, generate recommendations) with no regression in user experience

**Data Reliability Metrics**:

- **SC-014**: Data retrieval succeeds for 99%+ of requests through automatic fallback mechanism (efinance → AkShare)
- **SC-015**: Futures contract rollover maintains data continuity with zero gaps in historical price series
- **SC-016**: System successfully handles and reports missing option data without crashing

**Risk Management Metrics**:

- **SC-017**: Risk dashboard displays accurate real-time metrics with auto-refresh every 5 seconds
- **SC-018**: Stop-loss and forced liquidation warnings trigger correctly when positions are within specified thresholds (2% red, 2-5% yellow)
- **SC-019**: Combination strategy margin calculations accurately reflect hedge effects, reducing margin requirements by at least 20% compared to sum of individual legs

**Integration and Stability Metrics**:

- **SC-020**: Configuration validation catches 100% of invalid parameter combinations (e.g., forced liquidation margin rate >= default margin rate)
- **SC-021**: System handles single stock backtest failures gracefully, allowing other stocks to complete, with 95%+ success rate for batch operations
- **SC-022**: American options limitation is clearly documented, and users are informed that only expiry-date exercise is simulated in V0.3

## Dependencies & Assumptions *(mandatory)*

### External Dependencies

- **efinance library**: Primary data source for stocks, futures, and options historical and real-time data
- **AkShare library**: Backup data source for all asset types when efinance fails
- **reportlab or weasyprint**: PDF generation for backtest reports
- **openpyxl**: Excel file generation for trading records
- **python-docx**: Word document generation for position reports
- **scipy**: VaR/CVaR calculations and Black-Scholes option pricing
- **pydantic[dotenv]**: Centralized configuration management with type safety
- **alembic**: Database schema migration management to evolve V0.1/V0.2 schema
- **Python 3.10+**: Runtime environment

### Technical Assumptions

- System has access to at least 4 CPU cores (8 recommended) for parallel backtesting
- Users have stable internet connection for data retrieval from efinance/AkShare
- Historical data is available for the backtesting period requested (assumes 10+ years for stocks, varies for derivatives)
- Default margin rate for futures is 15%, forced liquidation threshold is 10% (configurable)
- Default risk-free rate for options pricing is 3% (configurable)
- VaR calculations use 95% confidence level with 1-day horizon (configurable)
- American options in V0.3 only exercise at expiry (early exercise not simulated)
- System assumes local time zone matches exchange time zone for all calculations
- **V0.3 builds on V0.1/V0.2 foundation**: Existing components (MarketDataFetcher from V0.2, BaseStrategy class, BacktestEngine, Scheduler) will be upgraded to support multi-asset trading, avoiding duplication by extending rather than replacing core infrastructure
- **UI framework migration in V0.3**: V0.3 will migrate to a new UI framework to support complex interactive features (drag-and-drop, real-time updates, advanced visualizations) while maintaining backward compatibility for V0.1/V0.2 core workflows

### Business Assumptions

- Users understand basic investment concepts (stocks, futures, options, margin, stop-loss, Greeks)
- Users are responsible for validating strategy parameters and backtest results
- Exported reports are for personal reference and not for regulatory compliance purposes
- Data sources (efinance, AkShare) provide reasonably accurate historical data (system does not independently verify data accuracy)
- Users manage their own data privacy and do not share sensitive portfolio information through reports
- System is for backtesting and analysis only; V0.3 does not support live trading (deferred to V0.4)

### Scope Boundaries

**In Scope for V0.3**:
- Watchlist UI management
- Parallel backtesting engine
- Parameter optimization with grid search and walk-forward validation
- Report export (PDF/Excel/Word)
- Futures and options support with margin/Greeks calculations
- Risk monitoring dashboard with real-time updates
- Combination strategy UI and backtesting
- Multi-timeframe strategies (P2 - optional)
- Extended technical indicators (P2 - optional)

**Out of Scope for V0.3** (deferred to future versions):
- Live broker API integration (V0.4)
- Real-time trading mode (V0.4)
- Push notification system (V0.4)
- Multi-user and permissions system (V0.5)
- Minute-level or tick-level data (V0.5)
- Advanced American option early exercise optimization (V0.4)
- AI-driven strategy generation (V0.6)
- News and sentiment analysis (V0.6)

## Open Questions

None - all requirements are specified with reasonable defaults where necessary. Configuration parameters (margin rates, risk thresholds, data sources) are documented in the Assumptions section and will be managed through centralized configuration (.env file with Pydantic validation).
