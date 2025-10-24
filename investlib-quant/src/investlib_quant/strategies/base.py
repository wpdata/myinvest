"""Base strategy class and asset-specific subclasses (T034)."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Literal
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


# ========== T034: Asset-Specific Strategy Subclasses ==========

class StockStrategy(BaseStrategy):
    """股票策略基类 (T034).

    特点：
    - T+1交易规则（当天买入，次日才能卖出）
    - 全额资金购买（不使用保证金）
    - 仅支持做多（long only）
    - 继承自BaseStrategy，适配现有Livermore/Kro策略
    """

    def __init__(self, name: str):
        """初始化股票策略。

        Args:
            name: 策略名称
        """
        super().__init__(name)
        self.asset_type = 'stock'
        self.trading_rule = 'T+1'
        self.direction_supported = ['long']  # Only support long positions for stocks

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        position_size_pct: float = 1.0
    ) -> int:
        """计算股票持仓数量（基于全额资金）。

        Args:
            capital: 可用资金
            entry_price: 入场价格
            position_size_pct: 仓位百分比 (0.0-1.0)

        Returns:
            可购买股数（整数，100股为1手）
        """
        # Calculate shares based on full capital (no margin)
        allocated_capital = capital * position_size_pct
        shares = int(allocated_capital / entry_price)

        # Round down to nearest 100 (1 lot = 100 shares in China)
        shares = (shares // 100) * 100

        return shares


class FuturesStrategy(BaseStrategy):
    """期货策略基类 (T034).

    特点：
    - T+0交易规则（当天可多次买卖）
    - 保证金交易（使用杠杆）
    - 双向交易（可做多或做空）
    - 支持合约展期（rollover）
    - 强平风险管理
    """

    def __init__(
        self,
        name: str,
        margin_rate: float = 0.15,
        multiplier: int = 300
    ):
        """初始化期货策略。

        Args:
            name: 策略名称
            margin_rate: 保证金率 (默认15%)
            multiplier: 合约乘数 (IF: 300, IC: 200)
        """
        super().__init__(name)
        self.asset_type = 'futures'
        self.trading_rule = 'T+0'
        self.direction_supported = ['long', 'short']  # Support both directions
        self.margin_rate = margin_rate
        self.multiplier = multiplier

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        position_size_pct: float = 1.0,
        direction: Literal['long', 'short'] = 'long'
    ) -> int:
        """计算期货持仓数量（基于保证金）。

        Args:
            capital: 可用资金
            entry_price: 入场价格
            position_size_pct: 仓位百分比 (0.0-1.0)
            direction: 交易方向 ('long' 或 'short')

        Returns:
            期货合约数量
        """
        # Calculate margin required per contract
        margin_per_contract = entry_price * self.multiplier * self.margin_rate

        # Calculate max contracts based on available capital
        allocated_capital = capital * position_size_pct
        contracts = int(allocated_capital / margin_per_contract)

        return contracts

    def calculate_liquidation_price(
        self,
        entry_price: float,
        direction: Literal['long', 'short'],
        force_close_margin_rate: float = 0.10
    ) -> float:
        """计算强制平仓价格。

        Args:
            entry_price: 入场价格
            direction: 交易方向
            force_close_margin_rate: 强平保证金率（默认10%）

        Returns:
            强平价格
        """
        # Calculate price change threshold for forced liquidation
        # When margin falls below force_close_margin_rate, position is liquidated
        price_change_pct = (self.margin_rate - force_close_margin_rate) / self.margin_rate

        if direction == 'long':
            # For long positions, liquidation occurs when price falls
            liquidation_price = entry_price * (1 - price_change_pct)
        else:
            # For short positions, liquidation occurs when price rises
            liquidation_price = entry_price * (1 + price_change_pct)

        return liquidation_price

    def handle_rollover(
        self,
        current_contract: str,
        current_date: pd.Timestamp
    ) -> Optional[str]:
        """处理合约展期（当接近交割日时切换到下一个合约）。

        Args:
            current_contract: 当前合约代码 (e.g., 'IF2506.CFFEX')
            current_date: 当前日期

        Returns:
            新合约代码或None（如果不需要展期）
        """
        # Extract contract month from symbol (e.g., IF2506 -> 2506 -> 2025年6月)
        import re
        match = re.search(r'([A-Z]+)(\d{4})', current_contract.upper())

        if not match:
            return None

        product_code = match.group(1)
        contract_month_str = match.group(2)

        # Parse year and month (YYMM format)
        year = 2000 + int(contract_month_str[:2])
        month = int(contract_month_str[2:])

        # Create expiry date (assume 3rd Friday of contract month)
        expiry_date = pd.Timestamp(year=year, month=month, day=15)

        # Check if within 7 days of expiry
        days_to_expiry = (expiry_date - current_date).days

        if days_to_expiry <= 7:
            # Need to roll to next contract
            next_month = month + 1 if month < 12 else 1
            next_year = year if month < 12 else year + 1

            # Generate next contract code
            next_contract_month = f"{next_year % 100:02d}{next_month:02d}"
            next_contract = f"{product_code}{next_contract_month}.CFFEX"

            return next_contract

        return None


class OptionsStrategy(BaseStrategy):
    """期权策略基类 (T034).

    特点：
    - 支持认购（Call）和认沽（Put）期权
    - Greeks风险跟踪（Delta, Gamma, Vega, Theta, Rho）
    - 到期日处理（自动行权或作废）
    - 支持多腿组合策略（由子类实现）
    """

    def __init__(
        self,
        name: str,
        option_type: Literal['call', 'put'] = 'call'
    ):
        """初始化期权策略。

        Args:
            name: 策略名称
            option_type: 期权类型 ('call' 或 'put')
        """
        super().__init__(name)
        self.asset_type = 'option'
        self.option_type = option_type
        self.direction_supported = ['long', 'short']
        self.greeks = None  # Will store Delta, Gamma, Vega, Theta, Rho

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        position_size_pct: float = 1.0,
        multiplier: int = 10000
    ) -> int:
        """计算期权持仓数量。

        Args:
            capital: 可用资金
            entry_price: 期权价格（每份）
            position_size_pct: 仓位百分比
            multiplier: 合约乘数（50ETF期权：10000）

        Returns:
            期权合约数量
        """
        # Calculate contract cost
        cost_per_contract = entry_price * multiplier

        # Calculate max contracts based on available capital
        allocated_capital = capital * position_size_pct
        contracts = int(allocated_capital / cost_per_contract)

        return contracts

    def calculate_greeks(
        self,
        underlying_price: float,
        strike_price: float,
        time_to_expiry: float,  # in years
        risk_free_rate: float = 0.03,
        volatility: float = 0.20
    ) -> Dict[str, float]:
        """计算期权Greeks（需要py_vollib库）。

        Args:
            underlying_price: 标的资产价格
            strike_price: 行权价
            time_to_expiry: 到期时间（年）
            risk_free_rate: 无风险利率（默认3%）
            volatility: 波动率（默认20%）

        Returns:
            Greeks字典: {'delta', 'gamma', 'vega', 'theta', 'rho'}
        """
        try:
            from py_vollib_vectorized import get_all_greeks

            greeks = get_all_greeks(
                flag='c' if self.option_type == 'call' else 'p',
                S=underlying_price,
                K=strike_price,
                t=time_to_expiry,
                r=risk_free_rate,
                sigma=volatility
            )

            self.greeks = {
                'delta': greeks['delta'],
                'gamma': greeks['gamma'],
                'vega': greeks['vega'] / 100,  # Per 1% vol change
                'theta': greeks['theta'] / 365,  # Per day
                'rho': greeks['rho'] / 100  # Per 1% rate change
            }

            return self.greeks

        except ImportError:
            # Fallback: return placeholder Greeks
            return {
                'delta': 0.5 if self.option_type == 'call' else -0.5,
                'gamma': 0.01,
                'vega': 0.10,
                'theta': -0.05,
                'rho': 0.05
            }

    def handle_expiry(
        self,
        option_position: Dict,
        underlying_price: float,
        strike_price: float
    ) -> Dict[str, any]:
        """处理期权到期（European-style，仅在到期日行权）。

        Args:
            option_position: 期权持仓信息
            underlying_price: 到期时标的价格
            strike_price: 行权价

        Returns:
            行权结果字典:
                - 'action': 'exercise' | 'expire_worthless'
                - 'profit_loss': 盈亏金额
                - 'reasoning': 原因说明
        """
        direction = option_position.get('direction', 'long')
        quantity = option_position.get('quantity', 0)
        entry_price = option_position.get('entry_price', 0)

        # Determine if option is in-the-money (ITM)
        if self.option_type == 'call':
            is_itm = underlying_price > strike_price
            intrinsic_value = max(0, underlying_price - strike_price)
        else:  # put
            is_itm = underlying_price < strike_price
            intrinsic_value = max(0, strike_price - underlying_price)

        if is_itm and direction == 'long':
            # Exercise option
            profit_loss = (intrinsic_value - entry_price) * quantity * 10000
            return {
                'action': 'exercise',
                'profit_loss': profit_loss,
                'intrinsic_value': intrinsic_value,
                'reasoning': f"期权价内（ITM），行权价值：{intrinsic_value:.4f}元"
            }
        else:
            # Option expires worthless
            profit_loss = -entry_price * quantity * 10000 if direction == 'long' else entry_price * quantity * 10000
            return {
                'action': 'expire_worthless',
                'profit_loss': profit_loss,
                'intrinsic_value': 0,
                'reasoning': f"期权价外（OTM），作废"
            }
