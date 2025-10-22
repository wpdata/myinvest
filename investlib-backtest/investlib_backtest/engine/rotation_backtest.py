"""多品种轮动策略回测引擎。

与传统的单品种回测不同，轮动策略回测需要：
1. 同时加载多个品种的历史数据
2. 跟踪当前持仓品种
3. 支持品种之间的切换（SWITCH操作）
4. 以资金视角而非品种视角计算收益
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from investlib_backtest.engine.portfolio import Portfolio


class RotationBacktestRunner:
    """多品种轮动策略回测引擎。

    专门用于回测需要在多个品种之间轮动的策略，如：
    - 股债轮动
    - ETF轮动
    - 行业轮动
    - 大类资产配置
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001
    ):
        """初始化回测引擎。

        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率（默认0.03%）
            slippage_rate: 滑点率（默认0.1%）
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        strategy,
        asset_symbols: Dict[str, str],
        start_date: str,
        end_date: str,
        capital: Optional[float] = None
    ) -> Dict[str, Any]:
        """运行多品种轮动策略回测。

        Args:
            strategy: 策略实例（必须支持多品种轮动）
            asset_symbols: 资产符号字典，例如：
                {
                    'index': '000300.SH',      # 监控指数
                    'etf': '159845.SZ',        # 进攻性资产
                    'bond': '511010.SH'        # 防御性资产
                }
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            capital: 初始资金（默认使用self.initial_capital）

        Returns:
            回测结果字典，包含：
            - 收益率曲线
            - 交易记录
            - 持仓变化
            - 绩效指标
        """
        capital = capital or self.initial_capital

        self.logger.info(
            f"[RotationBacktest] 开始多品种轮动回测: {strategy.name} "
            f"从 {start_date} 到 {end_date}"
        )

        # 初始化投资组合
        portfolio = RotationPortfolio(
            initial_capital=capital,
            commission_rate=self.commission_rate,
            slippage_rate=self.slippage_rate
        )

        # 获取所有资产的历史数据
        from investlib_data.market_api import MarketDataFetcher
        from investlib_data.cache_manager import CacheManager
        from investlib_data.database import SessionLocal

        session = None
        try:
            session = SessionLocal()
            cache_manager = CacheManager(session=session)
        except Exception as e:
            self.logger.warning(f"缓存不可用: {e}")
            cache_manager = None

        fetcher = MarketDataFetcher(cache_manager=cache_manager)

        try:
            # 加载所有资产的历史数据
            all_data: Dict[str, pd.DataFrame] = {}
            data_sources: Dict[str, str] = {}

            for asset_type, symbol in asset_symbols.items():
                self.logger.info(f"加载 {asset_type} 数据: {symbol}")
                result = fetcher.fetch_with_fallback(
                    symbol,
                    start_date,
                    end_date,
                    prefer_cache=True
                )
                all_data[asset_type] = result['data']
                data_sources[asset_type] = result['metadata']['api_source']
                self.logger.info(
                    f"✓ 加载 {len(result['data'])} 天数据 ({asset_type}: {symbol})"
                )

            # 获取所有交易日（取所有资产的并集）
            all_dates = sorted(set(
                date for df in all_data.values()
                for date in df['timestamp'].unique()
            ))

            self.logger.info(f"回测时间跨度: {len(all_dates)} 个交易日")

            # 持仓状态跟踪
            current_position = None  # 当前持仓品种
            position_entry_date = None  # 入场日期
            position_entry_price = None  # 入场价格

            # 信号和交易统计
            signals_generated = 0
            switches_executed = 0

            # 主回测循环
            for i, current_date in enumerate(all_dates):
                # 获取当日各资产价格
                current_prices = {}
                for asset_type, df in all_data.items():
                    day_data = df[df['timestamp'] == current_date]
                    if not day_data.empty:
                        current_prices[asset_type] = day_data.iloc[0]['close']

                # 准备策略所需的历史数据（截止到当前日期）
                historical_data = {}
                for asset_type, df in all_data.items():
                    historical_data[asset_type] = df[df['timestamp'] <= current_date]

                # 检查是否有足够的历史数据
                min_required_days = 120  # 根据策略需求调整
                if any(len(df) < min_required_days for df in historical_data.values()):
                    continue

                # 生成交易信号
                try:
                    # 根据策略类型调用不同的方法
                    if hasattr(strategy, 'generate_multi_asset_signal'):
                        # 多品种轮动策略
                        signal = strategy.generate_multi_asset_signal(
                            index_data=historical_data.get('index'),
                            etf_data=historical_data.get('etf'),
                            bond_data=historical_data.get('bond'),
                            current_position=current_position,
                            position_entry_date=position_entry_date
                        )
                    else:
                        self.logger.warning(
                            f"策略 {strategy.name} 不支持多品种轮动回测"
                        )
                        continue

                    signals_generated += 1

                    # 处理交易信号
                    if signal and signal.get('action') == 'SWITCH':
                        from_symbol = signal.get('from_symbol')
                        to_symbol = signal.get('target_symbol')
                        reasoning = signal.get('reasoning', {})

                        # 确定价格（使用目标资产的当前价格）
                        if to_symbol == asset_symbols.get('etf'):
                            price = current_prices.get('etf', 0)
                            asset_key = 'etf'
                        elif to_symbol == asset_symbols.get('bond'):
                            price = current_prices.get('bond', 0)
                            asset_key = 'bond'
                        else:
                            self.logger.warning(f"未知的目标品种: {to_symbol}")
                            continue

                        if price > 0:
                            # 执行切换
                            success = portfolio.switch_position(
                                from_symbol=from_symbol or current_position,
                                to_symbol=to_symbol,
                                price=price,
                                timestamp=current_date,
                                reasoning=reasoning
                            )

                            if success:
                                switches_executed += 1
                                current_position = to_symbol
                                position_entry_date = current_date
                                position_entry_price = price

                                self.logger.debug(
                                    f"[{current_date}] 切换: {from_symbol or 'None'} → "
                                    f"{to_symbol} @ {price:.2f} | "
                                    f"原因: {reasoning.get('trigger', 'N/A')}"
                                )

                except Exception as e:
                    self.logger.warning(
                        f"信号生成失败 ({current_date}): {e}"
                    )

                # 记录每日组合价值
                portfolio.record_daily_value(current_date, current_prices, asset_symbols)

                # 进度日志
                if (i + 1) % 50 == 0:
                    progress = (i + 1) / len(all_dates) * 100
                    self.logger.info(
                        f"进度: {progress:.1f}% ({i+1}/{len(all_dates)} 天) | "
                        f"切换次数: {switches_executed} | 信号数: {signals_generated}"
                    )

            # 获取最终价格用于组合估值
            final_prices = {
                asset_type: df.iloc[-1]['close']
                for asset_type, df in all_data.items()
            }

            # 生成回测报告
            summary = portfolio.get_summary(final_prices, asset_symbols)

            self.logger.info(
                f"[RotationBacktest] 回测完成: "
                f"最终价值: {summary['final_value']:.2f} | "
                f"收益率: {summary['total_return']*100:.2f}% | "
                f"切换次数: {switches_executed}"
            )

            return {
                'strategy_name': strategy.name,
                'asset_symbols': asset_symbols,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': capital,
                'final_capital': summary['final_value'],
                'total_return': summary['total_return'],
                'total_switches': switches_executed,
                'signals_generated': signals_generated,
                'switch_log': portfolio.get_switch_log(),
                'equity_curve': portfolio.get_equity_curve(),
                'position_history': portfolio.get_position_history(),
                'data_sources': data_sources,
                'backtest_completed_at': datetime.now().isoformat()
            }

        finally:
            if session:
                session.close()
                self.logger.debug("[RotationBacktest] 数据库会话已关闭")


class RotationPortfolio:
    """轮动策略专用投资组合。

    跟踪多品种之间的切换，以资金为中心计算收益。
    """

    def __init__(
        self,
        initial_capital: float,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.001
    ):
        """初始化组合。"""
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

        # 当前持仓
        self.current_position = None  # 当前持有的品种
        self.current_shares = 0  # 持有份额

        # 历史记录
        self.switch_log = []  # 切换记录
        self.equity_curve = []  # 净值曲线
        self.position_history = []  # 持仓历史

    def switch_position(
        self,
        from_symbol: Optional[str],
        to_symbol: str,
        price: float,
        timestamp: str,
        reasoning: Dict = None
    ) -> bool:
        """在品种之间切换。

        Args:
            from_symbol: 原持仓品种（None表示空仓）
            to_symbol: 目标品种
            price: 切换价格
            timestamp: 时间戳
            reasoning: 切换原因

        Returns:
            是否成功
        """
        # 如果有现有持仓，先卖出
        if self.current_position and self.current_shares > 0:
            sell_value = self.current_shares * price
            commission = sell_value * self.commission_rate
            slippage = sell_value * self.slippage_rate
            self.cash += sell_value - commission - slippage

        # 全仓买入新品种
        buy_value = self.cash * 0.99  # 留1%现金应对费用
        commission = buy_value * self.commission_rate
        slippage = buy_value * self.slippage_rate
        actual_buy_value = buy_value - commission - slippage

        self.current_shares = actual_buy_value / price
        self.cash -= buy_value
        self.current_position = to_symbol

        # 记录切换
        self.switch_log.append({
            'timestamp': timestamp,
            'from_symbol': from_symbol,
            'to_symbol': to_symbol,
            'price': price,
            'shares': self.current_shares,
            'value': actual_buy_value,
            'commission': commission,
            'slippage': slippage,
            'reasoning': reasoning or {}
        })

        return True

    def record_daily_value(
        self,
        date: str,
        prices: Dict[str, float],
        asset_symbols: Dict[str, str]
    ):
        """记录每日价值。"""
        # 找到当前持仓对应的价格
        current_value = self.cash
        if self.current_position and self.current_shares > 0:
            # 找到对应的资产类型
            for asset_type, symbol in asset_symbols.items():
                if symbol == self.current_position and asset_type in prices:
                    current_value += self.current_shares * prices[asset_type]
                    break

        self.equity_curve.append({
            'date': date,
            'value': current_value,
            'cash': self.cash,
            'position': self.current_position,
            'shares': self.current_shares
        })

        self.position_history.append({
            'date': date,
            'symbol': self.current_position,
            'shares': self.current_shares
        })

    def get_summary(
        self,
        final_prices: Dict[str, float],
        asset_symbols: Dict[str, str]
    ) -> Dict[str, Any]:
        """获取投资组合摘要。"""
        # 计算最终价值
        final_value = self.cash
        if self.current_position and self.current_shares > 0:
            for asset_type, symbol in asset_symbols.items():
                if symbol == self.current_position and asset_type in final_prices:
                    final_value += self.current_shares * final_prices[asset_type]
                    break

        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': (final_value - self.initial_capital) / self.initial_capital,
            'current_position': self.current_position,
            'current_shares': self.current_shares,
            'cash': self.cash
        }

    def get_switch_log(self) -> List[Dict]:
        """获取切换日志。"""
        return self.switch_log

    def get_equity_curve(self) -> List[Dict]:
        """获取净值曲线。"""
        return self.equity_curve

    def get_position_history(self) -> List[Dict]:
        """获取持仓历史。"""
        return self.position_history
