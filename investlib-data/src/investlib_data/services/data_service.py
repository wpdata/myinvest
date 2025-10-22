"""Unified data service integrating API and cache."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session

from investlib_data.market_api import MarketDataFetcher
from investlib_data.cache_manager import CacheManager


class DataService:
    """统一数据服务：API 优先，缓存降级。"""

    def __init__(self, session: Session):
        """初始化数据服务。

        Args:
            session: SQLAlchemy 数据库会话
        """
        self.session = session
        self.api_fetcher = MarketDataFetcher()
        self.cache = CacheManager(session)

    def get_market_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取市场数据，支持缓存。

        数据获取策略：
        1. 如果启用缓存且缓存命中（未过期） → 返回缓存数据
        2. 否则调用 API 获取最新数据
        3. API 成功 → 保存到缓存并返回
        4. API 失败 → 降级到缓存数据（即使过期）

        Args:
            symbol: 股票代码（如 "600519.SH"）
            start_date: 开始日期（YYYYMMDD 或 YYYY-MM-DD）
            end_date: 结束日期（YYYYMMDD 或 YYYY-MM-DD）
            use_cache: 是否使用缓存

        Returns:
            {
                "data": DataFrame,
                "metadata": {
                    "source": "cache" | "api",
                    "api_source": "Tushare vX.X.X",
                    "retrieval_timestamp": datetime,
                    "data_freshness": "realtime" | "historical" | "stale",
                    "cache_hit": bool
                }
            }

        Raises:
            ValueError: 如果所有数据源都失败
        """
        # 标准化日期格式
        start_dt, end_dt = self._parse_dates(start_date, end_date)

        # 1. 尝试从缓存读取（如果启用）
        cache_hit = False
        cached_df = pd.DataFrame()

        if use_cache:
            cached_df = self.cache.get_from_cache(symbol, start_dt, end_dt)
            if not cached_df.empty:
                cache_hit = True
                return {
                    "data": cached_df,
                    "metadata": {
                        "source": "cache",
                        "api_source": cached_df['api_source'].iloc[0] if 'api_source' in cached_df else "Unknown",
                        "retrieval_timestamp": cached_df['retrieval_timestamp'].iloc[0],
                        "data_freshness": "historical",
                        "cache_hit": True
                    }
                }

        # 2. 缓存未命中，调用 API
        try:
            result = self.api_fetcher.fetch_with_fallback(
                symbol,
                start_dt.strftime('%Y%m%d'),
                end_dt.strftime('%Y%m%d')
            )

            df = result['data']
            api_source = result['metadata']['api_source']
            api_version = api_source.split('v')[-1] if 'v' in api_source else "unknown"

            # 保存到缓存（7天过期）
            if use_cache:
                self.cache.save_to_cache(symbol, df, api_source, api_version)

            return {
                "data": df,
                "metadata": {
                    "source": "api",
                    "api_source": api_source,
                    "retrieval_timestamp": result['metadata']['retrieval_timestamp'],
                    "data_freshness": result['metadata']['data_freshness'],
                    "cache_hit": False
                }
            }

        except Exception as api_error:
            # 3. API 失败，降级到过期缓存数据（如果有）
            print(f"API failed: {api_error}, attempting to use stale cache...")

            # 查询所有缓存数据（忽略过期时间）
            all_cached = self.session.query(MarketDataPoint).filter(
                MarketDataPoint.symbol == symbol,
                MarketDataPoint.timestamp >= start_dt,
                MarketDataPoint.timestamp <= end_dt
            ).order_by(MarketDataPoint.timestamp).all()

            if all_cached:
                # 转换为 DataFrame
                stale_data = []
                for record in all_cached:
                    stale_data.append({
                        'timestamp': record.timestamp,
                        'open': record.open_price,
                        'high': record.high_price,
                        'low': record.low_price,
                        'close': record.close_price,
                        'volume': record.volume,
                        'api_source': record.api_source,
                        'retrieval_timestamp': record.retrieval_timestamp
                    })

                stale_df = pd.DataFrame(stale_data)

                return {
                    "data": stale_df,
                    "metadata": {
                        "source": "stale_cache",
                        "api_source": stale_df['api_source'].iloc[0] if not stale_df.empty else "Unknown",
                        "retrieval_timestamp": stale_df['retrieval_timestamp'].iloc[0],
                        "data_freshness": "stale",
                        "cache_hit": True,
                        "warning": "Using stale cache data due to API failure"
                    }
                }

            # 4. 完全失败
            raise ValueError(f"All data sources failed for {symbol}: {api_error}")

    def cleanup_cache(self) -> int:
        """清理过期缓存。

        Returns:
            删除的记录数
        """
        return self.cache.cleanup_expired()

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存统计信息。

        Returns:
            缓存统计字典
        """
        return self.cache.get_cache_stats()

    def _parse_dates(self, start_date: Optional[str], end_date: Optional[str]):
        """解析并标准化日期。

        Args:
            start_date: 开始日期字符串
            end_date: 结束日期字符串

        Returns:
            (start_datetime, end_datetime)
        """
        if not start_date:
            start_dt = datetime.now() - timedelta(days=365)
        else:
            # 支持 YYYYMMDD 和 YYYY-MM-DD
            if '-' in start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_dt = datetime.strptime(start_date, '%Y%m%d')

        if not end_date:
            end_dt = datetime.now()
        else:
            if '-' in end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_dt = datetime.strptime(end_date, '%Y%m%d')

        return start_dt, end_dt


# 导入缺失的模型（修正）
from investlib_data.models import MarketDataPoint
