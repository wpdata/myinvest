"""
Chinese Font Configuration for Charts and Reports
Ensures Chinese characters display correctly in matplotlib, ReportLab, and Streamlit
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
import platform
import warnings


def configure_chinese_fonts():
    """
    Configure Chinese fonts for matplotlib based on operating system.

    Font priority order:
    - macOS: PingFang SC > Heiti SC > STHeiti
    - Windows: Microsoft YaHei > SimHei > SimSun
    - Linux: Noto Sans CJK SC > WenQuanYi Micro Hei

    Returns:
        str: Name of the configured Chinese font
    """
    system = platform.system()

    # Font selection by OS
    if system == 'Darwin':  # macOS
        font_candidates = ['PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS']
    elif system == 'Windows':
        font_candidates = ['Microsoft YaHei', 'SimHei', 'SimSun', 'FangSong']
    else:  # Linux
        font_candidates = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Droid Sans Fallback']

    # Find available font
    available_fonts = [f.name for f in font_manager.fontManager.ttflist]
    chinese_font = None

    for font in font_candidates:
        if font in available_fonts:
            chinese_font = font
            break

    if chinese_font:
        # Configure matplotlib to use Chinese font
        plt.rcParams['font.sans-serif'] = [chinese_font] + plt.rcParams['font.sans-serif']
        plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display

        # Suppress DejaVuSans font warning
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

        return chinese_font
    else:
        warnings.warn(
            f'No Chinese font found on {system}. Charts may not display Chinese correctly. '
            f'Please install: {font_candidates[0]}',
            UserWarning
        )
        return None


def get_reportlab_font_config():
    """
    Get ReportLab font configuration for PDF reports.

    Returns:
        dict: Font configuration with font name and path
    """
    system = platform.system()

    font_config = {
        'Darwin': {
            'name': 'PingFangSC',
            'paths': [
                '/System/Library/Fonts/PingFang.ttc',
                '/Library/Fonts/Songti.ttc'
            ]
        },
        'Windows': {
            'name': 'SimSun',
            'paths': [
                'C:\\Windows\\Fonts\\msyh.ttc',  # Microsoft YaHei
                'C:\\Windows\\Fonts\\simsun.ttc'  # SimSun
            ]
        },
        'Linux': {
            'name': 'NotoSansCJK',
            'paths': [
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
            ]
        }
    }

    return font_config.get(system, font_config['Darwin'])


# Auto-configure on module import
CHINESE_FONT = configure_chinese_fonts()

if CHINESE_FONT:
    print(f'✓ Chinese font configured for matplotlib: {CHINESE_FONT}')
else:
    print('⚠ Warning: No Chinese font configured. Charts may not display Chinese correctly.')


__all__ = ['configure_chinese_fonts', 'get_reportlab_font_config', 'CHINESE_FONT']
