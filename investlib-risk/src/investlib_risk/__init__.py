"""MyInvest V0.3 - Risk Metrics Calculation Library

Provides risk analysis tools:
- VaR/CVaR calculation (Historical Simulation)
- Correlation matrix with rolling windows
- Concentration risk analysis
- Margin risk monitoring
"""

__version__ = "0.3.0"

from investlib_risk.var import calculate_var_historical, calculate_cvar_historical
from investlib_risk.correlation import CorrelationCalculator
from investlib_risk.concentration import calculate_concentration, calculate_industry_concentration
from investlib_risk.margin_risk import calculate_margin_usage_rate, calculate_liquidation_distance, generate_liquidation_warnings

__all__ = [
    "calculate_var_historical",
    "calculate_cvar_historical",
    "CorrelationCalculator",
    "calculate_concentration",
    "calculate_industry_concentration",
    "calculate_margin_usage_rate",
    "calculate_liquidation_distance",
    "generate_liquidation_warnings",
]
