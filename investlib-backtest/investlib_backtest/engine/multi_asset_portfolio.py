"""Multi-Asset Portfolio for futures and options backtesting (T037, T038).

Extends base Portfolio with:
- Margin management for futures
- Forced liquidation for futures (T038)
- Greeks tracking for options
"""

import logging
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class MultiAssetTrade:
    """Record of a multi-asset trade execution."""
    timestamp: str
    symbol: str
    asset_type: Literal['stock', 'futures', 'option']
    action: str  # 'BUY' or 'SELL'
    price: float
    quantity: int
    commission: float
    slippage: float
    total_cost: float
    data_source: str

    # Futures-specific fields
    margin_required: float = 0.0
    margin_rate: float = 0.0

    # Options-specific fields
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    theta: float = 0.0

    # Forced liquidation tracking
    is_forced_liquidation: bool = False
    liquidation_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class MultiAssetPortfolio:
    """Portfolio with multi-asset support (stocks, futures, options)."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001,
        force_close_margin_rate: float = 0.03  # 3% for forced liquidation
    ):
        """Initialize multi-asset portfolio.

        Args:
            initial_capital: Starting cash amount
            commission_rate: Commission as decimal (default 0.03%)
            slippage_rate: Slippage as decimal (default 0.1%)
            force_close_margin_rate: Margin rate triggering forced liquidation (default 3%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.force_close_margin_rate = force_close_margin_rate

        # Positions: {symbol: {'quantity': int, 'asset_type': str, 'entry_price': float}}
        self.positions: Dict[str, Dict[str, Any]] = {}

        # Margin tracking for futures
        self.margin_used: float = 0.0  # Total margin currently in use
        self.margin_available: float = initial_capital  # Available for new positions

        # Trade log
        self.trades: List[MultiAssetTrade] = []

        # Daily value history
        self.value_history: List[tuple] = []

        # Forced liquidation count
        self.forced_liquidations = 0

        self.logger = logging.getLogger(__name__)

    def buy(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        asset_type: Literal['stock', 'futures', 'option'] = 'stock',
        data_source: str = "backtest",
        margin_rate: float = 0.15,  # Default 15% for futures
        greeks: Optional[Dict[str, float]] = None,
        # Option-specific parameters
        expiry_date: Optional[str] = None,
        strike_price: Optional[float] = None,
        option_type: Optional[str] = None
    ) -> bool:
        """Execute buy order with multi-asset support.

        Args:
            symbol: Symbol
            price: Purchase price
            quantity: Quantity to buy
            timestamp: Execution timestamp
            asset_type: 'stock', 'futures', or 'option'
            data_source: Market data source
            margin_rate: Margin rate for futures (default 15%)
            greeks: Options Greeks dict (delta, gamma, vega, theta)

        Returns:
            True if order executed successfully
        """
        greeks = greeks or {}

        if asset_type == 'stock':
            return self._buy_stock(symbol, price, quantity, timestamp, data_source)
        elif asset_type == 'futures':
            return self._buy_futures(symbol, price, quantity, timestamp, data_source, margin_rate)
        elif asset_type == 'option':
            return self._buy_option(
                symbol, price, quantity, timestamp, data_source, greeks,
                expiry_date, strike_price, option_type
            )
        else:
            raise ValueError(f"Unknown asset_type: {asset_type}")

    def _buy_stock(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str
    ) -> bool:
        """Buy stock (full payment required)."""
        # Calculate costs
        base_cost = price * quantity
        commission = base_cost * self.commission_rate
        slippage = base_cost * self.slippage_rate
        total_cost = base_cost + commission + slippage

        # Check funds
        if total_cost > self.cash:
            self.logger.warning(
                f"Insufficient funds for BUY {symbol}: need {total_cost:.2f}, have {self.cash:.2f}"
            )
            return False

        # Execute
        self.cash -= total_cost

        if symbol in self.positions:
            self.positions[symbol]['quantity'] += quantity
        else:
            self.positions[symbol] = {
                'quantity': quantity,
                'asset_type': 'stock',
                'entry_price': price
            }

        # Record trade
        trade = MultiAssetTrade(
            timestamp=timestamp,
            symbol=symbol,
            asset_type='stock',
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
            f"BUY STOCK {quantity} {symbol} @ {price:.2f} | Cost: {total_cost:.2f} | Cash: {self.cash:.2f}"
        )
        return True

    def _buy_futures(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str,
        margin_rate: float
    ) -> bool:
        """Buy futures (margin-based)."""
        from investlib_margin.calculator import MarginCalculator

        calc = MarginCalculator()

        # Calculate margin required
        # Assuming standard multiplier (e.g., 300 for stock index futures)
        multiplier = 300 if symbol.startswith('IF') or symbol.startswith('IC') else 100

        margin_required = calc.calculate_margin(
            contract_type='futures',
            quantity=quantity,
            price=price,
            multiplier=multiplier,
            margin_rate=margin_rate
        )

        # Check margin available
        if margin_required > self.margin_available:
            self.logger.warning(
                f"Insufficient margin for BUY {symbol}: need {margin_required:.2f}, "
                f"available {self.margin_available:.2f}"
            )
            return False

        # Calculate transaction costs (on notional value)
        notional_value = price * quantity * multiplier
        commission = notional_value * self.commission_rate
        slippage = notional_value * self.slippage_rate
        total_cost = commission + slippage  # No upfront payment for futures

        # Check cash for fees
        if total_cost > self.cash:
            self.logger.warning(
                f"Insufficient cash for fees: need {total_cost:.2f}, have {self.cash:.2f}"
            )
            return False

        # Execute
        self.cash -= total_cost
        self.margin_used += margin_required
        self.margin_available -= margin_required

        if symbol in self.positions:
            # Average price if adding to position
            old_qty = self.positions[symbol]['quantity']
            old_price = self.positions[symbol]['entry_price']
            new_qty = old_qty + quantity
            new_avg_price = (old_price * old_qty + price * quantity) / new_qty

            self.positions[symbol]['quantity'] = new_qty
            self.positions[symbol]['entry_price'] = new_avg_price
        else:
            self.positions[symbol] = {
                'quantity': quantity,
                'asset_type': 'futures',
                'entry_price': price,
                'margin_rate': margin_rate,
                'multiplier': multiplier
            }

        # Record trade
        trade = MultiAssetTrade(
            timestamp=timestamp,
            symbol=symbol,
            asset_type='futures',
            action='BUY',
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            total_cost=total_cost,
            data_source=data_source,
            margin_required=margin_required,
            margin_rate=margin_rate
        )
        self.trades.append(trade)

        self.logger.info(
            f"BUY FUTURES {quantity} {symbol} @ {price:.2f} | "
            f"Margin: {margin_required:.2f} | Cash: {self.cash:.2f} | "
            f"Margin available: {self.margin_available:.2f}"
        )
        return True

    def _buy_option(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str,
        greeks: Dict[str, float],
        expiry_date: Optional[str],
        strike_price: Optional[float],
        option_type: Optional[str]
    ) -> bool:
        """Buy option (full premium payment)."""
        # Option premium: price * quantity * multiplier (10000 for 50ETF options)
        multiplier = 10000
        base_cost = price * quantity * multiplier
        commission = base_cost * self.commission_rate
        slippage = base_cost * self.slippage_rate
        total_cost = base_cost + commission + slippage

        # Check funds
        if total_cost > self.cash:
            self.logger.warning(
                f"Insufficient funds for BUY OPTION {symbol}: need {total_cost:.2f}, have {self.cash:.2f}"
            )
            return False

        # Execute
        self.cash -= total_cost

        if symbol in self.positions:
            self.positions[symbol]['quantity'] += quantity
        else:
            self.positions[symbol] = {
                'quantity': quantity,
                'asset_type': 'option',
                'entry_price': price,
                'greeks': greeks,
                'multiplier': multiplier,
                'expiry_date': expiry_date,
                'strike_price': strike_price,
                'option_type': option_type
            }

        # Record trade
        trade = MultiAssetTrade(
            timestamp=timestamp,
            symbol=symbol,
            asset_type='option',
            action='BUY',
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            total_cost=total_cost,
            data_source=data_source,
            delta=greeks.get('delta', 0.0),
            gamma=greeks.get('gamma', 0.0),
            vega=greeks.get('vega', 0.0),
            theta=greeks.get('theta', 0.0)
        )
        self.trades.append(trade)

        self.logger.info(
            f"BUY OPTION {quantity} {symbol} @ {price:.2f} | "
            f"Cost: {total_cost:.2f} | Delta: {greeks.get('delta', 0):.3f}"
        )
        return True

    def sell(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str = "backtest",
        is_forced: bool = False,
        liquidation_reason: str = ""
    ) -> bool:
        """Execute sell order with multi-asset support.

        Args:
            symbol: Symbol
            price: Sell price
            quantity: Quantity to sell
            timestamp: Execution timestamp
            data_source: Market data source
            is_forced: True if forced liquidation
            liquidation_reason: Reason for forced liquidation

        Returns:
            True if order executed successfully
        """
        # Check position exists
        if symbol not in self.positions:
            self.logger.warning(f"No position to sell: {symbol}")
            return False

        position = self.positions[symbol]
        asset_type = position['asset_type']

        if asset_type == 'stock':
            return self._sell_stock(symbol, price, quantity, timestamp, data_source, is_forced, liquidation_reason)
        elif asset_type == 'futures':
            return self._sell_futures(symbol, price, quantity, timestamp, data_source, is_forced, liquidation_reason)
        elif asset_type == 'option':
            return self._sell_option(symbol, price, quantity, timestamp, data_source)
        else:
            raise ValueError(f"Unknown asset_type: {asset_type}")

    def _sell_stock(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str,
        is_forced: bool,
        liquidation_reason: str
    ) -> bool:
        """Sell stock."""
        position = self.positions[symbol]
        current_qty = position['quantity']

        if quantity > current_qty:
            self.logger.warning(
                f"Insufficient shares for SELL {symbol}: need {quantity}, have {current_qty}"
            )
            return False

        # Calculate proceeds
        base_proceeds = price * quantity
        commission = base_proceeds * self.commission_rate
        slippage = base_proceeds * self.slippage_rate
        net_proceeds = base_proceeds - commission - slippage

        # Execute
        self.cash += net_proceeds
        position['quantity'] -= quantity

        if position['quantity'] == 0:
            del self.positions[symbol]

        # Record trade
        trade = MultiAssetTrade(
            timestamp=timestamp,
            symbol=symbol,
            asset_type='stock',
            action='SELL',
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            total_cost=-net_proceeds,  # Negative = income
            data_source=data_source,
            is_forced_liquidation=is_forced,
            liquidation_reason=liquidation_reason
        )
        self.trades.append(trade)

        if is_forced:
            self.forced_liquidations += 1
            self.logger.warning(
                f"FORCED SELL STOCK {quantity} {symbol} @ {price:.2f} | "
                f"Reason: {liquidation_reason} | Proceeds: {net_proceeds:.2f}"
            )
        else:
            self.logger.info(
                f"SELL STOCK {quantity} {symbol} @ {price:.2f} | Proceeds: {net_proceeds:.2f}"
            )

        return True

    def _sell_futures(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str,
        is_forced: bool,
        liquidation_reason: str
    ) -> bool:
        """Sell futures (close position, release margin)."""
        position = self.positions[symbol]
        current_qty = position['quantity']

        if quantity > current_qty:
            self.logger.warning(
                f"Insufficient contracts for SELL {symbol}: need {quantity}, have {current_qty}"
            )
            return False

        # Calculate P&L
        entry_price = position['entry_price']
        multiplier = position['multiplier']
        margin_rate = position['margin_rate']

        pnl = (price - entry_price) * quantity * multiplier

        # Calculate fees
        notional_value = price * quantity * multiplier
        commission = notional_value * self.commission_rate
        slippage = notional_value * self.slippage_rate
        total_fees = commission + slippage

        net_pnl = pnl - total_fees

        # Release margin
        from investlib_margin.calculator import MarginCalculator
        calc = MarginCalculator()

        margin_released = calc.calculate_margin(
            contract_type='futures',
            quantity=quantity,
            price=entry_price,  # Use entry price for margin calculation
            multiplier=multiplier,
            margin_rate=margin_rate
        )

        # Execute
        self.cash += net_pnl
        self.margin_used -= margin_released
        self.margin_available += margin_released
        position['quantity'] -= quantity

        if position['quantity'] == 0:
            del self.positions[symbol]

        # Record trade
        trade = MultiAssetTrade(
            timestamp=timestamp,
            symbol=symbol,
            asset_type='futures',
            action='SELL',
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            total_cost=-net_pnl,  # Negative = profit
            data_source=data_source,
            margin_required=-margin_released,  # Negative = released
            margin_rate=margin_rate,
            is_forced_liquidation=is_forced,
            liquidation_reason=liquidation_reason
        )
        self.trades.append(trade)

        if is_forced:
            self.forced_liquidations += 1
            self.logger.warning(
                f"FORCED SELL FUTURES {quantity} {symbol} @ {price:.2f} | "
                f"Reason: {liquidation_reason} | P&L: {net_pnl:.2f} | "
                f"Margin released: {margin_released:.2f}"
            )
        else:
            self.logger.info(
                f"SELL FUTURES {quantity} {symbol} @ {price:.2f} | "
                f"P&L: {net_pnl:.2f} | Margin released: {margin_released:.2f}"
            )

        return True

    def _sell_option(
        self,
        symbol: str,
        price: float,
        quantity: int,
        timestamp: str,
        data_source: str
    ) -> bool:
        """Sell option."""
        position = self.positions[symbol]
        current_qty = position['quantity']

        if quantity > current_qty:
            self.logger.warning(
                f"Insufficient contracts for SELL {symbol}: need {quantity}, have {current_qty}"
            )
            return False

        # Calculate proceeds
        multiplier = position['multiplier']
        base_proceeds = price * quantity * multiplier
        commission = base_proceeds * self.commission_rate
        slippage = base_proceeds * self.slippage_rate
        net_proceeds = base_proceeds - commission - slippage

        # Execute
        self.cash += net_proceeds
        position['quantity'] -= quantity

        if position['quantity'] == 0:
            del self.positions[symbol]

        # Record trade
        trade = MultiAssetTrade(
            timestamp=timestamp,
            symbol=symbol,
            asset_type='option',
            action='SELL',
            price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            total_cost=-net_proceeds,
            data_source=data_source
        )
        self.trades.append(trade)

        self.logger.info(
            f"SELL OPTION {quantity} {symbol} @ {price:.2f} | Proceeds: {net_proceeds:.2f}"
        )
        return True

    def check_forced_liquidation(
        self,
        current_prices: Dict[str, float],
        timestamp: str,
        data_source: str = "backtest"
    ) -> int:
        """Check and execute forced liquidations for futures positions (T038).

        Args:
            current_prices: Current market prices {symbol: price}
            timestamp: Current timestamp
            data_source: Data source

        Returns:
            Number of positions force-liquidated
        """
        from investlib_margin.calculator import MarginCalculator
        calc = MarginCalculator()

        liquidated_count = 0
        positions_to_liquidate = []

        # Check each futures position
        for symbol, position in self.positions.items():
            if position['asset_type'] != 'futures':
                continue

            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]
            entry_price = position['entry_price']
            margin_rate = position['margin_rate']

            # Calculate liquidation price
            # Assuming long position (BUY)
            liquidation_price = calc.calculate_liquidation_price(
                entry_price=entry_price,
                direction='long',
                margin_rate=margin_rate,
                force_close_margin_rate=self.force_close_margin_rate
            )

            # Check if current price hit liquidation
            if current_price <= liquidation_price:
                positions_to_liquidate.append((symbol, position, current_price))
                self.logger.warning(
                    f"⚠️ FORCED LIQUIDATION TRIGGERED for {symbol}: "
                    f"Current={current_price:.2f}, Liquidation={liquidation_price:.2f}, "
                    f"Entry={entry_price:.2f}"
                )

        # Execute liquidations
        for symbol, position, price in positions_to_liquidate:
            quantity = position['quantity']
            success = self._sell_futures(
                symbol=symbol,
                price=price,
                quantity=quantity,
                timestamp=timestamp,
                data_source=data_source,
                is_forced=True,
                liquidation_reason=f"Margin insufficient: price {price:.2f} <= liquidation {liquidation_price:.2f}"
            )

            if success:
                liquidated_count += 1

        return liquidated_count

    def check_option_expiry(
        self,
        current_date: str,
        current_prices: Dict[str, float],
        data_source: str = "backtest"
    ) -> int:
        """Check and handle option expiry (T039).

        Options expire at third Friday of the month. This method:
        1. Checks if any option positions are at expiry
        2. Calculates intrinsic value
        3. Auto-exercises ITM options or lets OTM expire worthless

        Args:
            current_date: Current date (YYYY-MM-DD)
            current_prices: Current market prices {underlying_symbol: price}
            data_source: Data source

        Returns:
            Number of options expired/exercised
        """
        from datetime import datetime

        expired_count = 0
        positions_to_expire = []

        current_dt = datetime.strptime(current_date, '%Y-%m-%d')

        # Check each option position
        for symbol, position in self.positions.items():
            if position['asset_type'] != 'option':
                continue

            # Check if position has expiry info
            if 'expiry_date' not in position:
                # Parse expiry from symbol if available
                # For now, skip if no expiry info
                continue

            expiry_date = position['expiry_date']
            expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')

            # Check if today is expiry date
            if current_dt.date() == expiry_dt.date():
                positions_to_expire.append((symbol, position))
                self.logger.info(
                    f"⏰ OPTION EXPIRY: {symbol} expires today ({current_date})"
                )

        # Process expiries
        for symbol, position in positions_to_expire:
            quantity = position['quantity']
            strike_price = position.get('strike_price', 0)
            option_type = position.get('option_type', 'call')
            multiplier = position.get('multiplier', 10000)

            # Get underlying price
            # Extract underlying from option symbol (e.g., 10005102.SH -> 510050.SH)
            # For simplicity, assume we have it in current_prices
            # In real implementation, need to map option symbol to underlying
            underlying_price = self._get_underlying_price(symbol, current_prices)

            if underlying_price is None:
                self.logger.warning(
                    f"Cannot find underlying price for {symbol}, assuming worthless"
                )
                intrinsic_value = 0
            else:
                # Calculate intrinsic value
                if option_type == 'call':
                    intrinsic_value = max(0, underlying_price - strike_price)
                else:  # put
                    intrinsic_value = max(0, strike_price - underlying_price)

            # Total value
            total_value = intrinsic_value * quantity * multiplier

            if intrinsic_value > 0:
                # ITM: Auto-exercise
                self.cash += total_value
                self.logger.info(
                    f"✅ OPTION EXERCISED: {symbol} ({option_type} @ {strike_price:.2f}) | "
                    f"Intrinsic: {intrinsic_value:.4f} | Total: {total_value:.2f}"
                )

                # Record as special trade
                trade = MultiAssetTrade(
                    timestamp=current_date,
                    symbol=symbol,
                    asset_type='option',
                    action='EXERCISE',
                    price=intrinsic_value,
                    quantity=quantity,
                    commission=0.0,
                    slippage=0.0,
                    total_cost=-total_value,  # Negative = income
                    data_source=data_source
                )
                self.trades.append(trade)
            else:
                # OTM: Expire worthless
                self.logger.info(
                    f"❌ OPTION EXPIRED WORTHLESS: {symbol} ({option_type} @ {strike_price:.2f}) | "
                    f"Underlying: {underlying_price:.2f if underlying_price else 'N/A'}"
                )

                # Record as worthless expiry
                trade = MultiAssetTrade(
                    timestamp=current_date,
                    symbol=symbol,
                    asset_type='option',
                    action='EXPIRE',
                    price=0.0,
                    quantity=quantity,
                    commission=0.0,
                    slippage=0.0,
                    total_cost=0.0,
                    data_source=data_source
                )
                self.trades.append(trade)

            # Remove position
            del self.positions[symbol]
            expired_count += 1

        return expired_count

    def _get_underlying_price(
        self,
        option_symbol: str,
        current_prices: Dict[str, float]
    ) -> Optional[float]:
        """Get underlying asset price for option.

        Args:
            option_symbol: Option symbol (e.g., '10005102.SH')
            current_prices: Dictionary of current prices

        Returns:
            Underlying price or None
        """
        # For 50ETF options (10XXXXXX.SH), underlying is 510050.SH
        if option_symbol.startswith('10') and '.SH' in option_symbol:
            underlying_symbol = '510050.SH'  # 50ETF
            return current_prices.get(underlying_symbol)

        # For other options, try to find in current_prices
        # This is a simplified implementation
        return None

    def record_daily_value(self, date: str, current_prices: Dict[str, float]):
        """Record daily portfolio value."""
        # Calculate total value
        total_value = self.cash

        # Add position values
        for symbol, position in self.positions.items():
            if symbol not in current_prices:
                continue

            price = current_prices[symbol]
            qty = position['quantity']
            asset_type = position['asset_type']

            if asset_type == 'stock':
                # Stock: quantity * price
                total_value += qty * price
            elif asset_type == 'futures':
                # Futures: P&L + margin
                entry_price = position['entry_price']
                multiplier = position['multiplier']
                pnl = (price - entry_price) * qty * multiplier
                total_value += pnl  # Cash already includes margin
            elif asset_type == 'option':
                # Option: quantity * price * multiplier
                multiplier = position['multiplier']
                total_value += qty * price * multiplier

        self.value_history.append((date, total_value))

    def get_summary(self, final_prices: Dict[str, float]) -> Dict[str, Any]:
        """Get portfolio summary."""
        # Calculate final value
        final_value = self.cash

        for symbol, position in self.positions.items():
            if symbol not in final_prices:
                continue

            price = final_prices[symbol]
            qty = position['quantity']
            asset_type = position['asset_type']

            if asset_type == 'stock':
                final_value += qty * price
            elif asset_type == 'futures':
                entry_price = position['entry_price']
                multiplier = position['multiplier']
                pnl = (price - entry_price) * qty * multiplier
                final_value += pnl
            elif asset_type == 'option':
                multiplier = position['multiplier']
                final_value += qty * price * multiplier

        total_return = (final_value - self.initial_capital) / self.initial_capital

        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'cash': self.cash,
            'margin_used': self.margin_used,
            'margin_available': self.margin_available,
            'positions': len(self.positions),
            'total_trades': len(self.trades),
            'forced_liquidations': self.forced_liquidations
        }

    def get_trade_log(self) -> List[Dict[str, Any]]:
        """Get trade history."""
        return [trade.to_dict() for trade in self.trades]

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """Get equity curve."""
        return [
            {'date': date, 'value': value}
            for date, value in self.value_history
        ]
