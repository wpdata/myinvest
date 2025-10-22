#!/bin/bash
# 安装 MyInvest 依赖
# 用于 invest conda 环境

set -e

echo "======================================"
echo "Installing MyInvest Dependencies"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Activate environment
echo "1. Activating invest environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate invest
echo -e "${GREEN}✓${NC} Environment activated"

# Install core dependencies
echo ""
echo "2. Installing core dependencies..."
pip install --upgrade pip

# Core libraries
echo "  Installing Click (CLI framework)..."
pip install click>=8.1.0

echo "  Installing SQLAlchemy (Database ORM)..."
pip install sqlalchemy>=2.0.0

echo "  Installing Pandas (Data processing)..."
pip install pandas>=2.1.0

echo "  Installing pytest (Testing)..."
pip install pytest>=7.4.0 pytest-cov>=4.1.0

echo "  Installing python-dotenv (Environment variables)..."
pip install python-dotenv>=1.0.0

# Optional but recommended
echo ""
echo "3. Installing optional dependencies..."
echo "  Installing Tushare (Market data - optional)..."
pip install tushare || echo -e "${YELLOW}⚠${NC} Tushare install failed (optional)"

echo "  Installing AKShare (Backup market data - optional)..."
pip install akshare || echo -e "${YELLOW}⚠${NC} AKShare install failed (optional)"

echo "  Installing Google Generative AI (AI Advisor - optional)..."
pip install google-generativeai || echo -e "${YELLOW}⚠${NC} Google AI install failed (optional)"

echo "  Installing Streamlit (UI - optional)..."
pip install streamlit>=1.40.0 || echo -e "${YELLOW}⚠${NC} Streamlit install failed (optional)"

echo "  Installing Plotly (Charts - optional)..."
pip install plotly>=5.22.0 || echo -e "${YELLOW}⚠${NC} Plotly install failed (optional)"

# Install local packages in development mode
echo ""
echo "4. Installing local packages (development mode)..."
cd /Users/pw/ai/myinvest

if [ -f "investlib-data/setup.py" ]; then
    echo "  Installing investlib-data..."
    pip install -e investlib-data/
else
    echo -e "${YELLOW}⚠${NC} investlib-data/setup.py not found"
fi

if [ -f "investlib-quant/setup.py" ]; then
    echo "  Installing investlib-quant..."
    pip install -e investlib-quant/
else
    echo -e "${YELLOW}⚠${NC} investlib-quant/setup.py not found"
fi

if [ -f "investlib-advisors/setup.py" ]; then
    echo "  Installing investlib-advisors..."
    pip install -e investlib-advisors/
else
    echo -e "${YELLOW}⚠${NC} investlib-advisors/setup.py not found"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✓ Dependencies Installed!${NC}"
echo "======================================"
echo ""
echo "Verify installation:"
echo "  python -c 'import click; import sqlalchemy; import pandas; print(\"All core packages OK\")'"
echo ""
