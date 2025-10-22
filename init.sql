-- MyInvest Database Initialization Script

-- 创建投资记录表
CREATE TABLE IF NOT EXISTS investment_records (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    symbol_name VARCHAR(100) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL')),
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    trade_date TIMESTAMP NOT NULL,

    -- 数据完整性字段
    source VARCHAR(50) NOT NULL CHECK (source IN ('manual_entry', 'broker_statement', 'api_import')),
    ingestion_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    checksum VARCHAR(64),

    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_investment_records_symbol ON investment_records(symbol);
CREATE INDEX idx_investment_records_trade_date ON investment_records(trade_date);

-- 创建操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id SERIAL PRIMARY KEY,
    operation_id UUID NOT NULL UNIQUE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    operation_type VARCHAR(20) NOT NULL CHECK (operation_type IN ('BUY', 'SELL', 'MODIFY', 'CANCEL')),
    symbol VARCHAR(20) NOT NULL,

    -- 系统原始建议（JSON）
    original_recommendation JSONB NOT NULL,

    -- 用户修改（JSON，可为空）
    user_modification JSONB,

    -- 执行状态
    execution_status VARCHAR(20) NOT NULL CHECK (execution_status IN ('PENDING', 'EXECUTED', 'CANCELLED')),

    -- 用户备注
    notes TEXT
);

CREATE INDEX idx_operation_logs_timestamp ON operation_logs(timestamp DESC);
CREATE INDEX idx_operation_logs_symbol ON operation_logs(symbol);

-- 创建持仓表
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    symbol_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    avg_cost DECIMAL(10, 2) NOT NULL CHECK (avg_cost > 0),
    current_price DECIMAL(10, 2),
    unrealized_pnl DECIMAL(15, 2),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 创建建议记录表（用于审计和回溯）
CREATE TABLE IF NOT EXISTS recommendation_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    recommendation JSONB NOT NULL,  -- 完整的建议 JSON
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recommendation_history_symbol ON recommendation_history(symbol);
CREATE INDEX idx_recommendation_history_created_at ON recommendation_history(created_at DESC);

-- 创建市场数据缓存表（7天过期）
CREATE TABLE IF NOT EXISTS market_data_cache (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10, 2) NOT NULL,
    high_price DECIMAL(10, 2) NOT NULL,
    low_price DECIMAL(10, 2) NOT NULL,
    close_price DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,

    -- 数据源元数据
    api_source VARCHAR(100) NOT NULL,
    api_version VARCHAR(50),
    retrieval_timestamp TIMESTAMP NOT NULL,
    data_freshness VARCHAR(20),
    adjustment_method VARCHAR(20),

    -- 缓存过期时间
    cache_expiry_date TIMESTAMP NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    UNIQUE(symbol, timestamp)
);

CREATE INDEX idx_market_data_cache_symbol ON market_data_cache(symbol);
CREATE INDEX idx_market_data_cache_timestamp ON market_data_cache(timestamp);
CREATE INDEX idx_market_data_cache_expiry ON market_data_cache(cache_expiry_date);

-- 插入示例数据（可选）
INSERT INTO positions (symbol, symbol_name, quantity, avg_cost, current_price, unrealized_pnl) VALUES
    ('600519.SH', '贵州茅台', 0, 0, 0, 0)
ON CONFLICT (symbol) DO NOTHING;

COMMENT ON TABLE investment_records IS '个人投资历史记录表';
COMMENT ON TABLE operation_logs IS '操作日志表（审计用）';
COMMENT ON TABLE positions IS '当前持仓表';
COMMENT ON TABLE recommendation_history IS '投资建议历史记录表';
COMMENT ON TABLE market_data_cache IS '市场数据缓存表（7天过期）';
