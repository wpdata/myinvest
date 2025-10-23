"""股票代码验证工具。

提供股票代码格式验证、类型检测等功能。
支持股票、ETF、指数、期货、期权。
"""

from typing import Tuple, Optional


def detect_symbol_type(symbol: str) -> str:
    """检测股票代码的类型。

    Args:
        symbol: 股票代码（如 600519.SH, IF2506.CFFEX, 10005102.SH）

    Returns:
        类型标识: 'stock', 'etf', 'index', 'futures', 'option', 'unknown'
    """
    symbol_upper = symbol.upper()

    # 检查期货交易所
    futures_exchanges = ['.CFFEX', '.DCE', '.CZCE', '.SHFE', '.INE']
    if any(exc in symbol_upper for exc in futures_exchanges):
        return 'futures'

    # 去除后缀，提取代码
    code = symbol.split('.')[0]

    # 检查期权（50ETF期权以10开头）
    if code.startswith('10') and symbol_upper.endswith('.SH'):
        return 'option'

    # 上海证券交易所（SH）
    if symbol.endswith('.SH'):
        if code.startswith('60'):
            return 'stock'  # 600xxx = 股票
        elif code.startswith('51') or code.startswith('50'):
            return 'etf'    # 50xxxx, 51xxxx = ETF
        elif code.startswith('000'):
            return 'index'  # 000xxx = 指数
        else:
            return 'unknown'

    # 深圳证券交易所（SZ）
    elif symbol.endswith('.SZ'):
        if code.startswith('00'):
            return 'stock'  # 000xxx, 002xxx = 股票
        elif code.startswith('30'):
            return 'stock'  # 300xxx = 创业板股票
        elif code.startswith('15') or code.startswith('16'):
            return 'etf'    # 15xxxx, 16xxxx = ETF
        elif code.startswith('399'):
            return 'index'  # 399xxx = 指数
        else:
            return 'unknown'

    else:
        return 'unknown'


def validate_symbol(symbol: str) -> Tuple[bool, Optional[str]]:
    """验证股票代码是否有效且受支持。

    Args:
        symbol: 股票/期货/期权代码

    Returns:
        (is_valid, error_message): 是否有效，错误消息（如果有）
    """
    # 基本格式检查
    if not symbol or not isinstance(symbol, str):
        return False, "代码不能为空"

    if '.' not in symbol:
        return False, "代码格式错误，应包含交易所后缀（如 .SH, .SZ, .CFFEX）"

    code, exchange = symbol.rsplit('.', 1)
    exchange_upper = exchange.upper()

    # 支持的交易所列表
    supported_exchanges = ['SH', 'SZ', 'CFFEX', 'DCE', 'CZCE', 'SHFE', 'INE']

    if exchange_upper not in supported_exchanges:
        return False, f"不支持的交易所: {exchange}。支持的交易所: {', '.join(supported_exchanges)}"

    # 类型检查
    symbol_type = detect_symbol_type(symbol)

    if symbol_type == 'unknown':
        return False, f"❌ 无法识别的代码类型：{symbol}"

    # 期货和期权的代码格式不同，不做严格长度检查
    if symbol_type in ['stock', 'etf', 'index']:
        # 股票/ETF/指数代码必须是6位数字
        if not code.isdigit():
            return False, "股票/ETF/指数代码应为纯数字"

        if len(code) != 6:
            return False, f"股票/ETF/指数代码长度应为 6 位，当前为 {len(code)} 位"

    # 所有类型（股票、ETF、指数、期货、期权）都通过验证
    return True, None


def get_symbol_info(symbol: str) -> dict:
    """获取代码的详细信息。

    Args:
        symbol: 股票/期货/期权代码

    Returns:
        包含代码信息的字典
    """
    code, exchange = symbol.split('.')
    symbol_type = detect_symbol_type(symbol)

    type_name_map = {
        'stock': '股票',
        'etf': 'ETF基金',
        'index': '指数',
        'futures': '期货',
        'option': '期权',
        'unknown': '未知'
    }

    exchange_name_map = {
        'SH': '上海证券交易所',
        'SZ': '深圳证券交易所',
        'CFFEX': '中国金融期货交易所',
        'DCE': '大连商品交易所',
        'CZCE': '郑州商品交易所',
        'SHFE': '上海期货交易所',
        'INE': '上海国际能源交易中心'
    }

    return {
        'code': code,
        'exchange': exchange.upper(),
        'exchange_name': exchange_name_map.get(exchange.upper(), f'未知交易所 ({exchange})'),
        'type': symbol_type,
        'type_name': type_name_map.get(symbol_type, '未知类型'),
        'supported': symbol_type in ['stock', 'etf', 'index', 'futures', 'option']
    }
