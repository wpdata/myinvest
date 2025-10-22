# InvestApp

Streamlit-based UI orchestrator for MyInvest v0.1.

## Features

- Multi-page app (Dashboard, Records, Market Data, Logs)
- Real-time chart rendering
- Simulated trading mode
- Operation logging

## Launch

```bash
streamlit run investapp/investapp/app.py
```

## Pages

- **Dashboard** (1_dashboard.py): Investment overview + recommendations
- **Records** (2_records.py): Import and manage investment records
- **Market Data** (3_market.py): K-line charts and data freshness
- **Logs** (4_logs.py): Operation log viewer
