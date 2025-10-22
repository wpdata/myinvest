"""Chart Renderer Component for data visualization."""

import plotly.graph_objects as go
import pandas as pd
from typing import Dict


def render_profit_loss_curve(data: pd.DataFrame, timeframe: str = 'daily') -> go.Figure:
    """Render profit/loss curve chart."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="暂无数据", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=20))
        return fig

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['date'], y=data['profit_loss'],
        mode='lines+markers', name='累计盈亏',
        line=dict(color='#1976d2', width=2)
    ))
    fig.update_layout(title=f"盈亏曲线", height=400)
    return fig


def render_asset_distribution(data: Dict[str, float]) -> go.Figure:
    """Render asset distribution pie chart."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(text="暂无持仓", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return fig

    fig = go.Figure(data=[go.Pie(labels=list(data.keys()), values=list(data.values()))])
    fig.update_layout(title="资产分布", height=400)
    return fig
