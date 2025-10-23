# investlib-export

MyInvest V0.3 - Report Export Library

## Features

- **PDF Reports**: Professional backtest reports with Chinese support
  - Cover page with strategy info
  - Performance metrics table
  - Equity curve and drawdown charts
  - Trade history
  - Disclaimer footer

- **Excel Reports**: Trading records with conditional formatting
  - Sheet 1: Trade Details (all trades)
  - Sheet 2: Monthly Summary (aggregated stats)
  - Sheet 3: Position Analysis (holding periods, P&L)
  - Green/red formatting for profits/losses

- **Word Reports**: Holdings and risk analysis
  - Current holdings table
  - Risk metrics (VaR, drawdown, Sharpe)
  - Recommended actions

## Installation

```bash
pip install -e .
```

## Dependencies

- reportlab >= 3.6.0 (PDF generation)
- openpyxl >= 3.1.0 (Excel generation)
- python-docx >= 0.8.11 (Word generation)
- matplotlib >= 3.7.0 (Chart embedding)

## Usage

```python
from investlib_export import PDFReportGenerator, ExcelReportGenerator, WordReportGenerator

# PDF Report
pdf_gen = PDFReportGenerator()
pdf_gen.generate_backtest_report(
    backtest_result=result,
    output_path="backtest_report.pdf",
    title="策略回测报告"
)

# Excel Report
excel_gen = ExcelReportGenerator()
excel_gen.generate_trading_records(
    backtest_result=result,
    output_path="trading_records.xlsx"
)

# Word Report
word_gen = WordReportGenerator()
word_gen.generate_holdings_report(
    holdings=current_holdings,
    risk_metrics=metrics,
    output_path="holdings_report.docx"
)
```

## Chinese Font Support

The library automatically detects and registers Chinese fonts:
- macOS: STHeiti, PingFang
- Linux: Noto Sans CJK
- Windows: Microsoft YaHei, SimSun

If no Chinese fonts are found, the library will log a warning.
