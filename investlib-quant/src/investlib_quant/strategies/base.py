"""Base strategy class."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd


class BaseStrategy(ABC):
    """策略基类，所有策略必须继承此类。"""

    def __init__(self, name: str):
        """初始化策略。

        Args:
            name: 策略名称
        """
        self.name = name

    @abstractmethod
    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """生成交易信号（抽象方法）。

        Args:
            market_data: 市场数据 DataFrame，必须包含列:
                - timestamp: 日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量

        Returns:
            信号字典或 None（如果无信号）:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "entry_price": float,
                "stop_loss": float,
                "take_profit": float,
                "position_size_pct": float,
                "confidence": "HIGH" | "MEDIUM" | "LOW",
                "reasoning": dict  # 策略推理细节
            }
        """
        pass

    def analyze_data(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        capital: float,
        metadata: Dict
    ) -> Optional[Dict]:
        """Analyze market data and generate trading signal (for backtest compatibility).

        This method wraps generate_signal() to provide compatibility with the backtest engine.

        Args:
            market_data: Market data DataFrame
            symbol: Symbol being analyzed
            capital: Available capital
            metadata: Data metadata (api_source, retrieval_timestamp, etc.)

        Returns:
            Signal dictionary or None
        """
        # Call the strategy's generate_signal method
        signal = self.generate_signal(market_data)

        # If no signal or HOLD, return None to skip trading
        if not signal or signal.get('action') == 'HOLD':
            return None

        # Return signal for BUY/SELL actions
        return signal

    def validate_data(self, df: pd.DataFrame, required_rows: int = 1) -> bool:
        """验证数据完整性。

        Args:
            df: 数据 DataFrame
            required_rows: 最小行数要求

        Returns:
            True if valid, False otherwise
        """
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        if df is None or df.empty:
            return False

        if len(df) < required_rows:
            return False

        for col in required_cols:
            if col not in df.columns:
                return False

        return True
