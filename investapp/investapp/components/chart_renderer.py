"""Functions for rendering Plotly charts."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def render_profit_loss_curve(data, timeframe="daily"):
    """Renders a profit/loss curve.

    Args:
        data (list): A list of tuples (date, profit_loss).
        timeframe (str): The timeframe for the chart (daily, weekly, monthly).

    Returns:
        A Plotly figure object.
    """
    if not data:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="暂无盈亏数据<br>添加投资记录后将显示盈亏曲线",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(
            title="累计收益曲线",
            font=dict(family="Microsoft YaHei, SimHei, sans-serif")
        )
        return fig

    df = pd.DataFrame(data, columns=["date", "profit_loss"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date")

    # For v0.1 MVP: profit_loss values are already cumulative or independent
    # No need to cumsum again

    # Resample data based on timeframe
    if timeframe != "daily":
        resample_rule = {"weekly": "W-MON", "monthly": "M"}.get(timeframe, "D")
        df = df.set_index("date").resample(resample_rule).last().reset_index()

    fig = px.line(df, x="date", y="profit_loss", title="累计收益曲线")
    fig.update_layout(
        xaxis_title="日期",
        yaxis_title="累计收益 (CNY)",
        font=dict(family="Microsoft YaHei, SimHei, sans-serif")
    )

    # Add zero line for reference
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    return fig

def render_asset_distribution(data):
    """Renders an asset distribution pie chart.

    Args:
        data (list): A list of CurrentHolding objects.

    Returns:
        A Plotly figure object.
    """
    if not data:
        return go.Figure()

    labels = [holding.symbol for holding in data]
    values = [holding.quantity * holding.current_price for holding in data]

    fig = px.pie(values=values, names=labels, title="资产分布")
    fig.update_layout(font=dict(family="Microsoft YaHei, SimHei, sans-serif"))
    return fig


def render_kline_chart(market_data, timeframe="daily"):
    """Renders a K-line (candlestick) chart with volume.

    Args:
        market_data (pd.DataFrame): DataFrame with columns: timestamp, open, high, low, close, volume
        timeframe (str): The timeframe for the chart (daily, weekly, monthly)

    Returns:
        A Plotly figure object with candlestick and volume subplot
    """
    if market_data is None or market_data.empty:
        return go.Figure()

    df = market_data.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # Resample data based on timeframe
    if timeframe != "daily":
        resample_rule = {"weekly": "W-MON", "monthly": "M"}.get(timeframe, "D")
        df = df.set_index('timestamp').resample(resample_rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).reset_index()

    # Create figure with secondary y-axis for volume
    fig = go.Figure()

    # Add candlestick trace
    # 中国市场习惯：红涨绿跌（与国际市场相反）
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='K线',
        increasing_line_color='#EF5350',  # 红色 - 涨
        decreasing_line_color='#26A69A'   # 绿色 - 跌
    ))

    # Add 120-day MA overlay if daily data
    if timeframe == "daily" and len(df) >= 120:
        df['ma120'] = df['close'].rolling(window=120).mean()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['ma120'],
            mode='lines',
            name='120日均线',
            line=dict(color='orange', width=1)
        ))

    # Add volume bars (on same subplot, scaled separately)
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        name='成交量',
        marker_color='rgba(100, 100, 100, 0.3)',
        yaxis='y2'
    ))

    # Update layout
    fig.update_layout(
        title='K线图',
        xaxis_title='日期',
        yaxis_title='价格 (¥)',
        yaxis2=dict(
            title='成交量',
            overlaying='y',
            side='right',
            showgrid=False
        ),
        xaxis_rangeslider_visible=False,
        font=dict(family="Microsoft YaHei, SimHei, sans-serif"),
        height=600,
        hovermode='x unified'
    )

    return fig
