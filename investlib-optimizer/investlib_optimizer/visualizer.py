"""
MyInvest V0.3 - Parameter Optimization Visualizer (T023)
Plotly heatmaps for parameter performance visualization.
"""

import logging
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


class ParameterVisualizer:
    """Visualization tools for parameter optimization results.

    Generates interactive Plotly heatmaps showing parameter performance.
    """

    def __init__(self):
        """Initialize visualizer."""
        pass

    def generate_heatmap(
        self,
        results_df: pd.DataFrame,
        x_param: str = 'stop_loss_pct',
        y_param: str = 'take_profit_pct',
        z_metric: str = 'sharpe_ratio',
        title: str = None,
        highlight_best: bool = True
    ) -> go.Figure:
        """Generate heatmap for 2D parameter space.

        Args:
            results_df: Grid search results DataFrame
            x_param: X-axis parameter name (e.g., 'stop_loss_pct')
            y_param: Y-axis parameter name (e.g., 'take_profit_pct')
            z_metric: Color metric (e.g., 'sharpe_ratio')
            title: Chart title (default: auto-generated Chinese title)
            highlight_best: Highlight optimal point (default: True)

        Returns:
            Plotly Figure object

        Raises:
            ValueError: If required columns missing
        """
        # Validate columns
        required_cols = [x_param, y_param, z_metric]
        missing_cols = [col for col in required_cols if col not in results_df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in results_df: {missing_cols}")

        # Filter out failed results
        valid_df = results_df[results_df[z_metric] != -999].copy()

        if valid_df.empty:
            raise ValueError("No valid results to visualize")

        # Pivot for heatmap
        pivot_df = valid_df.pivot_table(
            values=z_metric,
            index=y_param,
            columns=x_param,
            aggfunc='mean'
        )

        # Chinese labels
        label_map = {
            'stop_loss_pct': '止损 (%)',
            'take_profit_pct': '止盈 (%)',
            'position_size_pct': '仓位 (%)',
            'sharpe_ratio': '夏普比率',
            'total_return': '总收益率',
            'max_drawdown_pct': '最大回撤 (%)',
            'sortino_ratio': 'Sortino 比率'
        }

        x_label = label_map.get(x_param, x_param)
        y_label = label_map.get(y_param, y_param)
        z_label = label_map.get(z_metric, z_metric)

        # Default title
        if title is None:
            title = f"参数优化热力图：{z_label} vs {x_label}/{y_label}"

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='RdYlGn',  # Red-Yellow-Green
            colorbar=dict(title=z_label),
            hoverongaps=False,
            hovertemplate=(
                f"{x_label}: %{{x}}<br>"
                f"{y_label}: %{{y}}<br>"
                f"{z_label}: %{{z:.3f}}<br>"
                "<extra></extra>"
            )
        ))

        # Highlight optimal point
        if highlight_best:
            best_idx = valid_df[z_metric].idxmax()
            best_row = valid_df.loc[best_idx]

            fig.add_trace(go.Scatter(
                x=[best_row[x_param]],
                y=[best_row[y_param]],
                mode='markers',
                marker=dict(
                    size=15,
                    color='blue',
                    symbol='star',
                    line=dict(color='white', width=2)
                ),
                name=f'最优点: {z_label}={best_row[z_metric]:.3f}',
                hovertemplate=(
                    f"<b>最优参数</b><br>"
                    f"{x_label}: {best_row[x_param]}<br>"
                    f"{y_label}: {best_row[y_param]}<br>"
                    f"{z_label}: {best_row[z_metric]:.3f}<br>"
                    "<extra></extra>"
                )
            ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            font=dict(size=12),
            width=800,
            height=600
        )

        return fig

    def generate_multi_metric_comparison(
        self,
        results_df: pd.DataFrame,
        x_param: str = 'stop_loss_pct',
        y_param: str = 'take_profit_pct'
    ) -> go.Figure:
        """Generate multi-metric comparison with subplots.

        Creates a 2×2 grid showing:
        - Sharpe ratio
        - Total return
        - Max drawdown
        - Win rate

        Args:
            results_df: Grid search results
            x_param: X-axis parameter
            y_param: Y-axis parameter

        Returns:
            Plotly Figure with subplots
        """
        from plotly.subplots import make_subplots

        # Filter valid results
        valid_df = results_df[results_df['sharpe_ratio'] != -999].copy()

        metrics = [
            ('sharpe_ratio', '夏普比率'),
            ('total_return', '总收益率'),
            ('max_drawdown_pct', '最大回撤 (%)'),
            ('win_rate', '胜率')
        ]

        # Create 2x2 subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[label for _, label in metrics],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        for idx, (metric, label) in enumerate(metrics):
            row = (idx // 2) + 1
            col = (idx % 2) + 1

            if metric not in valid_df.columns:
                continue

            # Pivot data
            pivot_df = valid_df.pivot_table(
                values=metric,
                index=y_param,
                columns=x_param,
                aggfunc='mean'
            )

            # Add heatmap
            fig.add_trace(
                go.Heatmap(
                    z=pivot_df.values,
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    colorscale='RdYlGn' if metric != 'max_drawdown_pct' else 'RdYlGn_r',
                    showscale=True,
                    colorbar=dict(
                        title=label,
                        x=1.0 + (col - 1) * 0.05,
                        len=0.4,
                        y=0.75 - (row - 1) * 0.5
                    ),
                    hovertemplate=f"{label}: %{{z:.2f}}<extra></extra>"
                ),
                row=row, col=col
            )

        # Update layout
        fig.update_layout(
            title_text="参数优化多指标对比",
            showlegend=False,
            height=800,
            width=1000
        )

        # Update axes labels
        label_map = {
            'stop_loss_pct': '止损 (%)',
            'take_profit_pct': '止盈 (%)',
            'position_size_pct': '仓位 (%)'
        }

        x_label = label_map.get(x_param, x_param)
        y_label = label_map.get(y_param, y_param)

        for row in range(1, 3):
            for col in range(1, 3):
                fig.update_xaxes(title_text=x_label, row=row, col=col)
                fig.update_yaxes(title_text=y_label, row=row, col=col)

        return fig

    def generate_parameter_distribution(
        self,
        results_df: pd.DataFrame,
        metric: str = 'sharpe_ratio',
        bins: int = 20
    ) -> go.Figure:
        """Generate histogram of metric distribution.

        Args:
            results_df: Grid search results
            metric: Metric to plot distribution
            bins: Number of histogram bins

        Returns:
            Plotly Figure
        """
        valid_df = results_df[results_df[metric] != -999]

        label_map = {
            'sharpe_ratio': '夏普比率',
            'total_return': '总收益率',
            'max_drawdown_pct': '最大回撤 (%)'
        }

        metric_label = label_map.get(metric, metric)

        fig = go.Figure(data=[go.Histogram(
            x=valid_df[metric],
            nbinsx=bins,
            marker_color='steelblue',
            opacity=0.7
        )])

        fig.update_layout(
            title=f"{metric_label} 分布",
            xaxis_title=metric_label,
            yaxis_title="参数组合数量",
            bargap=0.1
        )

        # Add mean and median lines
        mean_val = valid_df[metric].mean()
        median_val = valid_df[metric].median()

        fig.add_vline(
            x=mean_val,
            line_dash="dash",
            line_color="red",
            annotation_text=f"平均: {mean_val:.2f}",
            annotation_position="top"
        )

        fig.add_vline(
            x=median_val,
            line_dash="dash",
            line_color="green",
            annotation_text=f"中位数: {median_val:.2f}",
            annotation_position="bottom"
        )

        return fig
