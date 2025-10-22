"""Portfolio state tracker for backtest simulations (T065).

Tracks cash, positions, and portfolio value during backtest execution.
Applies realistic transaction costs (commission + slippage).
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Trade:
    """Record of a single trade execution."""
    timestamp: str
    symbol: str
    action: str  # 'BUY' or 'SELL'
    price: float
    quantity: int
    commission: float
    slippage: float
    total_cost: float
    data_source: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class Portfolio:
    """Portfolio state tracker with transaction cost simulation."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,  # 0.03%
        slippage_rate: float = 0.001       # 0.1%
    ):
        """Initialize portfolio.

        Args:
            initial_capital: Starting cash amount
            commission_rate: Commission as decimal (default 0.0003 = 0.03%)
            slippage_rate: Slippage as decimal (default 0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

        # Positions: {symbol: quantity}
        self.positions: Dict[str, int] = {}

        # Trade log
        self.trades: List[Trade] = []

        # Daily value history: List[(date, portfolio_value)]
        self.value_history: List[tuple] = []

        self.logger = logging.getLogger(__name__)

    def buy(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str = "backtest"
    ) -> bool:
        """Execute buy order with transaction costs.

        Args:
            symbol: Stock symbol
            price: Purchase price per share
            quantity: Number of shares to buy
            timestamp: Execution timestamp
            data_source: Market data source

        Returns:
            True if order executed successfully, False if insufficient funds
        """
        # Calculate costs
        base_cost = price * quantity
        commission = base_cost * self.commission_rate
        slippage = base_cost * self.slippage_rate
        total_cost = base_cost + commission + slippage

        # Check if sufficient funds
        if total_cost > self.cash:
            self.logger.warning(
                f"Insufficient funds for BUY {symbol}: need {total_cost:.2f}, "
                f"have {self.cash:.2f}"
            )
            return False

        # Execute trade
        self.cash -= total_cost
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity

        # Record trade
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            action='BUY',
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            total_cost=total_cost,
            data_source=data_source
        )
        self.trades.append(trade)

        self.logger.info(
            f"BUY {quantity} {symbol} @ {price:.2f} | "
            f"Cost: {total_cost:.2f} (base={base_cost:.2f}, "
            f"comm={commission:.2f}, slip={slippage:.2f}) | "
            f"Cash remaining: {self.cash:.2f}"
        )

        return True

    def sell(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str = "backtest"
    ) -> bool:
        """Execute sell order with transaction costs.

        Args:
            symbol: Stock symbol
            price: Sell price per share
            quantity: Number of shares to sell
            timestamp: Execution timestamp
            data_source: Market data source

        Returns:
            True if order executed successfully, False if insufficient shares
        """
        # Check if sufficient shares
        current_position = self.positions.get(symbol, 0)
        if quantity > current_position:
            self.logger.warning(
                f"Insufficient shares for SELL {symbol}: "
                f"need {quantity}, have {current_position}"
            )
            return False

        # Calculate proceeds (after costs)
        base_proceeds = price * quantity
        commission = base_proceeds * self.commission_rate
        slippage = base_proceeds * self.slippage_rate
        net_proceeds = base_proceeds - commission - slippage

        # Execute trade
        self.cash += net_proceeds
        self.positions[symbol] -= quantity

        # Remove symbol if position closed
        if self.positions[symbol] == 0:
            del self.positions[symbol]

        # Record trade
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            action='SELL',
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            total_cost=-net_proceeds,  # Negative = cash inflow
            data_source=data_source
        )
        self.trades.append(trade)

        self.logger.info(
            f"SELL {quantity} {symbol} @ {price:.2f} | "
            f"Proceeds: {net_proceeds:.2f} (base={base_proceeds:.2f}, "
            f"comm={commission:.2f}, slip={slippage:.2f}) | "
            f"Cash: {self.cash:.2f}"
        )

        return True

    def calculate_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value (cash + positions).

        Args:
            current_prices: Dict of {symbol: current_price}

        Returns:
            Total portfolio value
        """
        position_value = sum(
            self.positions[symbol] * current_prices.get(symbol, 0)
            for symbol in self.positions
        )
        return self.cash + position_value

    def record_daily_value(self, date: str, current_prices: Dict[str, float]):
        """Record portfolio value for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)
            current_prices: Current market prices
        """
        value = self.calculate_value(current_prices)
        self.value_history.append((date, value))

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """Get equity curve (daily portfolio values).

        Returns:
            List of {date, value} dictionaries
        """
        return [
            {'date': date, 'value': value}
            for date, value in self.value_history
        ]

    def get_trade_log(self) -> List[Dict[str, Any]]:
        """Get complete trade log.

        Returns:
            List of trade dictionaries
        """
        return [trade.to_dict() for trade in self.trades]

    def get_summary(self, final_prices: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Get portfolio summary statistics.

        Args:
            final_prices: Final market prices for open positions

        Returns:
            Summary dictionary
        """
        final_prices = final_prices or {}
        final_value = self.calculate_value(final_prices)

        return {
            'initial_capital': self.initial_capital,
            'final_cash': self.cash,
            'final_value': final_value,
            'total_return': (final_value - self.initial_capital) / self.initial_capital,
            'total_trades': len(self.trades),
            'current_positions': dict(self.positions),
            'commission_rate': self.commission_rate,
            'slippage_rate': self.slippage_rate
        }
