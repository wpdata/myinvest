"""
MyInvest V0.3 - Multi-Asset Data Fetcher Extension (T033)
Adds futures and options support to MarketDataFetcher.
"""

import logging
from typing import Literal


logger = logging.getLogger(__name__)


def detect_asset_type(symbol: str) -> Literal['stock', 'futures', 'option']:
    """Detect asset type from symbol format (T033).

    Args:
        symbol: Symbol string

    Returns:
        'stock', 'futures', or 'option'

    Examples:
        >>> detect_asset_type('600519.SH')
        'stock'
        >>> detect_asset_type('IF2506.CFFEX')
        'futures'
        >>> detect_asset_type('10005102.SH')
        'option'

    Symbol Patterns:
        - Stock: XXXXXX.SH/SZ (6 digits)
        - Futures: LLDDMM.EXCHANGE (letters + digits + exchange)
            - Exchanges: CFFEX, DCE, CZCE, SHFE, INE
        - Option: 10XXXXXX.SH (starts with 10)
    """
    symbol_upper = symbol.upper()

    # Check for futures exchanges
    futures_exchanges = ['.CFFEX', '.DCE', '.CZCE', '.SHFE', '.INE']
    if any(exc in symbol_upper for exc in futures_exchanges):
        return 'futures'

    # Check for options (50ETF options start with 10)
    if symbol_upper.startswith('10') and '.SH' in symbol_upper:
        return 'option'

    # Default to stock
    return 'stock'


def get_asset_display_name(asset_type: str) -> str:
    """Get Chinese display name for asset type.

    Args:
        asset_type: 'stock', 'futures', or 'option'

    Returns:
        Chinese display name
    """
    names = {
        'stock': '股票',
        'futures': '期货',
        'option': '期权'
    }
    return names.get(asset_type, '未知')


def get_asset_badge_emoji(asset_type: str) -> str:
    """Get emoji badge for asset type.

    Args:
        asset_type: 'stock', 'futures', or 'option'

    Returns:
        Emoji string
    """
    emojis = {
        'stock': '📈',
        'futures': '📊',
        'option': '📉'
    }
    return emojis.get(asset_type, '📋')


def validate_futures_symbol(symbol: str) -> bool:
    """Validate futures symbol format.

    Args:
        symbol: Futures symbol (e.g., 'IF2506.CFFEX')

    Returns:
        True if valid format

    Futures Symbol Format:
        - Product code (2-3 letters): IF, IC, IH, etc.
        - Year (2 digits): 25 for 2025
        - Month (2 digits): 06 for June
        - Exchange: CFFEX, DCE, CZCE, SHFE, INE
    """
    if '.' not in symbol:
        return False

    code, exchange = symbol.split('.')

    # Check exchange
    valid_exchanges = ['CFFEX', 'DCE', 'CZCE', 'SHFE', 'INE']
    if exchange.upper() not in valid_exchanges:
        return False

    # Check code format (2-3 letters + 4 digits)
    if len(code) < 6:
        return False

    # Extract product code and date
    # Example: IF2506 -> IF (product), 2506 (date)
    import re
    match = re.match(r'^([A-Z]{1,3})(\d{4})$', code.upper())

    return match is not None


def get_continuous_contract_code(futures_symbol: str) -> str:
    """Get continuous contract code for rollover.

    Args:
        futures_symbol: Specific contract (e.g., 'IF2506.CFFEX')

    Returns:
        Continuous contract code (e.g., 'IF888.CFFEX' or 'IF000.CFFEX')

    Continuous Contract Codes:
        - IF888: Main contract (highest volume)
        - IF000: Nearest contract
        - Used to get continuous price series across rollovers
    """
    if '.' not in futures_symbol:
        return futures_symbol

    code, exchange = futures_symbol.split('.')

    # Extract product code (letters only)
    import re
    match = re.match(r'^([A-Z]+)', code.upper())

    if match:
        product_code = match.group(1)
        # Use 888 for main contract (most common)
        continuous_code = f"{product_code}888.{exchange}"
        return continuous_code

    return futures_symbol


# Example usage and testing
if __name__ == '__main__':
    # Test asset type detection
    test_symbols = [
        '600519.SH',      # Stock
        '000001.SZ',      # Stock
        'IF2506.CFFEX',   # Futures
        'IC2503.CFFEX',   # Futures
        'M2505.DCE',      # Futures
        '10005102.SH',    # Option
    ]

    print("Asset Type Detection:")
    for symbol in test_symbols:
        asset_type = detect_asset_type(symbol)
        display_name = get_asset_display_name(asset_type)
        emoji = get_asset_badge_emoji(asset_type)
        print(f"  {symbol:20} → {emoji} {asset_type:10} ({display_name})")

    print("\nFutures Symbol Validation:")
    futures_symbols = ['IF2506.CFFEX', 'IC2503.CFFEX', 'INVALID.SH']
    for symbol in futures_symbols:
        valid = validate_futures_symbol(symbol)
        status = "✓ Valid" if valid else "✗ Invalid"
        print(f"  {symbol:20} → {status}")

    print("\nContinuous Contract Codes:")
    for symbol in ['IF2506.CFFEX', 'IC2503.CFFEX', 'M2505.DCE']:
        continuous = get_continuous_contract_code(symbol)
        print(f"  {symbol:20} → {continuous}")
