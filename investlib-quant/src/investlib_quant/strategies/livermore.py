"""Livermore trend-following strategy."""

from typing import Dict, Optional
import pandas as pd
import numpy as np
from .base import BaseStrategy


class LivermoreStrategy(BaseStrategy):
    """Livermore 趋势跟随策略。

    核心逻辑：
    1. 价格突破 120 日均线 → 买入信号
    2. 成交量放大 30% 以上 → 确认信号
    3. 止损设置为入场价 -3.5%
    4. 止盈设置为入场价 +7%
    5. 仓位建议 15%（可根据市场环境调整）

    参数：
        ma_period: 均线周期（默认 120 日）
        volume_threshold: 成交量放大倍数（默认 1.3）
        stop_loss_pct: 止损百分比（默认 3.5%）
        take_profit_pct: 止盈百分比（默认 7%）
    """

    def __init__(
        self,
        ma_period: int = 120,
        volume_threshold: float = 1.3,
        stop_loss_pct: float = 3.5,
        take_profit_pct: float = 7.0
    ):
        """初始化 Livermore 策略。"""
        super().__init__(name="Livermore Trend Following")
        self.ma_period = ma_period
        self.volume_threshold = volume_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def generate_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """生成交易信号。

        Args:
            market_data: 市场数据（至少需要 120+ 天数据）

        Returns:
            信号字典或 None
        """
        # 验证数据
        if not self.validate_data(market_data, required_rows=self.ma_period + 1):
            return None

        # 确保数据按日期排序
        df = market_data.copy().sort_values('timestamp').reset_index(drop=True)

        # 计算技术指标
        df['ma_120'] = df['close'].rolling(window=self.ma_period).mean()
        df['volume_ma_20'] = df['volume'].rolling(window=20).mean()

        # 获取最新和前一日数据
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # 检查是否有足够数据
        if pd.isna(latest['ma_120']) or pd.isna(latest['volume_ma_20']):
            return {"action": "HOLD", "reason": "技术指标计算不足"}

        current_price = float(latest['close'])
        ma_120 = float(latest['ma_120'])
        volume_ratio = float(latest['volume'] / latest['volume_ma_20'])

        # 判断信号
        # 条件1：价格突破 120 日均线（前一日低于，今日高于）
        ma_breakout = (prev['close'] < prev['ma_120']) and (current_price > ma_120)

        # 条件2：成交量放大
        volume_surge = volume_ratio > self.volume_threshold

        # 生成买入信号
        if ma_breakout and volume_surge:
            stop_loss = current_price * (1 - self.stop_loss_pct / 100)
            take_profit = current_price * (1 + self.take_profit_pct / 100)

            # 置信度判断：成交量放大越多，置信度越高
            if volume_ratio > 1.5:
                confidence = "HIGH"
            elif volume_ratio > 1.3:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            return {
                "action": "BUY",
                "entry_price": round(current_price, 2),
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
                "position_size_pct": 15,  # 默认建议 15% 仓位
                "confidence": confidence,
                "reasoning": {
                    "strategy": "Livermore Trend Following",
                    "ma_breakout": True,
                    "volume_surge": True,
                    "current_price": round(current_price, 2),
                    "ma_120": round(ma_120, 2),
                    "volume_ratio": round(volume_ratio, 2),
                    "breakout_percentage": round((current_price - ma_120) / ma_120 * 100, 2),
                    "risk_reward_ratio": round(self.take_profit_pct / self.stop_loss_pct, 2)
                }
            }

        # 无信号
        return {"action": "HOLD"}

    def backtest_signal(self, market_data: pd.DataFrame, entry_date: str) -> Dict:
        """回测某个历史日期的信号（用于测试）。

        Args:
            market_data: 历史数据
            entry_date: 入场日期（YYYY-MM-DD）

        Returns:
            信号字典
        """
        # 截取到指定日期的数据
        df = market_data[market_data['timestamp'] <= entry_date].copy()
        return self.generate_signal(df)
