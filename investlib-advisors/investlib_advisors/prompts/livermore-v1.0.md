# Livermore Advisor v1.0

**Date**: 2025-10-15
**Version**: 1.0.0
**Strategy**: Trend Following (based on Jesse Livermore's methods)

## Buy Signal Conditions

1.  **Primary Indicator**: Price breaks above 120-day moving average.
2.  **Confirmation**: Trading volume is at least 20% above the 20-day average volume.
3.  **Secondary Confirmation**: MACD (12, 26, 9) shows a golden cross.

## Risk Management Rules

-   **Stop-Loss**: Set at 2x the Average True Range (ATR) below the entry price.
-   **Position Sizing**: Risk a maximum of 2% of total portfolio capital on a single trade.
-   **Take-Profit Target**: Set at 3x the risked amount (i.e., a 1:3 risk-reward ratio).

## Explanation Template

This section defines the structure for generating the `reasoning` field in the `InvestmentRecommendation` model.

### Template Structure

**Signal**: {action} {symbol}
**Entry Price**: {entry_price}
**Stop-Loss**: {stop_loss} (Calculated as 2x ATR of {atr_value})
**Take-Profit**: {take_profit}
**Position Size**: {position_pct}% of capital ({position_amount} shares)
**Maximum Loss**: {max_loss_amount}

**Market Signals Triggered**:

{for signal in triggers}
- {signal}
{endfor}

**Historical Precedents**:

{for precedent in historical_matches}
- On {precedent.date}, a similar pattern led to an outcome of {precedent.outcome}.
{endfor}

**Confidence Level**: {confidence} (based on {num_signals}/3 confirming signals)
