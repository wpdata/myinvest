"""120日均线突破策略（MA Breakout Strategy）。

这是一个经典的趋势跟随策略，通过长期均线突破捕捉中长期趋势。
策略名称来源于传奇交易员Jesse Livermore的交易哲学。
"""

from typing import Dict, Optional
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from .base import BaseStrategy


class LivermoreStrategy(BaseStrategy):
    """120日均线突破+成交量确认策略。

    策略别名：Livermore趋势跟随策略
    策略类型：趋势跟随、技术分析

    核心逻辑：
    1. 【买入触发】价格突破120日均线（前一日低于均线，当日突破）
    2. 【信号确认】成交量放大至20日平均的1.3倍以上
    3. 【止损保护】入场价 -3.5%
    4. 【止盈目标】入场价 +7%（风险回报比约2:1）
    5. 【仓位管理】建议15%仓位（根据市场环境可调整）

    适用场景：
    - 中长期趋势明确的市场
    - 适合股票、ETF等流动性好的品种
    - 牛市或震荡上行行情

    参数说明：
        ma_period: 均线周期，默认120日（约半年），用于识别长期趋势
        volume_threshold: 成交量放大倍数，默认1.3倍，用于确认突破有效性
        stop_loss_pct: 止损百分比，默认3.5%，控制单次交易最大损失
        take_profit_pct: 止盈百分比，默认7%，锁定利润目标

    风险特征：
    - 风险等级：MEDIUM
    - 典型持仓周期：数周至数月
    - 交易频率：LOW（突破信号不常出现）
    - 最大单次亏损：约3.5% * 15%仓位 = 0.525%总资金
    """

    def __init__(
        self,
        ma_period: int = 120,
        volume_threshold: float = 1.3,
        stop_loss_pct: float = 3.5,
        take_profit_pct: float = 7.0,
        position_size_pct: float = 15.0
    ):
        """初始化 Livermore 策略。"""
        super().__init__(name="Livermore Trend Following")
        self.ma_period = ma_period
        self.volume_threshold = volume_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct
        self.logger = logging.getLogger(__name__)

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
        # 卖出条件：价格跌破 120 日均线（前一日高于，今日低于）
        ma_breakdown = (prev['close'] > prev['ma_120']) and (current_price < ma_120)

        # 买入条件1：价格突破 120 日均线（前一日低于，今日高于）
        ma_breakout = (prev['close'] < prev['ma_120']) and (current_price > ma_120)

        # 买入条件2：成交量放大
        volume_surge = volume_ratio > self.volume_threshold

        # 生成卖出信号
        if ma_breakdown:
            return {
                "action": "SELL",
                "exit_price": round(current_price, 2),
                "confidence": "HIGH",
                "reasoning": {
                    "strategy": "Livermore Trend Following",
                    "ma_breakdown": True,
                    "current_price": round(current_price, 2),
                    "ma_120": round(ma_120, 2),
                    "breakdown_percentage": round((ma_120 - current_price) / ma_120 * 100, 2),
                    "reason": "价格跌破120日均线，趋势转弱"
                }
            }

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
                "position_size_pct": self.position_size_pct,  # 使用配置的仓位
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

    def analyze(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        capital: float = 100000.0,
        use_cache: bool = True
    ) -> Dict:
        """分析市场数据并生成交易信号（使用真实市场数据）。

        Args:
            symbol: 股票代码（例如 '600519.SH' 或 '600519'）
            start_date: 开始日期 YYYY-MM-DD 格式（默认：自动计算）
            end_date: 结束日期 YYYY-MM-DD 格式（默认：今天）
            capital: 可用资金（默认：100000）
            use_cache: 是否使用缓存数据（默认：True）

        Returns:
            包含信号、风险指标和数据元信息的完整字典

        Raises:
            ValueError: 如果数据不足以进行分析
            NoDataAvailableError: 如果所有数据源都失败
        """
        from investlib_data.market_api import MarketDataFetcher, NoDataAvailableError
        from investlib_data.cache_manager import CacheManager
        from investlib_data.database import SessionLocal

        # 设置默认日期范围（需要足够数据计算 MA120）
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            # 需要约 1.5 倍交易日用于 MA120 + 缓冲
            days_needed = int(self.ma_period * 1.5 + 30)  # 120 * 1.5 + 30 = 210 天
            start_date = (datetime.now() - timedelta(days=days_needed)).strftime('%Y-%m-%d')

        # 获取真实数据
        cache_manager = None
        session = None
        if use_cache:
            try:
                session = SessionLocal()
                cache_manager = CacheManager(session=session)
            except Exception as e:
                self.logger.warning(f"缓存不可用: {e}")

        fetcher = MarketDataFetcher(cache_manager=cache_manager)

        self.logger.info(f"[LivermoreStrategy] 获取 {symbol} 从 {start_date} 到 {end_date} 的数据")

        try:
            try:
                result = fetcher.fetch_with_fallback(symbol, start_date, end_date)
            except NoDataAvailableError as e:
                self.logger.error(f"[LivermoreStrategy] 获取 {symbol} 数据失败: {e}")
                raise

            market_data = result['data']
            metadata = result['metadata']

            # 记录数据来源
            self.logger.info(
                f"[LivermoreStrategy] 正在分析 {symbol}，数据来自 {metadata['api_source']}，"
                f"获取时间 {metadata['retrieval_timestamp']}，数据新鲜度={metadata['data_freshness']}"
            )

            # 生成信号
            signal = self.generate_signal(market_data)

            # 如果没有信号或是 HOLD，返回基本信息
            if not signal or signal.get('action') == 'HOLD':
                return {
                    'symbol': symbol,
                    'strategy': 'Livermore Trend Following',
                    'action': 'HOLD',
                    'confidence': 'N/A',
                    'key_factors': ['当前无明确信号'],
                    'entry_price': 0,
                    'stop_loss': 0,
                    'take_profit': 0,
                    'position_size_pct': 0,
                    'data_source': metadata['api_source'],
                    'data_timestamp': metadata['retrieval_timestamp'].isoformat() if isinstance(metadata['retrieval_timestamp'], datetime) else str(metadata['retrieval_timestamp']),
                    'data_freshness': metadata['data_freshness'],
                    'data_points': len(market_data),
                    'analysis_timestamp': datetime.now().isoformat()
                }

            # 添加额外的元信息到信号
            reasoning = signal.get('reasoning', {})
            key_factors = []

            if reasoning.get('ma_breakout'):
                key_factors.append(f"价格突破120日均线（当前价: ¥{reasoning.get('current_price', 0):.2f}, MA120: ¥{reasoning.get('ma_120', 0):.2f}）")

            if reasoning.get('volume_surge'):
                key_factors.append(f"成交量放大 {reasoning.get('volume_ratio', 0):.2f} 倍")

            if reasoning.get('risk_reward_ratio'):
                key_factors.append(f"风险回报比 1:{reasoning.get('risk_reward_ratio', 0):.2f}")

            complete_signal = {
                'symbol': symbol,
                'strategy': 'Livermore Trend Following',
                'action': signal['action'],
                'confidence': signal['confidence'],
                'key_factors': key_factors,
                'entry_price': signal['entry_price'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'position_size_pct': signal['position_size_pct'],
                # 数据元信息
                'data_source': metadata['api_source'],
                'data_timestamp': metadata['retrieval_timestamp'].isoformat() if isinstance(metadata['retrieval_timestamp'], datetime) else str(metadata['retrieval_timestamp']),
                'data_freshness': metadata['data_freshness'],
                'data_points': len(market_data),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return complete_signal

        finally:
            # 关键：关闭数据库会话以防止连接泄漏
            if session:
                session.close()
                self.logger.debug("[LivermoreStrategy] 数据库会话已关闭")


# 注册策略到策略中心
def register_strategy():
    """注册Livermore策略到策略注册中心。"""
    from .registry import StrategyRegistry, StrategyInfo

    strategy_info = StrategyInfo(
        name="ma_breakout_120",
        display_name="120日均线突破策略",
        description="通过120日均线突破+成交量确认捕捉中长期趋势，适合牛市和震荡上行行情",

        logic="价格突破120日均线 + 成交量放大1.3倍 → 买入信号。严格止损-3.5%，目标止盈+7%",

        parameters={
            "ma_period": {
                "default": 120,
                "description": "均线周期（日）"
            },
            "volume_threshold": {
                "default": 1.3,
                "description": "成交量放大倍数"
            },
            "stop_loss_pct": {
                "default": 3.5,
                "description": "止损百分比"
            },
            "take_profit_pct": {
                "default": 7.0,
                "description": "止盈百分比"
            },
            "position_size_pct": {
                "default": 15.0,
                "description": "仓位百分比"
            }
        },

        tags=["趋势跟随", "均线突破", "技术分析", "中长期"],
        risk_level="MEDIUM",
        suitable_for=["牛市", "震荡上行", "流动性好的股票/ETF"],

        strategy_class=LivermoreStrategy,

        example_code="""
from investlib_quant.strategies.livermore import LivermoreStrategy

# 创建策略实例（使用默认参数）
strategy = LivermoreStrategy()

# 或自定义参数
strategy = LivermoreStrategy(
    ma_period=100,      # 修改为100日均线
    volume_threshold=1.5,  # 提高成交量要求
    stop_loss_pct=3.0,     # 更紧的止损
    take_profit_pct=10.0   # 更高的目标
)

# 生成交易信号
signal = strategy.generate_signal(market_data)
print(f"信号: {signal['action']}, 置信度: {signal.get('confidence', 'N/A')}")
""".strip(),

        typical_holding_period="数周至数月",
        trade_frequency="LOW"
    )

    StrategyRegistry.register(strategy_info)


# 模块加载时自动注册
register_strategy()
