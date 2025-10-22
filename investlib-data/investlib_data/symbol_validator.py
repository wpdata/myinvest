"""股票代码验证工具。

提供股票代码格式验证、类型检测等功能。
"""

from typing import Tuple, Optional


def detect_symbol_type(symbol: str) -> str:
    """检测股票代码的类型。

    Args:
        symbol: 股票代码（如 600519.SH, 510300.SH）

    Returns:
        类型标识: 'stock', 'etf', 'index', 'unknown'
    """
    # 去除后缀，提取代码
    code = symbol.split('.')[0]

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
        symbol: 股票代码

    Returns:
        (is_valid, error_message): 是否有效，错误消息（如果有）
    """
    # 基本格式检查
    if not symbol or not isinstance(symbol, str):
        return False, "股票代码不能为空"

    if '.' not in symbol:
        return False, "股票代码格式错误，应包含交易所后缀（如 .SH 或 .SZ）"

    code, exchange = symbol.rsplit('.', 1)

    # 交易所检查
    if exchange not in ['SH', 'SZ']:
        return False, f"不支持的交易所: {exchange}。当前仅支持上海（.SH）和深圳（.SZ）"

    # 代码长度检查
    if not code.isdigit():
        return False, "股票代码应为纯数字"

    if len(code) != 6:
        return False, f"股票代码长度应为 6 位，当前为 {len(code)} 位"

    # 类型检查
    symbol_type = detect_symbol_type(symbol)

    if symbol_type == 'unknown':
        return False, f"❌ 无法识别的股票代码类型：{symbol}"

    # 所有类型（股票、ETF、指数）都通过验证
    return True, None


def get_symbol_info(symbol: str) -> dict:
    """获取股票代码的详细信息。

    Args:
        symbol: 股票代码

    Returns:
        包含代码信息的字典
    """
    code, exchange = symbol.split('.')
    symbol_type = detect_symbol_type(symbol)

    type_name_map = {
        'stock': '股票',
        'etf': 'ETF基金',
        'index': '指数',
        'unknown': '未知'
    }

    exchange_name_map = {
        'SH': '上海证券交易所',
        'SZ': '深圳证券交易所'
    }

    return {
        'code': code,
        'exchange': exchange,
        'exchange_name': exchange_name_map.get(exchange, '未知交易所'),
        'type': symbol_type,
        'type_name': type_name_map.get(symbol_type, '未知类型'),
        'supported': symbol_type == 'stock'
    }
