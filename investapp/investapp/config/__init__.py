"""Configuration module for MyInvest V0.3."""

from .settings import (
    settings,
    AppSettings,
    DataSourceSettings,
    FuturesSettings,
    OptionsSettings,
    RiskSettings,
    DatabaseSettings,
    # Backward compatibility exports
    DATABASE_URL,
    CACHE_DIR,
    CACHE_RETENTION_DAYS,
    MAX_POSITION_SIZE_PCT,
    DEFAULT_USER_ID,
    PAGE_TITLE,
    PAGE_ICON,
    LAYOUT,
    LABELS,
)

__all__ = [
    'settings',
    'AppSettings',
    'DataSourceSettings',
    'FuturesSettings',
    'OptionsSettings',
    'RiskSettings',
    'DatabaseSettings',
    # Backward compatibility
    'DATABASE_URL',
    'CACHE_DIR',
    'CACHE_RETENTION_DAYS',
    'MAX_POSITION_SIZE_PCT',
    'DEFAULT_USER_ID',
    'PAGE_TITLE',
    'PAGE_ICON',
    'LAYOUT',
    'LABELS',
]
