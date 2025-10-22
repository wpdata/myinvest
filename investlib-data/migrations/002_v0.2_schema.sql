-- MyInvest V0.2 Database Schema Migration
-- Created: 2025-10-16
-- Description: Add V0.2 tables and extend investment_recommendation for real data integration

-- ============================================================================
-- Extend investment_recommendations table for real data tracking
-- ============================================================================

-- Note: data_source already exists in table, adding remaining V0.2 columns
ALTER TABLE investment_recommendations ADD COLUMN data_freshness VARCHAR(20) CHECK (data_freshness IN ('realtime', 'delayed', 'historical'));
ALTER TABLE investment_recommendations ADD COLUMN advisor_weights TEXT;  -- JSON format: {"kroll": 0.6, "livermore": 0.4}
ALTER TABLE investment_recommendations ADD COLUMN is_automated BOOLEAN DEFAULT 0;

-- ============================================================================
-- Table: strategy_config
-- Purpose: Store multi-strategy fusion weights per user
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategy_config (
    id TEXT PRIMARY KEY,  -- UUID
    user_id VARCHAR(255) DEFAULT 'default_user',
    kroll_weight REAL CHECK (kroll_weight >= 0 AND kroll_weight <= 1),
    livermore_weight REAL CHECK (livermore_weight >= 0 AND livermore_weight <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (ABS(kroll_weight + livermore_weight - 1.0) < 0.001)  -- Sum must equal 1.0
);

-- Default configuration: 50/50 split
INSERT OR IGNORE INTO strategy_config (id, user_id, kroll_weight, livermore_weight)
VALUES ('default-config', 'default_user', 0.5, 0.5);

-- ============================================================================
-- Table: backtest_results
-- Purpose: Store complete backtest execution results and metrics
-- ============================================================================

CREATE TABLE IF NOT EXISTS backtest_results (
    id TEXT PRIMARY KEY,  -- UUID
    strategy_name VARCHAR(50) CHECK (strategy_name IN ('livermore', 'kroll', 'fused')),
    strategy_version VARCHAR(20) DEFAULT 'v1.0.0',
    symbols TEXT,  -- JSON array: ["600519.SH", "000001.SZ"]
    start_date DATE,
    end_date DATE,
    initial_capital REAL,
    final_capital REAL,
    total_return REAL,
    annualized_return REAL,
    max_drawdown REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    win_rate REAL,
    total_trades INTEGER,
    trade_log TEXT,  -- JSON: [{date, symbol, action, entry, exit, pnl, data_source}, ...]
    data_source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for backtest queries
CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_results(strategy_name, strategy_version);
CREATE INDEX IF NOT EXISTS idx_backtest_dates ON backtest_results(start_date, end_date);

-- ============================================================================
-- Table: strategy_approval
-- Purpose: Track approval status of backtested strategies
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategy_approval (
    id TEXT PRIMARY KEY,  -- UUID
    backtest_id TEXT REFERENCES backtest_results(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED')),
    approver_id VARCHAR(255) DEFAULT 'default_user',
    approval_time TIMESTAMP,
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Table: scheduler_log
-- Purpose: Track daily automated task execution
-- ============================================================================

CREATE TABLE IF NOT EXISTS scheduler_log (
    id TEXT PRIMARY KEY,  -- UUID
    execution_time TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('SUCCESS', 'FAILURE', 'PARTIAL')),
    symbols_processed INTEGER,
    recommendations_generated INTEGER,
    data_source VARCHAR(50),
    error_message TEXT,
    duration_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for scheduler queries
CREATE INDEX IF NOT EXISTS idx_scheduler_time ON scheduler_log(execution_time DESC);
CREATE INDEX IF NOT EXISTS idx_scheduler_status ON scheduler_log(status);

-- ============================================================================
-- Migration complete
-- ============================================================================
