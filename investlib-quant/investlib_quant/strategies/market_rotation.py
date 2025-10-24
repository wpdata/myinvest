"""市场轮动策略 - 大盘下跌触发的多品种轮动。

这是一个防御性的多品种轮动策略，在市场恐慌时买入中证1000 ETF，
其余时间持有国债ETF获取稳定收益。

策略理念：
- 市场恐慌时往往是买入机会（逆向投资）
- 中证1000代表中小盘，弹性更大
- 国债ETF提供稳定现金流和避险功能
"""

from typing import Dict, Optional, List
import pandas as pd
from datetime import datetime, timedelta
from .base import BaseStrategy


class MarketRotationStrategy(BaseStrategy):
    """大盘下跌触发的市场轮动策略。

    策略类型：多品种轮动、逆向投资、防御性策略

    核心逻辑：
    1. 【买入触发】监控大盘指数（如上证指数、沪深300）
       - 当大盘连续2个交易日跌幅都 <= -1.5% 时触发
    2. 【买入标的】全仓买入中证1000 ETF（代码：512100.SH 或 159845.SZ）
    3. 【持仓管理】持有20个交易日后自动卖出
    4. 【默认持仓】其余时间持有国债ETF（如：511010.SH 国债ETF）

    策略优势：
    - 捕捉市场恐慌时的超卖机会
    - 中证1000弹性大，反弹力度强
    - 国债ETF提供稳定收益和流动性
    - 固定持仓期，避免情绪化操作

    风险特征：
    - 风险等级：MEDIUM
    - 典型持仓周期：20个交易日（约1个月）
    - 交易频率：LOW（触发条件较严格）
    - 最大回撤：取决于中证1000走势，建议设置止损

    参数说明：
        index_symbol: 大盘指数代码（默认'000300.SH'沪深300）
        decline_threshold: 单日跌幅阈值（默认-1.5%）
        consecutive_days: 连续下跌天数（默认2天）
        etf_symbol: 买入的ETF代码（默认'159845.SZ'中证1000ETF）
        bond_symbol: 国债ETF代码（默认'511010.SH'国债ETF）
        holding_days: 持有交易日数量（默认20天）
        position_size_pct: 仓位百分比（默认100%全仓）
    """

    def __init__(
        self,
        index_symbol: str = "000300.SH",  # 沪深300
        decline_threshold: float = -1.5,  # 跌幅阈值（百分比）
        consecutive_days: int = 2,  # 连续下跌天数
        etf_symbol: str = "159845.SZ",  # 中证1000ETF
        bond_symbol: str = "511010.SH",  # 国债ETF
        holding_days: int = 20,  # 持有天数
        position_size_pct: float = 100.0,  # 仓位百分比
        stop_loss_pct: Optional[float] = None  # 可选止损
    ):
        """初始化市场轮动策略。"""
        super().__init__(name="Market Rotation Strategy")
        self.index_symbol = index_symbol
        self.decline_threshold = decline_threshold
        self.consecutive_days = consecutive_days
        self.etf_symbol = etf_symbol
        self.bond_symbol = bond_symbol
        self.holding_days = holding_days
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct

        # 持仓状态跟踪（由回测引擎管理）
        self._current_holding = bond_symbol  # 默认持有国债
        self._entry_date = None
        self._entry_price = None

    def generate_signal(
        self,
        market_data: pd.DataFrame,
        index_data: Optional[pd.DataFrame] = None,
        current_position: Optional[str] = None,
        position_entry_date: Optional[str] = None
    ) -> Optional[Dict]:
        """生成交易信号。

        注意：这个策略需要额外的指数数据和持仓状态信息。

        Args:
            market_data: 当前标的市场数据（ETF或国债）
            index_data: 大盘指数数据（必需）
            current_position: 当前持仓品种（None表示空仓或持有国债）
            position_entry_date: 当前持仓的入场日期

        Returns:
            信号字典:
            {
                "action": "BUY" | "SELL" | "HOLD" | "SWITCH",
                "target_symbol": str,  # 目标品种代码
                "from_symbol": str,  # 来源品种代码
                "entry_price": float,
                "position_size_pct": float,
                "reasoning": dict
            }
        """
        # 验证数据
        if index_data is None:
            return {
                "action": "HOLD",
                "reason": "缺少大盘指数数据"
            }

        if not self.validate_data(index_data, required_rows=self.consecutive_days):
            return {
                "action": "HOLD",
                "reason": "指数数据不足"
            }

        # 确保数据按日期排序
        idx_data = index_data.copy().sort_values('timestamp').reset_index(drop=True)

        # 检查当前持仓状态
        current_holding = current_position or self.bond_symbol

        # 情况1: 当前持有中证1000 ETF，检查是否需要卖出
        if current_holding == self.etf_symbol and position_entry_date:
            # 计算持有天数（按交易日计算，不是自然日）
            entry_date = pd.to_datetime(position_entry_date)
            latest_date = pd.to_datetime(idx_data.iloc[-1]['timestamp'])

            # 找到入场日期在数据中的位置，计算已经过了多少个交易日
            # 确保timestamp列是datetime类型
            timestamps = pd.to_datetime(idx_data['timestamp'])
            entry_idx_list = timestamps[timestamps >= entry_date].index
            if len(entry_idx_list) > 0:
                entry_idx = entry_idx_list[0]
                current_idx = len(idx_data) - 1
                holding_period = current_idx - entry_idx  # 交易日数量
            else:
                # 如果找不到入场日期，使用自然日作为fallback
                holding_period = (latest_date - entry_date).days

            # 获取当前价格用于止损检查
            if not market_data.empty:
                current_price = float(market_data.iloc[-1]['close'])
                if self._entry_price and self.stop_loss_pct:
                    loss_pct = (current_price - self._entry_price) / self._entry_price * 100
                    if loss_pct <= -self.stop_loss_pct:
                        return {
                            "action": "SWITCH",
                            "target_symbol": self.bond_symbol,
                            "from_symbol": self.etf_symbol,
                            "entry_price": current_price,
                            "position_size_pct": self.position_size_pct,
                            "reasoning": {
                                "trigger": "止损",
                                "holding_days": holding_period,
                                "loss_pct": round(loss_pct, 2)
                            }
                        }

            # 检查是否达到持仓期限
            if holding_period >= self.holding_days:
                return {
                    "action": "SWITCH",
                    "target_symbol": self.bond_symbol,
                    "from_symbol": self.etf_symbol,
                    "entry_price": float(market_data.iloc[-1]['close']) if not market_data.empty else 0,
                    "position_size_pct": self.position_size_pct,
                    "reasoning": {
                        "trigger": f"持有期满（{self.holding_days}天）",
                        "holding_days": holding_period,
                        "action": "切换回国债ETF"
                    }
                }

            return {"action": "HOLD", "reason": f"持有中证1000 ETF（第{holding_period}天）"}

        # 情况2: 当前持有国债ETF或空仓，检查是否触发买入信号
        # 检查最近N天的跌幅（需要N+1天数据来计算N天的涨跌幅）
        required_days = self.consecutive_days + 1
        if len(idx_data) < required_days:
            return {"action": "HOLD", "reason": "数据不足以判断连续跌幅"}

        recent_days = idx_data.tail(required_days).copy()

        # 计算每日涨跌幅
        recent_days['pct_change'] = recent_days['close'].pct_change() * 100

        # 获取最后N天的涨跌幅（排除第一天，因为它的pct_change是NaN）
        last_n_changes = recent_days['pct_change'].iloc[-self.consecutive_days:]

        # 检查最近N天是否都满足跌幅阈值
        all_decline = all(last_n_changes <= self.decline_threshold)

        if all_decline:
            # 触发买入信号
            latest_data = idx_data.iloc[-1]
            avg_decline = last_n_changes.mean()

            return {
                "action": "SWITCH",
                "target_symbol": self.etf_symbol,
                "from_symbol": current_holding,
                "entry_price": float(market_data.iloc[-1]['close']) if not market_data.empty else 0,
                "position_size_pct": self.position_size_pct,
                "confidence": "HIGH" if avg_decline <= -2.0 else "MEDIUM",
                "reasoning": {
                    "trigger": f"大盘连续{self.consecutive_days}日下跌",
                    "index_symbol": self.index_symbol,
                    "avg_decline": round(avg_decline, 2),
                    "decline_days": last_n_changes.tolist(),
                    "target_holding_days": self.holding_days,
                    "action": f"切换到中证1000 ETF，持有{self.holding_days}个交易日"
                }
            }

        # 无信号，保持当前持仓
        return {
            "action": "HOLD",
            "current_holding": current_holding,
            "reason": "未触发买入条件，保持当前持仓"
        }

    def generate_multi_asset_signal(
        self,
        index_data: pd.DataFrame,
        etf_data: pd.DataFrame,
        bond_data: pd.DataFrame,
        current_position: Optional[str] = None,
        position_entry_date: Optional[str] = None
    ) -> Dict:
        """生成多资产交易信号（推荐使用此方法）。

        Args:
            index_data: 大盘指数历史数据
            etf_data: 中证1000 ETF历史数据
            bond_data: 国债ETF历史数据
            current_position: 当前持仓（None或symbol）
            position_entry_date: 持仓入场日期

        Returns:
            完整的交易信号字典
        """
        # 确定当前应该查看哪个标的的数据
        if current_position == self.etf_symbol:
            market_data = etf_data
        else:
            market_data = bond_data

        return self.generate_signal(
            market_data=market_data,
            index_data=index_data,
            current_position=current_position,
            position_entry_date=position_entry_date
        )


# 注册策略到策略中心
def register_strategy():
    """注册市场轮动策略到策略注册中心。"""
    from .registry import StrategyRegistry, StrategyInfo

    strategy_info = StrategyInfo(
        name="market_rotation_panic_buy",
        display_name="市场轮动策略（大盘恐慌买入）",
        description="监控大盘跌幅，在市场恐慌时买入中证1000 ETF，平时持有国债ETF的多品种轮动策略",

        logic="大盘连续2日跌幅≤-1.5% → 全仓买入中证1000 ETF → 持有20个交易日 → 切换回国债ETF",

        parameters={
            "index_symbol": {
                "default": "000300.SH",
                "description": "监控的大盘指数（沪深300）"
            },
            "decline_threshold": {
                "default": -1.5,
                "description": "单日跌幅阈值（%）"
            },
            "consecutive_days": {
                "default": 2,
                "description": "连续下跌天数"
            },
            "etf_symbol": {
                "default": "159845.SZ",
                "description": "买入的ETF（中证1000）"
            },
            "bond_symbol": {
                "default": "511010.SH",
                "description": "默认持有的国债ETF"
            },
            "holding_days": {
                "default": 20,
                "description": "ETF持有交易日数量"
            },
            "position_size_pct": {
                "default": 100.0,
                "description": "仓位百分比"
            },
            "stop_loss_pct": {
                "default": None,
                "description": "可选止损百分比"
            }
        },

        tags=["多品种轮动", "逆向投资", "防御性", "ETF轮动", "指数监控"],
        risk_level="MEDIUM",
        suitable_for=["震荡市", "熊市", "追求稳健收益", "中长期投资"],

        strategy_class=MarketRotationStrategy,

        example_code="""
from investlib_quant.strategies.market_rotation import MarketRotationStrategy

# 创建策略实例
strategy = MarketRotationStrategy(
    index_symbol='000300.SH',     # 监控沪深300
    decline_threshold=-1.5,        # 跌幅阈值-1.5%
    consecutive_days=2,            # 连续2天
    etf_symbol='159845.SZ',        # 中证1000ETF
    bond_symbol='511010.SH',       # 国债ETF
    holding_days=20,               # 持有20天
    stop_loss_pct=5.0              # 可选5%止损
)

# 生成信号（需要提供多个数据源）
signal = strategy.generate_multi_asset_signal(
    index_data=index_df,      # 大盘指数数据
    etf_data=etf_df,          # 中证1000数据
    bond_data=bond_df,        # 国债ETF数据
    current_position='511010.SH',  # 当前持仓
    position_entry_date='2024-01-15'
)

print(f"信号: {signal['action']}")
if signal['action'] == 'SWITCH':
    print(f"从 {signal['from_symbol']} 切换到 {signal['target_symbol']}")
    print(f"原因: {signal['reasoning']['trigger']}")
""".strip(),

        typical_holding_period="20个交易日（约1个月）",
        trade_frequency="LOW"
    )

    StrategyRegistry.register(strategy_info)


# 模块加载时自动注册
register_strategy()
