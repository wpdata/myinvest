"""SQLAlchemy ORM models for MyInvest v0.1."""

from sqlalchemy import String, Float, Date, DateTime, Enum, UUID, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, date, timedelta
from typing import Optional
import enum
import uuid
import hashlib


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Enums
class AssetType(enum.Enum):
    """Asset type classification."""
    STOCK = "stock"              # 股票 (A股)
    ETF = "etf"                  # ETF基金
    FUND = "fund"                # 场外基金
    FUTURES = "futures"          # 期货
    OPTION = "option"            # 期权
    BOND = "bond"                # 债券
    CONVERTIBLE_BOND = "convertible_bond"  # 可转债
    OTHER = "other"              # 其他


class DataSource(enum.Enum):
    """Data source for investment records."""
    MANUAL_ENTRY = "manual_entry"
    BROKER_STATEMENT = "broker_statement"
    API_IMPORT = "api_import"


class DataFreshness(enum.Enum):
    """Market data freshness indicator."""
    REALTIME = "realtime"       # <5s delay
    DELAYED = "delayed"         # 5s-15min delay
    HISTORICAL = "historical"   # >15min delay


class AdjustmentMethod(enum.Enum):
    """Price adjustment method."""
    FORWARD = "forward"         # 前复权
    BACKWARD = "backward"       # 后复权
    UNADJUSTED = "unadjusted"   # 不复权


class RecommendationAction(enum.Enum):
    """Investment recommendation action."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Confidence(enum.Enum):
    """Recommendation confidence level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class OperationType(enum.Enum):
    """Operation type for logging."""
    BUY = "BUY"
    SELL = "SELL"
    MODIFY = "MODIFY"
    CANCEL = "CANCEL"


class ExecutionStatus(enum.Enum):
    """Execution status."""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


class ExecutionMode(enum.Enum):
    """Execution mode."""
    SIMULATED = "SIMULATED"
    LIVE = "LIVE"


# Models
class InvestmentRecord(Base):
    """Historical investment transaction record."""
    __tablename__ = "investment_records"

    # Primary key
    record_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Investment details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False, default=AssetType.STOCK)
    purchase_amount: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    # Optional sale information
    sale_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sale_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Multi-asset support (v0.3)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, default="long", server_default="long")
    margin_used: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0.0")

    # Data integrity (Constitution Principle VII)
    data_source: Mapped[DataSource] = mapped_column(Enum(DataSource), nullable=False)
    ingestion_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_checksum(self) -> str:
        """Calculate SHA256 checksum for data integrity."""
        data = f"{self.symbol}{self.purchase_date}{self.purchase_price}{self.quantity}"
        return hashlib.sha256(data.encode()).hexdigest()

    def __repr__(self):
        return f"<InvestmentRecord {self.symbol} {self.purchase_date} {self.quantity}@{self.purchase_price}>"


class MarketDataPoint(Base):
    """Market data with 7-day cache retention."""
    __tablename__ = "market_data"

    # Composite primary key
    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)

    # OHLCV data
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)

    # Data integrity
    api_source: Mapped[str] = mapped_column(String(50), nullable=False)
    api_version: Mapped[str] = mapped_column(String(20), nullable=False)
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    data_freshness: Mapped[DataFreshness] = mapped_column(Enum(DataFreshness), nullable=False)
    adjustment_method: Mapped[AdjustmentMethod] = mapped_column(Enum(AdjustmentMethod), nullable=False)

    # 7-day cache expiry
    cache_expiry_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=7),
        nullable=False,
        index=True
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MarketDataPoint {self.symbol} {self.timestamp} C:{self.close_price}>"


class InvestmentRecommendation(Base):
    """AI-generated investment recommendation."""
    __tablename__ = "investment_recommendations"

    # Primary key
    recommendation_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Recommendation details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    action: Mapped[RecommendationAction] = mapped_column(Enum(RecommendationAction), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)  # MANDATORY
    take_profit: Mapped[float] = mapped_column(Float, nullable=False)
    position_size_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_loss_amount: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)

    # AI Advisor metadata (Constitution Principle IX)
    advisor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    advisor_version: Mapped[str] = mapped_column(String(20), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Explainability
    reasoning: Mapped[str] = mapped_column(String(1000), nullable=False)
    confidence: Mapped[Confidence] = mapped_column(Enum(Confidence), nullable=False)
    key_factors: Mapped[str] = mapped_column(String(500), nullable=False)  # JSON
    historical_precedents: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # JSON

    # Data provenance
    market_data_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)

    # Audit
    created_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<InvestmentRecommendation {self.symbol} {self.action.value} {self.entry_price}>"


class OperationLog(Base):
    """Append-only audit trail (Constitution Principle VIII)."""
    __tablename__ = "operation_log"

    # Prevent updates/deletes at ORM level
    __mapper_args__ = {"confirm_deleted_rows": False}

    # Primary key
    operation_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Immutable timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # User and operation details
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, default="default_user")
    operation_type: Mapped[OperationType] = mapped_column(Enum(OperationType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Traceability
    original_recommendation: Mapped[str] = mapped_column(String(2000), nullable=False)  # JSON
    user_modification: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)  # JSON

    # Execution details
    execution_status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), nullable=False)
    execution_mode: Mapped[ExecutionMode] = mapped_column(Enum(ExecutionMode), nullable=False, default=ExecutionMode.SIMULATED)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Foreign key
    recommendation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # NO updated_at (append-only)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<OperationLog {self.operation_type.value} {self.symbol} {self.timestamp}>"


# Append-only enforcement
@event.listens_for(OperationLog, 'before_update')
def prevent_operation_log_update(mapper, connection, target):
    raise ValueError("OperationLog is append-only, updates not allowed")


@event.listens_for(OperationLog, 'before_delete')
def prevent_operation_log_delete(mapper, connection, target):
    raise ValueError("OperationLog is append-only, deletes not allowed")


class AccountBalance(Base):
    """Account balance tracking for different asset types."""
    __tablename__ = "account_balances"

    # Primary key
    balance_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Account details
    account_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False, unique=True, index=True)
    available_cash: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timestamps
    last_update_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AccountBalance {self.account_type.value} {self.available_cash:.2f}>"


class CurrentHolding(Base):
    """Current portfolio positions."""
    __tablename__ = "current_holdings"

    # Primary key
    holding_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Holdings details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False, default=AssetType.STOCK)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)  # Average cost
    current_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Calculated fields
    profit_loss_amount: Mapped[float] = mapped_column(Float, nullable=False)
    profit_loss_pct: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamps
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_update_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Multi-asset support (v0.3)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, default="long", server_default="long")
    margin_used: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0.0")

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_profit_loss(self):
        """Calculate P&L metrics."""
        self.profit_loss_amount = (self.current_price - self.purchase_price) * self.quantity
        self.profit_loss_pct = ((self.current_price / self.purchase_price) - 1) * 100

    def __repr__(self):
        return f"<CurrentHolding {self.symbol} {self.quantity}@{self.purchase_price}>"


class ApprovalStatus(enum.Enum):
    """Approval workflow status."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUEST_REVISION = "REQUEST_REVISION"


class SchedulerStatus(enum.Enum):
    """Scheduler run status."""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILURE = "FAILURE"


class StrategyApproval(Base):
    """Human-in-the-loop approval for automated recommendations."""
    __tablename__ = "strategy_approval"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign key to recommendation
    recommendation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Approval workflow
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), nullable=False, index=True)
    submitted_by: Mapped[str] = mapped_column(String(50), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    approved_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Risk assessment
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_loss_pct: Mapped[float] = mapped_column(Float, nullable=False)
    
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    from sqlalchemy.orm import relationship
    recommendation = relationship("InvestmentRecommendation", foreign_keys=[recommendation_id], 
                                  primaryjoin="StrategyApproval.recommendation_id==InvestmentRecommendation.recommendation_id")

    def __repr__(self):
        return f"<StrategyApproval {self.recommendation_id} {self.status.value}>"


class SchedulerLog(Base):
    """Daily scheduler execution log."""
    __tablename__ = "scheduler_log"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Execution details
    run_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[SchedulerStatus] = mapped_column(Enum(SchedulerStatus), nullable=False)
    
    symbols_analyzed: Mapped[int] = mapped_column(nullable=False, default=0)
    recommendations_generated: Mapped[int] = mapped_column(nullable=False, default=0)
    errors_encountered: Mapped[int] = mapped_column(nullable=False, default=0)
    
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    log_message: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SchedulerLog {self.run_timestamp} {self.status.value}>"


class BacktestResult(Base):
    """Historical backtest results for strategies."""
    __tablename__ = "backtest_results"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Backtest metadata
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Performance metrics
    total_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    annualized_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    win_rate_pct: Mapped[float] = mapped_column(Float, nullable=False)

    total_trades: Mapped[int] = mapped_column(nullable=False)
    winning_trades: Mapped[int] = mapped_column(nullable=False)
    losing_trades: Mapped[int] = mapped_column(nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BacktestResult {self.strategy_name} {self.symbol} {self.total_return_pct:.2f}%>"


class StrategyConfig(Base):
    """Strategy configuration and parameters."""
    __tablename__ = "strategy_config"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Strategy identification
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    
    # Parameters (JSON)
    parameters: Mapped[str] = mapped_column(String(2000), nullable=False)  # JSON
    
    # Weights for fusion
    fusion_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StrategyConfig {self.strategy_name} enabled={self.enabled}>"
