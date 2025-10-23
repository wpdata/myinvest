"""
MyInvest V0.3 - PDF Report Generator (T027)
Professional backtest reports with Chinese support using ReportLab.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet

from investlib_export.font_setup import get_chinese_styles, get_disclaimer_text


logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Professional PDF backtest report generator with Chinese support.

    Generates comprehensive backtest reports including:
    - Cover page
    - Performance metrics
    - Equity curve chart
    - Drawdown chart
    - Trade history
    - Disclaimer
    """

    def __init__(self):
        """Initialize PDF report generator."""
        self.styles = get_chinese_styles()
        self.page_width, self.page_height = A4

    def generate_backtest_report(
        self,
        backtest_result: Dict[str, Any],
        output_path: str,
        title: str = "策略回测报告"
    ) -> str:
        """Generate complete backtest PDF report.

        Args:
            backtest_result: Backtest result dict from BacktestRunner
            output_path: Output PDF file path
            title: Report title (default: "策略回测报告")

        Returns:
            str: Path to generated PDF file

        Raises:
            ValueError: If backtest_result invalid
        """
        logger.info(f"[PDFGenerator] Generating report: {output_path}")

        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build content
        story = []

        # Cover page
        story.extend(self._build_cover_page(backtest_result, title))
        story.append(PageBreak())

        # Performance metrics
        story.extend(self._build_metrics_page(backtest_result))
        story.append(PageBreak())

        # Equity curve
        story.extend(self._build_equity_curve_page(backtest_result))
        story.append(PageBreak())

        # Trade history
        story.extend(self._build_trade_history_page(backtest_result))

        # Disclaimer footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(get_disclaimer_text(), self.styles['Footer']))

        # Build PDF
        doc.build(story)

        logger.info(f"[PDFGenerator] Report generated: {output_path}")
        return output_path

    def _build_cover_page(
        self,
        result: Dict[str, Any],
        title: str
    ) -> list:
        """Build cover page content."""
        content = []

        # Title
        content.append(Spacer(1, 2*inch))
        content.append(Paragraph(title, self.styles['Title']))
        content.append(Spacer(1, 0.5*inch))

        # Basic info
        strategy_name = result.get('strategy_name', 'Unknown')
        symbols = result.get('symbols', result.get('symbol', 'Unknown'))
        if isinstance(symbols, list):
            symbols = ', '.join(symbols)

        start_date = result.get('start_date', 'N/A')
        end_date = result.get('end_date', 'N/A')

        info_text = f"""
        <b>策略名称:</b> {strategy_name}<br/>
        <b>股票代码:</b> {symbols}<br/>
        <b>回测期间:</b> {start_date} 至 {end_date}<br/>
        <b>生成时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """

        content.append(Paragraph(info_text, self.styles['Body']))

        return content

    def _build_metrics_page(self, result: Dict[str, Any]) -> list:
        """Build performance metrics page."""
        content = []

        content.append(Paragraph("一、性能指标", self.styles['Heading1']))
        content.append(Spacer(1, 0.2*inch))

        # Extract metrics
        initial_capital = result.get('initial_capital', 0)
        final_capital = result.get('final_capital', 0)
        total_return = result.get('total_return', 0)
        total_trades = result.get('total_trades', 0)

        # Create metrics table
        data = [
            ['指标', '数值'],
            ['初始资金', f'¥{initial_capital:,.2f}'],
            ['最终资金', f'¥{final_capital:,.2f}'],
            ['总收益率', f'{total_return*100:.2f}%'],
            ['总交易次数', f'{total_trades}']
        ]

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        content.append(table)

        return content

    def _build_equity_curve_page(self, result: Dict[str, Any]) -> list:
        """Build equity curve chart page."""
        content = []

        content.append(Paragraph("二、权益曲线", self.styles['Heading1']))
        content.append(Spacer(1, 0.2*inch))

        # Generate equity curve chart
        equity_curve = result.get('equity_curve', [])

        if equity_curve:
            # Create matplotlib chart
            fig, ax = plt.subplots(figsize=(8, 4))

            dates = [point['date'] for point in equity_curve]
            values = [point['portfolio_value'] for point in equity_curve]

            ax.plot(dates, values, linewidth=2, color='#2c5aa0')
            ax.set_xlabel('日期', fontsize=10)
            ax.set_ylabel('账户价值 (¥)', fontsize=10)
            ax.set_title('权益曲线', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)

            # Rotate x-axis labels
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150)
            buf.seek(0)
            plt.close(fig)

            # Add to PDF
            img = Image(buf, width=6*inch, height=3*inch)
            content.append(img)
        else:
            content.append(Paragraph("无权益曲线数据", self.styles['Body']))

        return content

    def _build_trade_history_page(self, result: Dict[str, Any]) -> list:
        """Build trade history page."""
        content = []

        content.append(Paragraph("三、交易历史", self.styles['Heading1']))
        content.append(Spacer(1, 0.2*inch))

        trade_log = result.get('trade_log', [])

        if trade_log:
            # Limit to first 50 trades
            trades_to_show = trade_log[:50]

            # Build table data
            data = [['日期', '操作', '数量', '价格', '总金额']]

            for trade in trades_to_show:
                data.append([
                    trade.get('timestamp', 'N/A'),
                    '买入' if trade.get('action') == 'BUY' else '卖出',
                    str(trade.get('quantity', 0)),
                    f"¥{trade.get('price', 0):.2f}",
                    f"¥{trade.get('total_value', 0):,.2f}"
                ])

            table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            content.append(table)

            if len(trade_log) > 50:
                content.append(Spacer(1, 0.2*inch))
                content.append(Paragraph(
                    f"注：仅显示前50笔交易，共{len(trade_log)}笔交易",
                    self.styles['Caption']
                ))
        else:
            content.append(Paragraph("无交易记录", self.styles['Body']))

        return content
