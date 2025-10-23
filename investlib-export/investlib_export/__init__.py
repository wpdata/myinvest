"""
MyInvest V0.3 - Report Export Library
Professional backtest report generation in PDF/Excel/Word formats with Chinese support.
"""

__version__ = "0.3.0"

from investlib_export.pdf_generator import PDFReportGenerator
from investlib_export.excel_generator import ExcelReportGenerator
from investlib_export.word_generator import WordReportGenerator
from investlib_export.font_setup import setup_chinese_fonts

# Initialize Chinese fonts on import
setup_chinese_fonts()

__all__ = [
    "PDFReportGenerator",
    "ExcelReportGenerator",
    "WordReportGenerator",
    "setup_chinese_fonts"
]
