# Quickstart: MyInvest v0.1

**Date**: 2025-10-14
**Estimated Setup Time**: 10 minutes

## Prerequisites

- Python 3.10 or higher
- Git
- 无需API Token（使用免费的Efinance数据源）

## Setup Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd myinvest
git checkout 001-myinvest-v0-1
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file in project root:

```bash
cp .env.example .env
```

编辑 `.env` 文件（可选，使用默认配置即可）:

```
DATABASE_URL=sqlite:///data/myinvest.db
CACHE_DIR=data/cache

# 注意：Efinance 为主数据源（免费，无需 Token）
# AKShare 为备份数据源
```

### 5. Initialize Database

```bash
python -m investlib_data.cli init-db
```

### 6. Launch Application

```bash
streamlit run investapp/investapp/app.py
```

Application will open in browser at http://localhost:8501

## First Steps

### Import Sample Investment Records

1. Prepare CSV file with format:
```csv
symbol,purchase_date,purchase_price,quantity,sale_date,sale_price
600519.SH,2023-01-15,1500.00,100,,
000001.SZ,2023-02-20,12.50,1000,2023-06-15,14.80
```

2. Click "Import Investment Records" button
3. Upload CSV file
4. Review validation results

### Generate Recommendations

1. Click "Generate Recommendations" button on dashboard
2. Wait 5-10 seconds for analysis
3. Review recommendation cards with stop-loss, take-profit, max loss
4. Click "View Detailed Explanation" for reasoning

### Execute Simulated Trade

1. Click "Confirm Execution" on recommendation card
2. Review second confirmation dialog
3. Optionally modify stop-loss or position size
4. Click "Confirm Execution" in dialog
5. Check "Operation Logs" page for recorded transaction

## Troubleshooting

### Market Data API Error

**Problem**: `EfinanceAPIError` or `AKShareAPIError`
**Solution**: 检查网络连接，系统会自动在Efinance和AKShare之间切换

### Database Error

**Problem**: `sqlite3.OperationalError: no such table`
**Solution**: Run `python -m investlib_data.cli init-db` to create tables

### Import Shows All Errors

**Problem**: All CSV rows rejected with validation errors
**Solution**: Check CSV format matches template, ensure prices > 0, dates <= today

## Development Workflow

### Run Tests

```bash
# All tests
pytest

# Integration tests only (requires API token)
pytest tests/integration

# With coverage
pytest --cov=investlib_data --cov=investlib_quant --cov=investlib_advisors
```

### CLI Commands

```bash
# Fetch market data
python -m investlib_data.cli fetch-market --symbol 600519.SH --output json

# Analyze with Livermore strategy
python -m investlib_quant.cli analyze --symbol 600519.SH --strategy livermore

# Ask Livermore advisor
python -m investlib_advisors.cli ask --advisor livermore --context data.json
```

## Next Steps

- Review [data-model.md](data-model.md) for database schema
- Read [research.md](research.md) for technology decisions
- Check [contracts/](contracts/) for API specifications
- Proceed to `/speckit.tasks` to generate implementation tasks

**Ready to start development!**
