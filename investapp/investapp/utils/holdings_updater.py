"""持仓价格更新工具 - 实时获取市场数据更新持仓."""

import sys
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-data'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))

from sqlalchemy.orm import Session
from investlib_data.models import CurrentHolding
from investlib_data.market_api import MarketDataFetcher

logger = logging.getLogger(__name__)


class HoldingsUpdater:
    """更新持仓的当前价格和收益数据."""

    def __init__(self):
        """初始化更新器."""
        self.market_fetcher = MarketDataFetcher()

    def update_all_holdings(self, session: Session) -> Dict[str, Any]:
        """更新所有持仓的价格和收益.

        Args:
            session: 数据库会话

        Returns:
            更新结果字典
        """
        start_time = datetime.now()
        logger.info("[HoldingsUpdater] 开始更新所有持仓价格...")

        results = {
            'total_holdings': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # 获取所有持仓
            holdings = session.query(CurrentHolding).all()
            results['total_holdings'] = len(holdings)

            if not holdings:
                logger.info("[HoldingsUpdater] 没有持仓需要更新")
                return results

            # 更新每个持仓
            for holding in holdings:
                try:
                    logger.info(f"[HoldingsUpdater] 更新 {holding.symbol}...")

                    # 获取最新价格数据 (获取最近7天数据，取最新一条)
                    from datetime import timedelta
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

                    result = self.market_fetcher.fetch_with_fallback(
                        symbol=holding.symbol,
                        start_date=start_date,
                        end_date=end_date,
                        prefer_cache=False  # 强制从API获取最新数据
                    )

                    if result and 'data' in result:
                        df = result['data']
                        if not df.empty:
                            # 取最新的收盘价
                            latest_price = df.iloc[-1]['close']

                            # 更新价格
                            old_price = holding.current_price
                            holding.current_price = latest_price

                            # 重新计算收益
                            holding.calculate_profit_loss()

                            # 更新时间戳
                            holding.last_update_timestamp = datetime.now()

                            logger.info(
                                f"[HoldingsUpdater] ✅ {holding.symbol}: "
                                f"¥{old_price:.2f} → ¥{holding.current_price:.2f} "
                                f"(盈亏: {holding.profit_loss_pct:+.2f}%)"
                            )

                            results['updated'] += 1
                        else:
                            raise ValueError("返回的数据为空")
                    else:
                        raise ValueError("无法获取价格数据")

                except Exception as e:
                    logger.error(f"[HoldingsUpdater] ❌ 更新 {holding.symbol} 失败: {e}")
                    results['failed'] += 1
                    results['errors'].append({
                        'symbol': holding.symbol,
                        'error': str(e)
                    })

            # 提交更改
            session.commit()

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"[HoldingsUpdater] ✅ 更新完成: "
                f"{results['updated']}/{results['total_holdings']} 成功, "
                f"耗时 {duration:.2f}秒"
            )

        except Exception as e:
            logger.error(f"[HoldingsUpdater] ❌ 更新过程出错: {e}")
            session.rollback()
            results['errors'].append({
                'symbol': 'GLOBAL',
                'error': str(e)
            })

        return results

    def update_single_holding(
        self,
        session: Session,
        symbol: str
    ) -> Dict[str, Any]:
        """更新单个持仓的价格.

        Args:
            session: 数据库会话
            symbol: 股票代码

        Returns:
            更新结果
        """
        from datetime import timedelta

        logger.info(f"[HoldingsUpdater] 更新单个持仓: {symbol}")

        try:
            holding = session.query(CurrentHolding).filter_by(symbol=symbol).first()

            if not holding:
                return {
                    'success': False,
                    'error': f'未找到持仓: {symbol}'
                }

            # 获取最新价格
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            result = self.market_fetcher.fetch_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                prefer_cache=False
            )

            if result and 'data' in result:
                df = result['data']
                if not df.empty:
                    latest_price = df.iloc[-1]['close']

                    old_price = holding.current_price
                    holding.current_price = latest_price
                    holding.calculate_profit_loss()
                    holding.last_update_timestamp = datetime.now()

                    session.commit()

                    return {
                        'success': True,
                        'symbol': symbol,
                        'old_price': old_price,
                        'new_price': holding.current_price,
                        'profit_loss_pct': holding.profit_loss_pct,
                        'profit_loss_amount': holding.profit_loss_amount
                    }
                else:
                    return {
                        'success': False,
                        'error': '返回的数据为空'
                    }
            else:
                return {
                    'success': False,
                    'error': '无法获取价格数据'
                }

        except Exception as e:
            logger.error(f"[HoldingsUpdater] 更新 {symbol} 失败: {e}")
            session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
