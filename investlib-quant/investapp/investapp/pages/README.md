# Investapp Pages

This directory contains Streamlit pages for the MyInvest application.

## Pages

- `1_dashboard.py` - Main dashboard with recommendations and data freshness indicators
- `3_market.py` - Market data page showing real-time data sources
- `5_system_status.py` - API monitoring and system status
- `6_backtest.py` - Backtesting interface
- `7_scheduler_log.py` - Scheduler execution history
- `8_approval.py` - Strategy approval workflow

## V0.2 Updates

All pages updated to display data provenance:
- Data source badges on all data displays
- Freshness indicators (realtime/delayed/historical)
- "Refresh Data" buttons to bypass cache
- Warnings when using historical data
