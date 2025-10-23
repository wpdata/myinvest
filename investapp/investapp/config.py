"""InvestApp Configuration."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database
# 使用绝对路径确保无论从哪个目录启动都能找到正确的数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////Users/pw/ai/myinvest/data/myinvest.db")

# Market Data APIs
# Note: Efinance is now the primary data source (free, no token required)
# AKShare is used as fallback
CACHE_DIR = os.getenv("CACHE_DIR", "/Users/pw/ai/myinvest/data/cache")

# Application Settings
MAX_POSITION_SIZE_PCT = 20  # Maximum position size as % of capital
CACHE_RETENTION_DAYS = 7
DEFAULT_USER_ID = "default_user"

# Streamlit Page Config
PAGE_TITLE = "MyInvest - 智能投资分析系统"
PAGE_ICON = "📊"
LAYOUT = "wide"

# UI Labels (Chinese)
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
