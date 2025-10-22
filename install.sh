#!/bin/bash
# MyInvest v0.1 - Installation Script
# Run this after activating your conda environment: conda activate invest

set -e

echo "=== Installing MyInvest v0.1 ==="

# Install main dependencies
echo "Installing main dependencies..."
pip install -r requirements.txt

# Install local libraries in editable mode
echo "Installing investlib-data..."
pip install -e investlib-data

echo "Installing investlib-quant..."
pip install -e investlib-quant

echo "Installing investlib-advisors..."
pip install -e investlib-advisors

# Create data directory
echo "Creating data directory..."
mkdir -p data/cache
touch data/.gitkeep

# Copy environment template
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your TUSHARE_TOKEN"
fi

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your TUSHARE_TOKEN"
echo "2. Initialize database: python -m investlib_data.cli init-db"
echo "3. Launch app: streamlit run investapp/investapp/app.py"
