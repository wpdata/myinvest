"""Market data cache manager with 7-day retention."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from investlib_data.models import MarketDataPoint, DataFreshness, AdjustmentMethod
import pandas as pd


class CacheManager:
    """Manage market data cache with 7-day retention."""

    def __init__(self, session: Session):
        """Initialize cache manager.

        Args:
            session: SQLAlchemy session
        """
        import logging
        self.session = session
        self.logger = logging.getLogger(__name__)

    def save_to_cache(self, symbol: str, df: pd.DataFrame, api_source: str, api_version: str) -> int:
        """Save market data to cache with 7-day expiry.

        Args:
            symbol: Stock symbol
            df: DataFrame with OHLCV data
            api_source: API source string (e.g., "Tushare v1.2.85")
            api_version: API version

        Returns:
            Number of records saved
        """
        saved_count = 0

        for _, row in df.iterrows():
            # Convert timestamp to datetime if needed
            if isinstance(row['timestamp'], pd.Timestamp):
                timestamp = row['timestamp'].to_pydatetime()
            elif isinstance(row['timestamp'], str):
                # Try multiple date formats
                timestamp = None
                for fmt in ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d']:
                    try:
                        timestamp = datetime.strptime(row['timestamp'], fmt)
                        break
                    except ValueError:
                        continue
                if timestamp is None:
                    # If all formats fail, try pandas to_datetime as fallback
                    timestamp = pd.to_datetime(row['timestamp']).to_pydatetime()
            else:
                timestamp = row['timestamp']

            # Check if already exists (upsert logic)
            existing = self.session.query(MarketDataPoint).filter_by(
                symbol=symbol,
                timestamp=timestamp
            ).first()

            if existing:
                # Update existing record
                existing.open_price = float(row['open'])
                existing.high_price = float(row['high'])
                existing.low_price = float(row['low'])
                existing.close_price = float(row['close'])
                existing.volume = float(row['volume'])
                existing.retrieval_timestamp = datetime.utcnow()
                existing.cache_expiry_date = datetime.utcnow() + timedelta(days=7)
            else:
                # Create new record
                data_point = MarketDataPoint(
                    symbol=symbol,
                    timestamp=timestamp,
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=float(row['volume']),
                    api_source=api_source,
                    api_version=api_version,
                    retrieval_timestamp=datetime.utcnow(),
                    data_freshness=DataFreshness.HISTORICAL,  # Cached data is historical
                    adjustment_method=AdjustmentMethod.FORWARD,  # 前复权
                    cache_expiry_date=datetime.utcnow() + timedelta(days=7)
                )
                self.session.add(data_point)

            saved_count += 1

        self.session.commit()
        self.logger.info(f"[CacheManager] Saved {saved_count} records for {symbol} to cache (source: {api_source})")
        return saved_count

    def get_from_cache(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Retrieve market data from cache.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with cached data (empty if not found or expired)
        """
        now = datetime.utcnow()

        # Query cache with expiry check
        records = self.session.query(MarketDataPoint).filter(
            MarketDataPoint.symbol == symbol,
            MarketDataPoint.timestamp >= start_date,
            MarketDataPoint.timestamp <= end_date,
            MarketDataPoint.cache_expiry_date > now  # Not expired
        ).order_by(MarketDataPoint.timestamp).all()

        if not records:
            self.logger.warning(f"[CacheManager] Cache miss for {symbol} ({start_date} to {end_date})")
            return pd.DataFrame()

        self.logger.info(f"[CacheManager] ✅ Returning cached data for {symbol}, cached at {records[0].retrieval_timestamp}, rows={len(records)}")

        # Convert to DataFrame
        data = []
        for record in records:
            data.append({
                'timestamp': record.timestamp,
                'open': record.open_price,
                'high': record.high_price,
                'low': record.low_price,
                'close': record.close_price,
                'volume': record.volume,
                'api_source': record.api_source,
                'retrieval_timestamp': record.retrieval_timestamp,
                'data_freshness': 'historical'  # Cached data is historical
            })

        return pd.DataFrame(data)

    def cleanup_expired(self) -> int:
        """Delete expired cache entries.

        Returns:
            Number of records deleted
        """
        now = datetime.utcnow()

        deleted_count = self.session.query(MarketDataPoint).filter(
            MarketDataPoint.cache_expiry_date <= now
        ).delete()

        self.session.commit()
        self.logger.info(f"[CacheManager] Cleaned up {deleted_count} expired cache entries")
        return deleted_count

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache stats (total_records, expired_records, symbols)
        """
        now = datetime.utcnow()

        total = self.session.query(MarketDataPoint).count()
        expired = self.session.query(MarketDataPoint).filter(
            MarketDataPoint.cache_expiry_date <= now
        ).count()

        symbols = self.session.query(MarketDataPoint.symbol).distinct().count()

        return {
            'total_records': total,
            'expired_records': expired,
            'active_records': total - expired,
            'unique_symbols': symbols
        }
