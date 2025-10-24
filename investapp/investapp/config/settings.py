"""
MyInvest V0.3 Centralized Configuration
Type-safe configuration using Pydantic BaseSettings with nested structure.
"""

from pydantic_settings import BaseSettings
from pydantic import validator, Field
from typing import Literal


class DataSourceSettings(BaseSettings):
    """Data source configuration for market data APIs."""

    primary: Literal['efinance'] = 'efinance'
    fallback: Literal['akshare'] = 'akshare'
    auto_fallback: bool = True
    cache_enabled: bool = True
    cache_dir: str = Field(default='./data/cache', description='Cache directory path')
    cache_expiry_days: int = Field(default=7, ge=1, le=30, description='Cache retention period in days')

    class Config:
        env_prefix = 'DATA_SOURCE__'


class FuturesSettings(BaseSettings):
    """Futures trading configuration."""

    enabled: bool = True
    default_margin_rate: float = Field(
        default=0.15,
        ge=0.05,
        le=0.50,
        description='Default margin rate for futures (5%-50%)'
    )
    force_close_margin_rate: float = Field(
        default=0.10,
        ge=0.05,
        le=0.30,
        description='Forced liquidation margin threshold'
    )

    @validator('force_close_margin_rate')
    def validate_force_close_rate(cls, v, values):
        """Ensure forced liquidation rate is lower than default margin rate."""
        if 'default_margin_rate' in values and v >= values['default_margin_rate']:
            raise ValueError('强平线必须低于保证金率 (Forced liquidation rate must be lower than default margin rate)')
        return v

    class Config:
        env_prefix = 'FUTURES__'


class OptionsSettings(BaseSettings):
    """Options trading configuration."""

    enabled: bool = True
    pricing_model: Literal['black_scholes'] = 'black_scholes'
    risk_free_rate: float = Field(
        default=0.03,
        ge=0.0,
        le=0.10,
        description='Risk-free rate for options pricing (0%-10%)'
    )
    default_volatility: float = Field(
        default=0.20,
        ge=0.05,
        le=1.0,
        description='Default volatility when IV is unavailable (5%-100%)'
    )

    class Config:
        env_prefix = 'OPTIONS__'


class RiskSettings(BaseSettings):
    """Risk monitoring configuration."""

    var_confidence: float = Field(
        default=0.95,
        ge=0.90,
        le=0.99,
        description='VaR confidence level (90%-99%)'
    )
    refresh_interval: int = Field(
        default=5,
        ge=1,
        le=60,
        description='Dashboard refresh interval in seconds'
    )
    margin_warning_threshold: float = Field(
        default=0.70,
        ge=0.50,
        le=0.90,
        description='Margin usage warning threshold (50%-90%)'
    )

    class Config:
        env_prefix = 'RISK__'


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = Field(
        default='sqlite:///./data/myinvest.db',
        description='Database connection URL'
    )
    backup_dir: str = Field(
        default='./data/backups',
        description='Database backup directory'
    )

    class Config:
        env_prefix = 'DATABASE__'


class AppSettings(BaseSettings):
    """Main application settings with nested configuration."""

    # Application metadata
    app_name: str = Field(default='MyInvest', description='Application name')
    version: str = Field(default='0.3.0', description='Application version')

    # Page config
    page_title: str = 'MyInvest - 智能投资分析系统'
    page_icon: str = '📊'
    layout: Literal['wide', 'centered'] = 'wide'

    # User settings
    default_user_id: str = 'default_user'
    max_position_size_pct: int = Field(
        default=20,
        ge=1,
        le=100,
        description='Maximum position size as % of capital'
    )

    # Nested settings
    data_source: DataSourceSettings = DataSourceSettings()
    futures: FuturesSettings = FuturesSettings()
    options: OptionsSettings = OptionsSettings()
    risk: RiskSettings = RiskSettings()
    database: DatabaseSettings = DatabaseSettings()

    class Config:
        env_file = '.env'
        env_nested_delimiter = '__'
        case_sensitive = False
        extra = 'ignore'  # Allow extra fields for backward compatibility with V0.2


# Global singleton instance
settings = AppSettings()


# Backward compatibility: Export commonly used constants
DATABASE_URL = settings.database.url
CACHE_DIR = settings.data_source.cache_dir
CACHE_RETENTION_DAYS = settings.data_source.cache_expiry_days
MAX_POSITION_SIZE_PCT = settings.max_position_size_pct
DEFAULT_USER_ID = settings.default_user_id
PAGE_TITLE = settings.page_title
PAGE_ICON = settings.page_icon
LAYOUT = settings.layout

# UI Labels (maintain backward compatibility)
LABELS = {
    "simulation_mode": "当前模式：模拟交易",
    "generate_recommendations": "生成投资建议",
    "import_records": "导入投资记录",
    "confirm_execution": "确认执行",
    "view_explanation": "查看详细解释",
    "total_assets": "总资产",
    "profit_loss": "累计收益",
    "current_holdings": "当前持仓",
}
