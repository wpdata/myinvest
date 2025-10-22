"""Trade analysis calculator (T069).

Analyzes trade execution:
- Win rate
- Profit factor
- Average win/loss
- Trade distribution
"""

from typing import List, Dict, Any
import pandas as pd


class TradeAnalysis:
    """Analyze trade execution and profitability."""

    def calculate_win_rate(self, trade_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate win rate from trade log.

        Args:
            trade_log: List of trades from Portfolio

        Returns:
            Dict with win_rate, winning_trades, losing_trades, total_trades
        """
        if not trade_log:
            return {
                'win_rate': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'breakeven_trades': 0,
                'total_trades': 0
            }

        # Match BUY and SELL to calculate P&L per trade
        trades_by_symbol = self._match_trades(trade_log)

        winning = 0
        losing = 0
        breakeven = 0

        for symbol_trades in trades_by_symbol.values():
            for trade in symbol_trades:
                pnl = trade.get('pnl', 0)
                if pnl > 0:
                    winning += 1
                elif pnl < 0:
                    losing += 1
                else:
                    breakeven += 1

        total = winning + losing + breakeven
        win_rate = winning / total if total > 0 else 0.0

        return {
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'winning_trades': winning,
            'losing_trades': losing,
            'breakeven_trades': breakeven,
            'total_trades': total
        }

    def calculate_profit_factor(self, trade_log: List[Dict[str, Any]]) -> float:
        """Calculate profit factor (gross profit / gross loss).

        Args:
            trade_log: List of trades

        Returns:
            Profit factor (higher is better, >1 means profitable)
        """
        trades_by_symbol = self._match_trades(trade_log)

        gross_profit = 0.0
        gross_loss = 0.0

        for symbol_trades in trades_by_symbol.values():
            for trade in symbol_trades:
                pnl = trade.get('pnl', 0)
                if pnl > 0:
                    gross_profit += pnl
                elif pnl < 0:
                    gross_loss += abs(pnl)

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    def calculate_average_win_loss(
        self,
        trade_log: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate average win and average loss.

        Args:
            trade_log: List of trades

        Returns:
            Dict with avg_win, avg_loss, avg_win_loss_ratio
        """
        trades_by_symbol = self._match_trades(trade_log)

        wins = []
        losses = []

        for symbol_trades in trades_by_symbol.values():
            for trade in symbol_trades:
                pnl = trade.get('pnl', 0)
                if pnl > 0:
                    wins.append(pnl)
                elif pnl < 0:
                    losses.append(abs(pnl))

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        ratio = avg_win / avg_loss if avg_loss > 0 else 0.0

        return {
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_loss_ratio': ratio
        }

    def analyze_trade_distribution(
        self,
        trade_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze distribution of trades.

        Args:
            trade_log: List of trades

        Returns:
            Dict with largest_win, largest_loss, median_pnl, etc.
        """
        trades_by_symbol = self._match_trades(trade_log)

        all_pnls = []
        for symbol_trades in trades_by_symbol.values():
            for trade in symbol_trades:
                all_pnls.append(trade.get('pnl', 0))

        if not all_pnls:
            return {
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'median_pnl': 0.0,
                'total_pnl': 0.0
            }

        pnl_series = pd.Series(all_pnls)

        return {
            'largest_win': pnl_series.max(),
            'largest_loss': pnl_series.min(),
            'median_pnl': pnl_series.median(),
            'mean_pnl': pnl_series.mean(),
            'total_pnl': pnl_series.sum(),
            'pnl_std': pnl_series.std()
        }

    def calculate_all_metrics(
        self,
        trade_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate all trade analysis metrics.

        Args:
            trade_log: List of trades from backtest

        Returns:
            Complete trade metrics dictionary
        """
        win_rate_metrics = self.calculate_win_rate(trade_log)
        profit_factor = self.calculate_profit_factor(trade_log)
        avg_metrics = self.calculate_average_win_loss(trade_log)
        distribution = self.analyze_trade_distribution(trade_log)

        return {
            **win_rate_metrics,
            'profit_factor': profit_factor,
            **avg_metrics,
            **distribution
        }

    def _match_trades(self, trade_log: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Match BUY and SELL trades to calculate P&L.

        Args:
            trade_log: Raw trade log from Portfolio

        Returns:
            Dict of {symbol: [matched_trades]} where each matched trade has P&L
        """
        trades_by_symbol = {}

        # Group trades by symbol
        for trade in trade_log:
            symbol = trade['symbol']
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = []
            trades_by_symbol[symbol].append(trade)

        # Match BUY and SELL for each symbol
        matched_trades = {}

        for symbol, trades in trades_by_symbol.items():
            matched = []
            position_queue = []  # Track open positions (FIFO)

            for trade in sorted(trades, key=lambda x: x['timestamp']):
                if trade['action'] == 'BUY':
                    # Add to position queue
                    position_queue.append({
                        'buy_price': trade['price'],
                        'buy_timestamp': trade['timestamp'],
                        'quantity': trade['quantity'],
                        'buy_cost': trade['total_cost']
                    })
                elif trade['action'] == 'SELL' and position_queue:
                    # Match with oldest BUY (FIFO)
                    sell_quantity = trade['quantity']
                    sell_price = trade['price']
                    sell_timestamp = trade['timestamp']
                    sell_proceeds = -trade['total_cost']  # Negative = cash inflow

                    while sell_quantity > 0 and position_queue:
                        position = position_queue[0]
                        matched_qty = min(sell_quantity, position['quantity'])

                        # Calculate P&L for this matched portion
                        buy_cost_per_share = position['buy_cost'] / position['quantity']
                        sell_proceeds_per_share = sell_proceeds / trade['quantity']
                        pnl = matched_qty * (sell_proceeds_per_share - buy_cost_per_share)

                        matched.append({
                            'symbol': symbol,
                            'buy_date': position['buy_timestamp'],
                            'sell_date': sell_timestamp,
                            'buy_price': position['buy_price'],
                            'sell_price': sell_price,
                            'quantity': matched_qty,
                            'pnl': pnl,
                            'return_pct': (sell_price - position['buy_price']) / position['buy_price'] * 100
                        })

                        # Update quantities
                        sell_quantity -= matched_qty
                        position['quantity'] -= matched_qty

                        # Remove position if fully sold
                        if position['quantity'] == 0:
                            position_queue.pop(0)

            matched_trades[symbol] = matched

        return matched_trades
