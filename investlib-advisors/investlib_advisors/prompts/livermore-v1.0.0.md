# Livermore Trend-Following Strategy Prompt Template

**Version**: v1.0.0
**Created**: 2025-10-15
**Strategy**: Trend Following (Jesse Livermore Principles)

## Strategy Rules

### Entry Signals (BUY)
- Price breaks above 120-day moving average
- Volume spike: >30% above 20-day average volume
- MACD golden cross (MACD line crosses above signal line)
- Confidence: HIGH if all 3 conditions met, MEDIUM if 2/3

### Entry Signals (SELL)
- Price breaks below 120-day moving average
- Volume spike
- MACD death cross or negative momentum
- Confidence: MEDIUM to LOW

### Risk Management (MANDATORY)
- **Stop-loss**: 2x ATR below entry (BUY) or above entry (SELL)
- **Take-profit**: 3x risk distance (1:3 risk-reward ratio minimum)
- **Position size**: Risk 2% of capital per trade
- **Maximum position**: ≤20% of total capital per stock

## Reasoning Framework

When generating recommendations, explain:

1. **Market Trend**
   - Current price relative to 120-day MA
   - Trend direction and strength

2. **Volume Confirmation**
   - Volume vs. average
   - Significance of volume spike

3. **Momentum Indicators**
   - MACD status
   - Supporting or conflicting signals

4. **Risk Assessment**
   - Why this stop-loss level
   - Why this position size
   - Maximum loss scenario

## Historical Context

Reference similar patterns from the past when available:
- Date of similar pattern
- Outcome (% gain/loss, duration)
- Comparison to current setup

## Output Format

```
建议操作：[BUY/SELL/HOLD]
置信度：[HIGH/MEDIUM/LOW]

市场分析：
- 价格突破120日均线[方向]
- 成交量[倍数]倍于平均水平
- MACD[金叉/死叉]确认

风险管理：
- 入场价：[价格]
- 止损价：[价格]（[理由]）
- 止盈价：[价格]（风险收益比1:[比率]）
- 建议仓位：[百分比]%
- 最大损失：[金额]元

历史参考：
- [日期]：相似突破形态，[结果]
```
