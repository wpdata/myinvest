"""Kroll风险控制策略 - 60日均线+RSI+波动率管理。

这是一个保守的、风险优先的策略，强调资金安全和风险控制。
策略名称来源于风险管理专家Stanley Kroll的投资理念。

核心特点：
- 更短的均线周期（60日 vs 120日），反应更灵敏
- RSI过滤避免追高（RSI < 70）
- 动态仓位管理（根据波动率调整）
- 更紧的止损（2.5% vs 3.5%）
- 更保守的止盈（5% vs 7%）

V0.2: 使用真实市场数据通过MarketDataFetcher
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from investlib_data.market_api import MarketDataFetcher, NoDataAvailableError
from investlib_quant.indicators import calculate_rsi, calculate_atr, calculate_ma


class KrollStrategy:
    """Kroll risk-focused strategy analyzer with real data integration."""

    def __init__(
        self,
        ma_period: int = 60,
        volume_period: int = 20,
        rsi_period: int = 14,
        atr_period: int = 14,
        volume_threshold: float = 1.5,
        rsi_overbought: int = 70,
        rsi_high_confidence: int = 60,
        stop_loss_pct: float = 2.5,
        take_profit_pct: float = 5.0,
        base_position_pct: float = 12.0,
        reduced_position_pct: float = 8.0,
        high_volatility_threshold: float = 3.0,
        position_size_pct: float = None  # 兼容参数优化器
    ):
        """Initialize Kroll strategy parameters.

        Args:
            ma_period: Moving average period (default 60 days)
            volume_period: Volume average period (default 20 days)
            rsi_period: RSI period (default 14)
            atr_period: ATR period (default 14)
            volume_threshold: Volume multiplier for signal (default 1.5x)
            rsi_overbought: RSI threshold for overbought (default 70)
            rsi_high_confidence: RSI threshold for high confidence (default 60)
            stop_loss_pct: Stop-loss percentage (default 2.5%)
            take_profit_pct: Take-profit percentage (default 5.0%)
            base_position_pct: Base position size (default 12%)
            reduced_position_pct: Reduced position for high volatility (default 8%)
            high_volatility_threshold: ATR% threshold for high volatility (default 3%)
            position_size_pct: Alias for base_position_pct (for optimizer compatibility)
        """
        # 支持 position_size_pct 别名（用于参数优化器）
        if position_size_pct is not None:
            base_position_pct = position_size_pct
            reduced_position_pct = position_size_pct * 0.67  # 降低到67%

        self.ma_period = ma_period
        self.volume_period = volume_period
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.volume_threshold = volume_threshold
        self.rsi_overbought = rsi_overbought
        self.rsi_high_confidence = rsi_high_confidence
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.base_position_pct = base_position_pct
        self.reduced_position_pct = reduced_position_pct
        self.high_volatility_threshold = high_volatility_threshold
        self.position_size_pct = base_position_pct  # 保存用于输出
        self.logger = logging.getLogger(__name__)

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for Kroll strategy.

        Args:
            data: DataFrame with OHLCV columns

        Returns:
            DataFrame with added indicator columns
        """
        df = data.copy()

        # MA60
        df['ma_60'] = calculate_ma(df, period=self.ma_period)

        # RSI
        df['rsi'] = calculate_rsi(df, period=self.rsi_period)

        # ATR
        df['atr'] = calculate_atr(df, period=self.atr_period)

        # Volume average and ratio
        df['volume_ma'] = df['volume'].rolling(window=self.volume_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # ATR as percentage of price (for volatility check)
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        return df

    def detect_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect Kroll trading signal from indicators.

        Args:
            df: DataFrame with calculated indicators

        Returns:
            Signal dictionary with action, confidence, and factors
        """
        # Use latest data point
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest

        # Initialize signal
        action = 'HOLD'
        confidence = 'LOW'
        key_factors = []

        # Get current values
        price = latest['close']
        ma60 = latest['ma_60']
        rsi = latest['rsi']
        volume_ratio = latest['volume_ratio']
        atr = latest['atr']
        atr_pct = latest['atr_pct']

        # Check for bullish breakout: Price > MA60
        price_above_ma = price > ma60
        if price_above_ma:
            key_factors.append(f"Price ({price:.2f}) above MA60 ({ma60:.2f})")

        # Check for volume surge
        volume_surge = volume_ratio > self.volume_threshold
        if volume_surge:
            key_factors.append(f"Volume surge: {volume_ratio:.2f}x average")

        # Check RSI (not overbought)
        rsi_ok = rsi < self.rsi_overbought
        if not rsi_ok:
            key_factors.append(f"OVERBOUGHT: RSI={rsi:.1f} > {self.rsi_overbought}")

        # Determine action and confidence
        if price_above_ma and volume_surge and rsi_ok:
            action = 'BUY'
            # Confidence based on RSI
            if rsi < self.rsi_high_confidence:
                confidence = 'HIGH'
                key_factors.append(f"High confidence: RSI={rsi:.1f} < {self.rsi_high_confidence}")
            else:
                confidence = 'MEDIUM'
                key_factors.append(f"Medium confidence: RSI={rsi:.1f} in [{self.rsi_high_confidence}, {self.rsi_overbought})")
        elif not rsi_ok:
            action = 'HOLD'
            confidence = 'LOW'
            key_factors.append("Holding: Market overbought")
        else:
            action = 'HOLD'
            confidence = 'LOW'
            key_factors.append("No strong entry signal detected")

        # Determine position size based on volatility
        position_size = self.base_position_pct
        if atr_pct > self.high_volatility_threshold:
            position_size = self.reduced_position_pct
            key_factors.append(f"High volatility (ATR={atr_pct:.2f}%) → reduced position to {position_size}%")

        return {
            'action': action,
            'confidence': confidence,
            'key_factors': key_factors,
            'entry_price': price,
            'rsi': rsi,
            'atr': atr,
            'atr_pct': atr_pct,
            'position_size_pct': position_size
        }

    def calculate_risk_metrics(
        self,
        signal_data: Dict[str, Any],
        capital: float = 100000.0
    ) -> Dict[str, Any]:
        """Calculate risk metrics (stop-loss, take-profit, max loss).

        Args:
            signal_data: Signal dictionary from detect_signal()
            capital: Total capital available

        Returns:
            Risk metrics dictionary
        """
        # 确保价格和仓位大小是数值类型
        entry_price = float(signal_data['entry_price'])
        position_size_pct = float(signal_data['position_size_pct'])

        # Calculate stop-loss and take-profit (Kroll: tighter stops, conservative targets)
        stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
        take_profit = entry_price * (1 + self.take_profit_pct / 100)

        # Calculate max loss
        position_value = capital * (position_size_pct / 100)
        price_risk = entry_price - stop_loss
        max_loss_amount = position_value * (price_risk / entry_price)
        max_loss_pct = (max_loss_amount / capital) * 100

        # Determine risk level
        if max_loss_pct < 1.5:
            risk_level = 'LOW'
        elif max_loss_pct < 3.0:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'

        return {
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'position_size_pct': round(position_size_pct, 2),
            'max_loss_amount': round(max_loss_amount, 2),
            'max_loss_pct': round(max_loss_pct, 3),
            'risk_level': risk_level
        }

    def analyze_data(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        capital: float = 100000.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze provided market data without fetching from API.

        This method is used by backtesting to avoid redundant API calls.

        Args:
            market_data: DataFrame with OHLCV data
            symbol: Stock symbol (for logging/output)
            capital: Total capital available (default: 100000)
            metadata: Optional metadata dict (for data provenance tracking)

        Returns:
            Complete signal dictionary with action, risk metrics, and data metadata

        Raises:
            ValueError: If insufficient data or missing required columns
        """
        # Use default metadata if not provided
        if metadata is None:
            metadata = {
                'api_source': 'Direct Data',
                'retrieval_timestamp': datetime.now(),
                'data_freshness': 'unknown'
            }

        # Validate input data
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in market_data.columns:
                raise ValueError(f"Missing required column: {col}")

        # Require minimum data points
        min_required = max(self.ma_period, self.rsi_period, self.atr_period) + 1
        if len(market_data) < min_required:
            raise ValueError(
                f"Insufficient data for {symbol}: need at least {min_required} days, "
                f"got {len(market_data)} days."
            )

        # Calculate indicators
        df = self.calculate_indicators(market_data)

        # Detect signal
        signal_data = self.detect_signal(df)

        # Calculate risk metrics
        risk_metrics = self.calculate_risk_metrics(signal_data, capital)

        # Combine into complete signal with metadata
        complete_signal = {
            'symbol': symbol,
            'strategy': 'Kroll',
            'action': signal_data['action'],
            'confidence': signal_data['confidence'],
            'key_factors': signal_data['key_factors'],
            **risk_metrics,
            # Technical indicators
            'rsi': round(signal_data['rsi'], 2),
            'atr': round(signal_data['atr'], 2),
            'atr_pct': round(signal_data['atr_pct'], 2),
            # Data metadata
            'data_source': metadata.get('api_source', 'Unknown'),
            'data_timestamp': metadata['retrieval_timestamp'].isoformat() if isinstance(metadata.get('retrieval_timestamp'), datetime) else str(metadata.get('retrieval_timestamp', 'Unknown')),
            'data_freshness': metadata.get('data_freshness', 'unknown'),
            'data_points': len(market_data),
            'analysis_timestamp': datetime.now().isoformat()
        }

        return complete_signal

    def analyze(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        capital: float = 100000.0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Analyze market data and generate Kroll trading signal using real market data.

        Args:
            symbol: Stock symbol (e.g., '600519.SH' or '600519')
            start_date: Start date in YYYY-MM-DD format (default: auto-calculated)
            end_date: End date in YYYY-MM-DD format (default: today)
            capital: Total capital available (default: 100000)
            use_cache: Whether to use cached data (default: True)

        Returns:
            Complete signal dictionary with action, risk metrics, data metadata

        Raises:
            ValueError: If insufficient data for analysis
            NoDataAvailableError: If all data sources fail
        """
        # Set default date range (need enough for MA60 + RSI/ATR)
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            # Need ~1.5x trading days for MA60 + buffer
            days_needed = int(self.ma_period * 1.5 + 30)  # 60 * 1.5 + 30 = 120 days
            start_date = (datetime.now() - timedelta(days=days_needed)).strftime('%Y-%m-%d')

        # Fetch real data
        from investlib_data.cache_manager import CacheManager
        from investlib_data.database import SessionLocal

        cache_manager = None
        session = None
        if use_cache:
            try:
                session = SessionLocal()
                cache_manager = CacheManager(session=session)
            except Exception as e:
                self.logger.warning(f"Cache not available: {e}")

        fetcher = MarketDataFetcher(cache_manager=cache_manager)

        self.logger.info(f"[KrollStrategy] Fetching data for {symbol} from {start_date} to {end_date}")

        try:
            try:
                result = fetcher.fetch_with_fallback(symbol, start_date, end_date)
            except NoDataAvailableError as e:
                self.logger.error(f"[KrollStrategy] Failed to fetch data for {symbol}: {e}")
                raise

            market_data = result['data']
            metadata = result['metadata']

            # Log data provenance
            self.logger.info(
                f"[KrollStrategy] Analyzing {symbol} with data from {metadata['api_source']}, "
                f"retrieved at {metadata['retrieval_timestamp']}, freshness={metadata['data_freshness']}"
            )

            # Validate input data
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in market_data.columns:
                    raise ValueError(f"Missing required column: {col}")

            # Require minimum data points
            min_required = max(self.ma_period, self.rsi_period, self.atr_period) + 1
            if len(market_data) < min_required:
                raise ValueError(
                    f"Insufficient data for {symbol}: need at least {min_required} days, "
                    f"got {len(market_data)} days. Try extending date range."
                )

            # Calculate indicators
            df = self.calculate_indicators(market_data)

            # Detect signal
            signal_data = self.detect_signal(df)

            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(signal_data, capital)

            # Combine into complete signal with metadata
            complete_signal = {
                'symbol': symbol,
                'strategy': 'Kroll',
                'action': signal_data['action'],
                'confidence': signal_data['confidence'],
                'key_factors': signal_data['key_factors'],
                **risk_metrics,
                # Technical indicators
                'rsi': round(signal_data['rsi'], 2),
                'atr': round(signal_data['atr'], 2),
                'atr_pct': round(signal_data['atr_pct'], 2),
                # Data metadata
                'data_source': metadata['api_source'],
                'data_timestamp': metadata['retrieval_timestamp'].isoformat() if isinstance(metadata['retrieval_timestamp'], datetime) else str(metadata['retrieval_timestamp']),
                'data_freshness': metadata['data_freshness'],
                'data_points': len(market_data),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return complete_signal
        finally:
            # CRITICAL: Close database session to prevent connection leaks
            if session:
                session.close()
                self.logger.debug("[KrollStrategy] Database session closed")


# 注册策略到策略中心
def register_strategy():
    """注册Kroll策略到策略注册中心。"""
    try:
        # 延迟导入，避免循环依赖
        import sys
        import os
        # 添加 src 目录到路径
        src_path = os.path.join(os.path.dirname(__file__), '../src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        from investlib_quant.strategies.registry import StrategyRegistry, StrategyInfo

        strategy_info = StrategyInfo(
            name="ma60_rsi_volatility",
            display_name="Kroll风险控制策略",
            description="60日均线+RSI过滤+动态仓位管理，强调风险控制和资金安全的保守型策略",

            logic="价格突破MA60 + 成交量>1.5倍 + RSI<70 → 买入。根据ATR动态调整仓位（高波动降低仓位）",

            parameters={
                "ma_period": {
                    "default": 60,
                    "description": "均线周期（日），比Livermore更短，反应更灵敏"
                },
                "volume_threshold": {
                    "default": 1.5,
                    "description": "成交量放大倍数，要求更高"
                },
                "rsi_period": {
                    "default": 14,
                    "description": "RSI计算周期"
                },
                "rsi_overbought": {
                    "default": 70,
                    "description": "RSI超买阈值，避免追高"
                },
                "stop_loss_pct": {
                    "default": 2.5,
                    "description": "止损百分比，更紧的保护"
                },
                "take_profit_pct": {
                    "default": 5.0,
                    "description": "止盈百分比，更保守的目标"
                },
                "base_position_pct": {
                    "default": 12.0,
                    "description": "基础仓位百分比"
                },
                "reduced_position_pct": {
                    "default": 8.0,
                    "description": "高波动时降低的仓位"
                },
                "high_volatility_threshold": {
                    "default": 3.0,
                    "description": "高波动阈值（ATR%）"
                }
            },

            tags=["风险控制", "均线突破", "RSI过滤", "动态仓位", "保守型"],
            risk_level="LOW",
            suitable_for=["震荡市", "风险厌恶投资者", "波动较大的市场"],

            strategy_class=KrollStrategy,

            example_code="""
from investlib_quant.kroll_strategy import KrollStrategy

# 创建策略实例（使用默认参数）
strategy = KrollStrategy()

# 分析股票并生成信号
signal = strategy.analyze(
    symbol='600519',  # 贵州茅台
    start_date='2023-01-01',
    end_date='2024-01-01',
    capital=100000.0
)

print(f"策略: {signal['strategy']}")
print(f"信号: {signal['action']}")
print(f"置信度: {signal['confidence']}")
print(f"风险等级: {signal['risk_level']}")
print(f"仓位大小: {signal['position_size_pct']}%")
print(f"\\n关键因素:")
for factor in signal['key_factors']:
    print(f"  - {factor}")
""".strip(),

            typical_holding_period="数周",
            trade_frequency="MEDIUM"
        )

        StrategyRegistry.register(strategy_info)
    except ImportError:
        # 如果注册中心还未创建，静默失败
        pass


# 模块加载时尝试注册
register_strategy()
