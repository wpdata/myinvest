"""
Chinese Localization Module for MyInvest V0.3
Constitution Principle I enforcement: Chinese-first interface
"""

import json
import os
from typing import Dict, Any

# Global translation dictionary
_translations: Dict[str, Any] = {}


def load_translations(locale: str = 'zh_CN') -> None:
    """Load translation dictionary from JSON file."""
    global _translations

    locale_file = os.path.join(
        os.path.dirname(__file__),
        f'{locale}.json'
    )

    if os.path.exists(locale_file):
        with open(locale_file, 'r', encoding='utf-8') as f:
            _translations = json.load(f)
    else:
        raise FileNotFoundError(f'Translation file not found: {locale_file}')


def _(key: str, **kwargs) -> str:
    """
    Translation helper function (gettext-style).

    Usage:
        from investapp.locales import _

        # Simple translation
        title = _("watchlist.title")  # -> "监视列表管理"

        # With placeholders
        msg = _("watchlist.messages.symbol_added", symbol="600519")

    Args:
        key: Translation key in dot notation (e.g., "watchlist.title")
        **kwargs: Placeholder values for string formatting

    Returns:
        Translated string in Chinese
    """
    keys = key.split('.')
    value = _translations

    try:
        for k in keys:
            value = value[k]

        # Handle string formatting if placeholders provided
        if kwargs and isinstance(value, str):
            return value.format(**kwargs)

        return str(value)
    except (KeyError, TypeError):
        # Return key itself if translation not found (for debugging)
        return f'[{key}]'


# Initialize translations on import
try:
    load_translations('zh_CN')
except FileNotFoundError:
    print('Warning: Chinese translation file not found. Using fallback keys.')
    _translations = {}


__all__ = ['_', 'load_translations']
