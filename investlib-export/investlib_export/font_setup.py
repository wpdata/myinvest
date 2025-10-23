"""
MyInvest V0.3 - Chinese Font Setup for ReportLab (T026)
Configures Chinese fonts for PDF generation.
"""

import logging
import os
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


logger = logging.getLogger(__name__)


def setup_chinese_fonts():
    """Setup Chinese fonts for ReportLab PDF generation.

    Tries multiple font sources in order:
    1. System fonts (macOS/Linux/Windows)
    2. Fallback to default fonts if Chinese fonts unavailable

    Returns:
        bool: True if Chinese fonts registered successfully
    """
    # Font search paths by OS
    font_paths = [
        # macOS
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        # Linux
        '/usr/share/fonts/truetype/arphic/uming.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        # Windows
        'C:/Windows/Fonts/msyh.ttc',  # Microsoft YaHei
        'C:/Windows/Fonts/simsun.ttc',  # SimSun
    ]

    registered = False

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # Register font
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                logger.info(f"[FontSetup] Registered Chinese font: {font_path}")
                registered = True
                break
            except Exception as e:
                logger.warning(f"[FontSetup] Failed to register {font_path}: {e}")
                continue

    if not registered:
        logger.warning(
            "[FontSetup] No Chinese fonts found. PDF may not render Chinese characters correctly. "
            "Consider installing Noto Sans CJK or Microsoft YaHei."
        )
        # Fallback: use Helvetica (won't show Chinese)
        return False

    return True


def get_chinese_styles():
    """Get paragraph styles configured for Chinese fonts.

    Returns:
        dict: Paragraph styles for different purposes
    """
    styles = getSampleStyleSheet()

    # Check if Chinese font is available
    try:
        pdfmetrics.getFont('ChineseFont')
        font_name = 'ChineseFont'
    except:
        font_name = 'Helvetica'
        logger.warning("[FontSetup] Chinese font not available, using Helvetica")

    chinese_styles = {
        'Title': ParagraphStyle(
            'ChineseTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=24,
            textColor='#1f4788',
            alignment=TA_CENTER,
            spaceAfter=30
        ),
        'Heading1': ParagraphStyle(
            'ChineseHeading1',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            textColor='#2c5aa0',
            spaceAfter=12,
            spaceBefore=12
        ),
        'Heading2': ParagraphStyle(
            'ChineseHeading2',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            textColor='#4a7cb8',
            spaceAfter=10,
            spaceBefore=10
        ),
        'Body': ParagraphStyle(
            'ChineseBody',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            leading=16,
            spaceAfter=8
        ),
        'Caption': ParagraphStyle(
            'ChineseCaption',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=9,
            textColor='#666666',
            alignment=TA_CENTER,
            spaceAfter=6
        ),
        'Footer': ParagraphStyle(
            'ChineseFooter',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=8,
            textColor='#999999',
            alignment=TA_CENTER
        )
    }

    return chinese_styles


def get_disclaimer_text():
    """Get Chinese disclaimer text for reports.

    Returns:
        str: Disclaimer text in Chinese
    """
    return """
    免责声明：本报告仅供参考，不构成投资建议。
    历史回测结果不代表未来表现。投资有风险，入市需谨慎。
    请在专业顾问指导下做出投资决策。
    """
