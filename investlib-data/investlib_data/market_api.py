"""Market data API wrappers for Efinance and AKShare."""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd


class EfinanceAPIError(Exception):
    """Efinance API error."""
    pass


class AKShareAPIError(Exception):
    """AKShare API error."""
    pass


class ETFAPIError(Exception):
    """ETF API error."""
    pass


class IndexAPIError(Exception):
    """Index API error."""
    pass


class FuturesAPIError(Exception):
    """Futures API error."""
    pass


class OptionsAPIError(Exception):
    """Options API error."""
    pass


class EfinanceClient:
    """Efinance API client - free, no token required."""

    def __init__(self):
        """Initialize Efinance client."""
        import logging
        import os
        self.logger = logging.getLogger(__name__)

        # Disable proxy for API calls (avoid proxy connection issues)
        # Save original proxy settings
        self._original_proxy = {
            'http_proxy': os.environ.get('http_proxy'),
            'https_proxy': os.environ.get('https_proxy'),
            'HTTP_PROXY': os.environ.get('HTTP_PROXY'),
            'HTTPS_PROXY': os.environ.get('HTTPS_PROXY'),
        }

        # Remove proxy environment variables
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
            if key in os.environ:
                del os.environ[key]

        self.logger.info("[EfinanceClient] Disabled proxy for API calls")

        try:
            import efinance as ef
            self.ef = ef
            # Try to get version, efinance may not have __version__
            try:
                self.version = ef.__version__
            except AttributeError:
                self.version = "latest"
            self.logger.info(f"[EfinanceClient] Initialized with version {self.version}")
        except ImportError:
            raise EfinanceAPIError("efinance package not installed. Run: pip install efinance")

    def fetch_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        retries: int = 3
    ) -> pd.DataFrame:
        """Fetch daily OHLCV data with metadata.

        Args:
            symbol: Stock symbol (e.g., '600519.SH' or '600519')
            start_date: Start date in YYYYMMDD or YYYY-MM-DD format
            end_date: End date in YYYYMMDD or YYYY-MM-DD format
            retries: Number of retry attempts

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, metadata

        Raises:
            EfinanceAPIError: If fetch fails after retries
        """
        import os

        # CRITICAL: Disable proxy before EVERY API call
        # Save current proxy settings
        saved_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            saved_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        # Set NO_PROXY to bypass proxy for all hosts
        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'

        try:
            # Convert symbol format: 600519.SH -> 600519
            clean_symbol = symbol.split('.')[0]

            # Keep date in YYYYMMDD format (efinance requires this format)
            # Convert from YYYY-MM-DD to YYYYMMDD if needed
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')

            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            for attempt in range(retries):
                try:
                    self.logger.info(f"[EfinanceClient] Fetching {symbol} (attempt {attempt + 1}/{retries})")

                    # Fetch data using efinance
                    # klt=101 means daily data
                    try:
                        df = self.ef.stock.get_quote_history(
                            stock_codes=clean_symbol,
                            beg=start_date,
                            end=end_date,
                            klt=101  # Daily data
                        )
                    except Exception as api_error:
                        # Catch JSON parsing errors and other API-level errors
                        error_msg = str(api_error)
                        if "Expecting value" in error_msg or "JSONDecodeError" in str(type(api_error)):
                            raise EfinanceAPIError(f"API returned invalid JSON (possible rate limit or service issue): {error_msg}")
                        raise EfinanceAPIError(f"API call failed: {error_msg}")

                    if df is None or df.empty:
                        raise EfinanceAPIError(f"No data returned for {symbol} (API may be down or rate limited)")

                    # Add metadata
                    retrieval_timestamp = datetime.utcnow()
                    df['api_source'] = f"Efinance v{self.version}"
                    df['api_version'] = self.version
                    df['retrieval_timestamp'] = retrieval_timestamp
                    df['data_freshness'] = 'realtime'  # Assume fresh on success

                    # Rename columns to standard format
                    # Efinance columns: 股票名称, 股票代码, 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
                    column_mapping = {
                        '日期': 'timestamp',
                        '开盘': 'open',
                        '最高': 'high',
                        '最低': 'low',
                        '收盘': 'close',
                        '成交量': 'volume',
                        '股票代码': 'symbol',
                        '股票名称': 'name'
                    }

                    # Only rename columns that exist
                    existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
                    df = df.rename(columns=existing_columns)

                    # Ensure required columns exist
                    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        raise EfinanceAPIError(f"Missing required columns: {missing_cols}")

                    self.logger.info(f"[EfinanceClient] ✅ Fetched {symbol} from Efinance at {retrieval_timestamp.strftime('%Y-%m-%d %H:%M:%S')}, rows={len(df)}")
                    return df

                except Exception as e:
                    self.logger.warning(f"[EfinanceClient] ❌ Attempt {attempt + 1} failed for {symbol}: {e}")
                    if attempt < retries - 1:
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        self.logger.info(f"[EfinanceClient] Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"[EfinanceClient] ❌ Failed after {retries} attempts for {symbol}")
                        raise EfinanceAPIError(f"Failed after {retries} attempts: {e}")

            raise EfinanceAPIError("Unexpected retry loop exit")
        finally:
            # Restore original proxy settings
            for key, value in saved_proxy.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class AKShareClient:
    """AKShare API client (fallback)."""

    def __init__(self):
        """Initialize AKShare client."""
        import logging
        import os
        self.logger = logging.getLogger(__name__)

        # Disable proxy for API calls (avoid proxy connection issues)
        # Save original proxy settings
        self._original_proxy = {
            'http_proxy': os.environ.get('http_proxy'),
            'https_proxy': os.environ.get('https_proxy'),
            'HTTP_PROXY': os.environ.get('HTTP_PROXY'),
            'HTTPS_PROXY': os.environ.get('HTTPS_PROXY'),
        }

        # Remove proxy environment variables
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
            if key in os.environ:
                del os.environ[key]

        self.logger.info("[AKShareClient] Disabled proxy for API calls")

        try:
            import akshare as ak
            self.ak = ak
            self.version = ak.__version__
            self.logger.info(f"[AKShareClient] Initialized with version {self.version}")

            # Fix SSL certificate verification issues on macOS
            # Disable SSL warnings (AKShare uses requests library internally)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Set environment variable to disable SSL verification
            # This is needed because AKShare doesn't expose SSL config
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            self.logger.info("[AKShareClient] SSL verification disabled (workaround for macOS)")

        except ImportError:
            raise AKShareAPIError("akshare package not installed")

    def fetch_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        retries: int = 3
    ) -> pd.DataFrame:
        """Fetch daily OHLCV data with metadata.

        Args:
            symbol: Stock symbol (e.g., '600519' for Shanghai stocks)
            start_date: Start date in YYYYMMDD or YYYY-MM-DD format
            end_date: End date in YYYYMMDD or YYYY-MM-DD format
            retries: Number of retry attempts

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, metadata

        Raises:
            AKShareAPIError: If fetch fails after retries
        """
        import os

        # CRITICAL: Disable proxy before EVERY API call
        # Save current proxy settings
        saved_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            saved_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        # Set NO_PROXY to bypass proxy for all hosts
        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'

        try:
            # Convert symbol format: 600519.SH -> 600519
            clean_symbol = symbol.split('.')[0]

            # Convert date format to YYYYMMDD (AKShare requires this format)
            # From YYYY-MM-DD to YYYYMMDD if needed
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')

            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            for attempt in range(retries):
                try:
                    self.logger.info(f"[AKShareClient] Fetching {symbol} (attempt {attempt + 1}/{retries})")

                    # Fetch data (adjust='qfq' means 前复权 - forward adjusted)
                    df = self.ak.stock_zh_a_hist(
                        symbol=clean_symbol,
                        period='daily',
                        start_date=start_date,
                        end_date=end_date,
                        adjust='qfq'
                    )

                    if df is None or df.empty:
                        raise AKShareAPIError(f"No data returned for {symbol}")

                    # Add metadata
                    retrieval_timestamp = datetime.utcnow()
                    df['api_source'] = f"AKShare v{self.version}"
                    df['api_version'] = self.version
                    df['retrieval_timestamp'] = retrieval_timestamp
                    df['data_freshness'] = 'realtime'

                    # Rename columns to standard format
                    df = df.rename(columns={
                        '日期': 'timestamp',
                        '开盘': 'open',
                        '最高': 'high',
                        '最低': 'low',
                        '收盘': 'close',
                        '成交量': 'volume'
                    })

                    self.logger.info(f"[AKShareClient] ✅ Fetched {symbol} from AKShare at {retrieval_timestamp.strftime('%Y-%m-%d %H:%M:%S')}, rows={len(df)}")
                    return df

                except Exception as e:
                    self.logger.warning(f"[AKShareClient] ❌ Attempt {attempt + 1} failed for {symbol}: {e}")
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"[AKShareClient] Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"[AKShareClient] ❌ Failed after {retries} attempts for {symbol}")
                        raise AKShareAPIError(f"Failed after {retries} attempts: {e}")

            raise AKShareAPIError("Unexpected retry loop exit")
        finally:
            # Restore original proxy settings
            for key, value in saved_proxy.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class ETFClient:
    """ETF data client using AKShare."""

    def __init__(self):
        """Initialize ETF client."""
        import logging
        import os
        self.logger = logging.getLogger(__name__)

        # Disable proxy
        self._original_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            self._original_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        self.logger.info("[ETFClient] Disabled proxy for API calls")

        try:
            import akshare as ak
            self.ak = ak
            self.version = ak.__version__
            self.logger.info(f"[ETFClient] Initialized with AKShare version {self.version}")

            # SSL fix
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            self.logger.info("[ETFClient] SSL verification disabled")

        except ImportError:
            raise ETFAPIError("akshare package not installed")

    def fetch_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        retries: int = 3
    ) -> pd.DataFrame:
        """Fetch ETF daily data.

        Args:
            symbol: ETF code (e.g., '510300' for 510300.SH)
            start_date: Start date (YYYYMMDD or YYYY-MM-DD)
            end_date: End date (YYYYMMDD or YYYY-MM-DD)
            retries: Number of retry attempts

        Returns:
            DataFrame with OHLCV data

        Raises:
            ETFAPIError: If fetch fails after retries
        """
        import os

        # Disable proxy before each call
        saved_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            saved_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'

        try:
            # Convert symbol format: 510300.SH -> 510300
            clean_symbol = symbol.split('.')[0]

            # Convert date format to YYYYMMDD
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')

            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            for attempt in range(retries):
                try:
                    self.logger.info(f"[ETFClient] Fetching {symbol} (attempt {attempt + 1}/{retries})")

                    # Fetch ETF data using AKShare
                    df = self.ak.fund_etf_hist_em(
                        symbol=clean_symbol,
                        period='daily',
                        start_date=start_date,
                        end_date=end_date,
                        adjust='qfq'
                    )

                    if df is None or df.empty:
                        raise ETFAPIError(f"No data returned for {symbol}")

                    # Add metadata
                    retrieval_timestamp = datetime.utcnow()
                    df['api_source'] = f"ETF (AKShare v{self.version})"
                    df['api_version'] = self.version
                    df['retrieval_timestamp'] = retrieval_timestamp
                    df['data_freshness'] = 'realtime'

                    # Rename columns to standard format
                    df = df.rename(columns={
                        '日期': 'timestamp',
                        '开盘': 'open',
                        '最高': 'high',
                        '最低': 'low',
                        '收盘': 'close',
                        '成交量': 'volume'
                    })

                    self.logger.info(f"[ETFClient] ✅ Fetched {symbol} from ETF API, rows={len(df)}")
                    return df

                except Exception as e:
                    self.logger.warning(f"[ETFClient] ❌ Attempt {attempt + 1} failed for {symbol}: {e}")
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"[ETFClient] Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"[ETFClient] ❌ Failed after {retries} attempts for {symbol}")
                        raise ETFAPIError(f"Failed after {retries} attempts: {e}")

            raise ETFAPIError("Unexpected retry loop exit")
        finally:
            # Restore proxy settings
            for key, value in saved_proxy.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class IndexClient:
    """Index data client using AKShare."""

    def __init__(self):
        """Initialize Index client."""
        import logging
        import os
        self.logger = logging.getLogger(__name__)

        # Disable proxy
        self._original_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            self._original_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        self.logger.info("[IndexClient] Disabled proxy for API calls")

        try:
            import akshare as ak
            self.ak = ak
            self.version = ak.__version__
            self.logger.info(f"[IndexClient] Initialized with AKShare version {self.version}")

            # SSL fix
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            self.logger.info("[IndexClient] SSL verification disabled")

        except ImportError:
            raise IndexAPIError("akshare package not installed")

    def fetch_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        retries: int = 3
    ) -> pd.DataFrame:
        """Fetch index daily data.

        Args:
            symbol: Index code (e.g., '000001' for 000001.SH)
            start_date: Start date (YYYYMMDD or YYYY-MM-DD)
            end_date: End date (YYYYMMDD or YYYY-MM-DD)
            retries: Number of retry attempts

        Returns:
            DataFrame with OHLCV data

        Raises:
            IndexAPIError: If fetch fails after retries
        """
        import os

        # Disable proxy before each call
        saved_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            saved_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'

        try:
            # Convert symbol format: 000001.SH -> sh000001, 399001.SZ -> sz399001
            clean_symbol = symbol.split('.')[0]
            if symbol.endswith('.SH'):
                # Shanghai index: add 'sh' prefix
                full_symbol = f"sh{clean_symbol}"
            elif symbol.endswith('.SZ'):
                # Shenzhen index: add 'sz' prefix
                full_symbol = f"sz{clean_symbol}"
            else:
                full_symbol = clean_symbol

            # Convert date format to YYYYMMDD
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')

            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            for attempt in range(retries):
                try:
                    self.logger.info(f"[IndexClient] Fetching {symbol} (attempt {attempt + 1}/{retries})")

                    # Fetch index data using AKShare
                    df = self.ak.index_zh_a_hist(
                        symbol=full_symbol,
                        period='daily',
                        start_date=start_date,
                        end_date=end_date
                    )

                    if df is None or df.empty:
                        raise IndexAPIError(f"No data returned for {symbol}")

                    # Add metadata
                    retrieval_timestamp = datetime.utcnow()
                    df['api_source'] = f"Index (AKShare v{self.version})"
                    df['api_version'] = self.version
                    df['retrieval_timestamp'] = retrieval_timestamp
                    df['data_freshness'] = 'realtime'

                    # Rename columns to standard format
                    df = df.rename(columns={
                        '日期': 'timestamp',
                        '开盘': 'open',
                        '最高': 'high',
                        '最低': 'low',
                        '收盘': 'close',
                        '成交量': 'volume',
                        '成交额': 'amount'
                    })

                    self.logger.info(f"[IndexClient] ✅ Fetched {symbol} from Index API, rows={len(df)}")
                    return df

                except Exception as e:
                    self.logger.warning(f"[IndexClient] ❌ Attempt {attempt + 1} failed for {symbol}: {e}")
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"[IndexClient] Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"[IndexClient] ❌ Failed after {retries} attempts for {symbol}")
                        raise IndexAPIError(f"Failed after {retries} attempts: {e}")

            raise IndexAPIError("Unexpected retry loop exit")
        finally:
            # Restore proxy settings
            for key, value in saved_proxy.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class FuturesClient:
    """Futures data client using AKShare."""

    def __init__(self):
        """Initialize Futures client."""
        import logging
        import os
        self.logger = logging.getLogger(__name__)

        # Disable proxy
        self._original_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            self._original_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        self.logger.info("[FuturesClient] Disabled proxy for API calls")

        try:
            import akshare as ak
            self.ak = ak
            self.version = ak.__version__
            self.logger.info(f"[FuturesClient] Initialized with AKShare version {self.version}")

            # SSL fix
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            self.logger.info("[FuturesClient] SSL verification disabled")

        except ImportError:
            raise FuturesAPIError("akshare package not installed")

    def fetch_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        retries: int = 3
    ) -> pd.DataFrame:
        """Fetch futures daily data.

        Args:
            symbol: Futures code (e.g., 'IF2506.CFFEX')
            start_date: Start date (YYYYMMDD or YYYY-MM-DD)
            end_date: End date (YYYYMMDD or YYYY-MM-DD)
            retries: Number of retry attempts

        Returns:
            DataFrame with OHLCV data

        Raises:
            FuturesAPIError: If fetch fails after retries
        """
        import os

        # Disable proxy before each call
        saved_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            saved_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'

        try:
            # Parse symbol: IF2506.CFFEX -> IF2506
            clean_symbol = symbol.split('.')[0].upper()

            # Convert date format to YYYYMMDD
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')

            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            for attempt in range(retries):
                try:
                    self.logger.info(f"[FuturesClient] Fetching {symbol} (attempt {attempt + 1}/{retries})")

                    # Fetch futures data using AKShare
                    # Use futures_zh_daily_sina for daily data
                    df = self.ak.futures_zh_daily_sina(symbol=clean_symbol)

                    if df is None or df.empty:
                        raise FuturesAPIError(f"No data returned for {symbol}")

                    # Add metadata
                    retrieval_timestamp = datetime.utcnow()
                    df['api_source'] = f"Futures (AKShare v{self.version})"
                    df['api_version'] = self.version
                    df['retrieval_timestamp'] = retrieval_timestamp
                    df['data_freshness'] = 'realtime'

                    # Rename columns to standard format
                    df = df.rename(columns={
                        'date': 'timestamp',
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'volume': 'volume',
                        'hold': 'open_interest'  # Futures-specific
                    })

                    self.logger.info(f"[FuturesClient] ✅ Fetched {symbol} from Futures API, rows={len(df)}")
                    return df

                except Exception as e:
                    self.logger.warning(f"[FuturesClient] ❌ Attempt {attempt + 1} failed for {symbol}: {e}")
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"[FuturesClient] Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"[FuturesClient] ❌ Failed after {retries} attempts for {symbol}")
                        raise FuturesAPIError(f"Failed after {retries} attempts: {e}")

            raise FuturesAPIError("Unexpected retry loop exit")
        finally:
            # Restore proxy settings
            for key, value in saved_proxy.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class OptionsClient:
    """Options data client using AKShare."""

    def __init__(self):
        """Initialize Options client."""
        import logging
        import os
        self.logger = logging.getLogger(__name__)

        # Disable proxy
        self._original_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            self._original_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        self.logger.info("[OptionsClient] Disabled proxy for API calls")

        try:
            import akshare as ak
            self.ak = ak
            self.version = ak.__version__
            self.logger.info(f"[OptionsClient] Initialized with AKShare version {self.version}")

            # SSL fix
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            self.logger.info("[OptionsClient] SSL verification disabled")

        except ImportError:
            raise OptionsAPIError("akshare package not installed")

    def fetch_daily_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        retries: int = 3
    ) -> pd.DataFrame:
        """Fetch options daily data.

        Args:
            symbol: Options code (e.g., '10005102.SH' for 50ETF option)
            start_date: Start date (YYYYMMDD or YYYY-MM-DD)
            end_date: End date (YYYYMMDD or YYYY-MM-DD)
            retries: Number of retry attempts

        Returns:
            DataFrame with OHLCV data

        Raises:
            OptionsAPIError: If fetch fails after retries
        """
        import os

        # Disable proxy before each call
        saved_proxy = {}
        for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
            saved_proxy[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'

        try:
            # Parse symbol: 10005102.SH -> 10005102
            clean_symbol = symbol.split('.')[0]

            # Convert date format to YYYYMMDD
            if start_date and '-' in start_date:
                start_date = start_date.replace('-', '')
            if end_date and '-' in end_date:
                end_date = end_date.replace('-', '')

            if not start_date:
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')  # Shorter for options
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            for attempt in range(retries):
                try:
                    self.logger.info(f"[OptionsClient] Fetching {symbol} (attempt {attempt + 1}/{retries})")

                    # Fetch options data using AKShare
                    # Use option_finance_minute_em for options data
                    df = self.ak.option_finance_board(symbol=clean_symbol)

                    if df is None or df.empty:
                        raise OptionsAPIError(f"No data returned for {symbol}")

                    # Add metadata
                    retrieval_timestamp = datetime.utcnow()
                    df['api_source'] = f"Options (AKShare v{self.version})"
                    df['api_version'] = self.version
                    df['retrieval_timestamp'] = retrieval_timestamp
                    df['data_freshness'] = 'realtime'

                    # Add timestamp column if not present
                    if 'timestamp' not in df.columns:
                        df['timestamp'] = datetime.now().strftime('%Y-%m-%d')

                    self.logger.info(f"[OptionsClient] ✅ Fetched {symbol} from Options API, rows={len(df)}")
                    return df

                except Exception as e:
                    self.logger.warning(f"[OptionsClient] ❌ Attempt {attempt + 1} failed for {symbol}: {e}")
                    if attempt < retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"[OptionsClient] Retrying in {wait_time}s...")
                        import time
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"[OptionsClient] ❌ Failed after {retries} attempts for {symbol}")
                        raise OptionsAPIError(f"Failed after {retries} attempts: {e}")

            raise OptionsAPIError("Unexpected retry loop exit")
        finally:
            # Restore proxy settings
            for key, value in saved_proxy.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class NoDataAvailableError(Exception):
    """Raised when no data source is available."""
    pass


class MarketDataFetcher:
    """Unified market data fetcher with retry and fallback logic.

    Fallback chain: Efinance → AKShare → Cache
    """

    def __init__(self, cache_manager=None):
        """Initialize fetcher with multi-source support.

        Args:
            cache_manager: Optional CacheManager instance. If None, cache fallback is disabled.
        """
        self.efinance = None
        self.akshare = None
        self.etf = None
        self.index = None
        self.futures = None
        self.options = None
        self.cache_manager = cache_manager

        # Try to initialize Efinance as primary (for stocks)
        try:
            self.efinance = EfinanceClient()
        except Exception:
            pass  # Efinance not available

        # Try to initialize AKShare as fallback (for stocks)
        try:
            self.akshare = AKShareClient()
        except Exception:
            pass  # AKShare not available

        # Try to initialize ETF client
        try:
            self.etf = ETFClient()
        except Exception:
            pass  # ETF not available

        # Try to initialize Index client
        try:
            self.index = IndexClient()
        except Exception:
            pass  # Index not available

        # Try to initialize Futures client
        try:
            self.futures = FuturesClient()
        except Exception:
            pass  # Futures not available

        # Try to initialize Options client
        try:
            self.options = OptionsClient()
        except Exception:
            pass  # Options not available

        if not any([self.efinance, self.akshare, self.etf, self.index, self.futures, self.options, self.cache_manager]):
            raise RuntimeError("No market data source available (no API and no cache)")

    def _calculate_data_freshness(self, retrieval_timestamp: datetime) -> str:
        """Calculate data freshness based on time elapsed.

        Args:
            retrieval_timestamp: When the data was retrieved

        Returns:
            'realtime' (<5s), 'delayed' (5s-15min), or 'historical' (>15min)
        """
        time_elapsed = (datetime.utcnow() - retrieval_timestamp).total_seconds()

        if time_elapsed < 5:
            return 'realtime'
        elif time_elapsed <= 900:  # 15 minutes
            return 'delayed'
        else:
            return 'historical'

    def fetch_with_fallback(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        prefer_cache: bool = False
    ) -> Dict[str, Any]:
        """Fetch market data with automatic fallback.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD or YYYYMMDD)
            end_date: End date (YYYY-MM-DD or YYYYMMDD)
            prefer_cache: If True, try cache FIRST (for backtesting). Default False (for live trading).

        Returns:
            Dict with 'data' (DataFrame) and 'metadata' (dict with api_source, retrieval_timestamp, data_freshness)

        Raises:
            NoDataAvailableError: If all sources fail (APIs + cache)

        Fallback Strategy:
            - If prefer_cache=True (backtest): Cache → Efinance → AKShare
            - If prefer_cache=False (live): Efinance → AKShare → Cache
        """
        import logging
        logger = logging.getLogger(__name__)

        # Auto-route based on symbol type
        try:
            from investlib_data.multi_asset_api import detect_asset_type
            asset_type = detect_asset_type(symbol)
        except ImportError:
            # Fallback to old detection
            from investlib_data.symbol_validator import detect_symbol_type
            symbol_type = detect_symbol_type(symbol)
            # Map old types to new types
            if symbol_type == 'etf':
                asset_type = 'etf'
            elif symbol_type == 'index':
                asset_type = 'index'
            else:
                asset_type = 'stock'

        logger.info(f"[MarketDataFetcher] Symbol {symbol} detected as type: {asset_type}")

        # Route to appropriate client based on asset type
        if asset_type == 'futures':
            # Futures: use FuturesClient
            return self._fetch_futures_data(symbol, start_date, end_date, prefer_cache, logger)
        elif asset_type == 'option':
            # Options: use OptionsClient
            return self._fetch_options_data(symbol, start_date, end_date, prefer_cache, logger)
        elif asset_type == 'etf':
            # ETF: use ETFClient only
            return self._fetch_etf_data(symbol, start_date, end_date, prefer_cache, logger)
        elif asset_type == 'index':
            # Index: use IndexClient only
            return self._fetch_index_data(symbol, start_date, end_date, prefer_cache, logger)
        else:
            # Stock: use Efinance → AKShare fallback
            return self._fetch_stock_data(symbol, start_date, end_date, prefer_cache, logger)

    def _fetch_stock_data(
        self,
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        prefer_cache: bool,
        logger
    ) -> Dict[str, Any]:
        """Fetch stock data with Efinance → AKShare → Cache fallback."""

        # BACKTEST MODE: Try cache first to avoid API rate limits
        if prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache first (prefer_cache=True) for {symbol}")

                # Parse dates for cache query
                if start_date:
                    if len(start_date) == 8 and '-' not in start_date:
                        start_dt = datetime.strptime(start_date, '%Y%m%d')
                    else:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    if len(end_date) == 8 and '-' not in end_date:
                        end_dt = datetime.strptime(end_date, '%Y%m%d')
                    else:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for {symbol}, rows={len(df)} (prefer_cache mode)")

                    # Get retrieval timestamp from cached data
                    if 'retrieval_timestamp' in df.columns and len(df) > 0:
                        retrieval_timestamp = df.iloc[0]['retrieval_timestamp']
                        if isinstance(retrieval_timestamp, str):
                            retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)
                    else:
                        retrieval_timestamp = datetime.utcnow() - timedelta(hours=1)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (unknown source)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
                else:
                    logger.info(f"[MarketDataFetcher] Cache miss for {symbol}, falling back to APIs")
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] Cache failed for {symbol}: {e}, falling back to APIs")

        # Try Level 1: Efinance
        if self.efinance:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Efinance for {symbol}")
                df = self.efinance.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ Efinance succeeded for {symbol}, rows={len(df)}, freshness={data_freshness}")

                # Save to cache if available
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(
                            symbol, df,
                            f"Efinance v{self.efinance.version}",
                            self.efinance.version
                        )
                    except Exception as cache_error:
                        logger.warning(f"Failed to save to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"Efinance v{self.efinance.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ Efinance failed for {symbol}: {e}")

        # Try Level 2: AKShare
        if self.akshare:
            try:
                logger.info(f"[MarketDataFetcher] Attempting AKShare for {symbol}")
                df = self.akshare.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ AKShare succeeded for {symbol}, rows={len(df)}, freshness={data_freshness}")

                # Save to cache if available
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(
                            symbol, df,
                            f"AKShare v{self.akshare.version}",
                            self.akshare.version
                        )
                    except Exception as cache_error:
                        logger.warning(f"Failed to save to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"AKShare v{self.akshare.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ AKShare failed for {symbol}: {e}")

        # Try Level 3: Cache (last resort)
        if self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache for {symbol}")

                # Parse dates for cache query
                if start_date:
                    if len(start_date) == 8 and '-' not in start_date:
                        start_dt = datetime.strptime(start_date, '%Y%m%d')
                    else:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    if len(end_date) == 8 and '-' not in end_date:
                        end_dt = datetime.strptime(end_date, '%Y%m%d')
                    else:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for {symbol}, rows={len(df)}")
                    logger.warning(f"[MarketDataFetcher] ⚠️ Using cached data for {symbol} (all APIs failed)")

                    # Get retrieval timestamp from cached data
                    if 'retrieval_timestamp' in df.columns and len(df) > 0:
                        retrieval_timestamp = df.iloc[0]['retrieval_timestamp']
                        if isinstance(retrieval_timestamp, str):
                            retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)
                    else:
                        retrieval_timestamp = datetime.utcnow() - timedelta(hours=1)  # Assume old

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                    # Get api_source from cache
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (unknown source)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
                else:
                    logger.error(f"[MarketDataFetcher] ❌ Cache miss for {symbol}")
            except Exception as e:
                logger.error(f"[MarketDataFetcher] ❌ Cache failed for {symbol}: {e}")

        # All sources failed
        logger.error(f"[MarketDataFetcher] ❌ ALL SOURCES FAILED for {symbol}")
        raise NoDataAvailableError(f"All data sources failed for symbol {symbol} (Efinance, AKShare, Cache)")

    def _fetch_etf_data(
        self,
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        prefer_cache: bool,
        logger
    ) -> Dict[str, Any]:
        """Fetch ETF data with Efinance → AKShare (ETFClient) → Cache fallback.

        Note: ETFs are also traded on exchanges, so Efinance can handle them too.
        We try Efinance first (faster, more reliable), then fall back to specialized ETF API.
        """

        # Try cache first if prefer_cache=True
        if prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache first (prefer_cache=True) for ETF {symbol}")

                # Parse dates
                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if '-' in start_date or len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if '-' in end_date or len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for ETF {symbol}, rows={len(df)}")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (ETF)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] Cache failed for ETF {symbol}: {e}")

        # Try Level 1: Efinance (works for ETFs too!)
        if self.efinance:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Efinance for ETF {symbol}")
                df = self.efinance.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ Efinance succeeded for ETF {symbol}, rows={len(df)}")

                # Save to cache
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(symbol, df, f"Efinance (ETF) v{self.efinance.version}", self.efinance.version)
                    except Exception as cache_error:
                        logger.warning(f"Failed to save ETF data to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"Efinance (ETF) v{self.efinance.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ Efinance failed for ETF {symbol}: {e}")

        # Try Level 2: ETFClient (specialized AKShare API)
        if self.etf:
            try:
                logger.info(f"[MarketDataFetcher] Attempting ETFClient (AKShare) for {symbol}")
                df = self.etf.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ ETFClient succeeded for {symbol}, rows={len(df)}")

                # Save to cache
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(symbol, df, f"AKShare (ETF) v{self.etf.version}", self.etf.version)
                    except Exception as cache_error:
                        logger.warning(f"Failed to save ETF data to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"AKShare (ETF) v{self.etf.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ ETFClient failed for {symbol}: {e}")

        # Try Level 3: Cache as last resort
        if not prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache as last resort for ETF {symbol}")

                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for ETF {symbol}, rows={len(df)}")
                    logger.warning(f"[MarketDataFetcher] ⚠️ Using cached data for ETF {symbol} (all APIs failed)")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (ETF)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.error(f"[MarketDataFetcher] ❌ Cache failed for ETF {symbol}: {e}")

        # All sources failed for ETF
        logger.error(f"[MarketDataFetcher] ❌ ALL SOURCES FAILED for ETF {symbol}")
        raise NoDataAvailableError(f"All data sources failed for ETF {symbol}")

    def _fetch_index_data(
        self,
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        prefer_cache: bool,
        logger
    ) -> Dict[str, Any]:
        """Fetch Index data with Efinance → AKShare (IndexClient) → Cache fallback.

        Note: Indexes are also traded on exchanges, so Efinance can handle them too.
        We try Efinance first (faster, more reliable), then fall back to specialized Index API.
        """

        # Try cache first if prefer_cache=True
        if prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache first (prefer_cache=True) for Index {symbol}")

                # Parse dates
                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for Index {symbol}, rows={len(df)}")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (Index)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] Cache failed for Index {symbol}: {e}")

        # Try Level 1: Efinance (works for Indexes too!)
        if self.efinance:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Efinance for Index {symbol}")
                df = self.efinance.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ Efinance succeeded for Index {symbol}, rows={len(df)}")

                # Save to cache
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(symbol, df, f"Efinance (Index) v{self.efinance.version}", self.efinance.version)
                    except Exception as cache_error:
                        logger.warning(f"Failed to save Index data to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"Efinance (Index) v{self.efinance.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ Efinance failed for Index {symbol}: {e}")

        # Try Level 2: IndexClient (specialized AKShare API)
        if self.index:
            try:
                logger.info(f"[MarketDataFetcher] Attempting IndexClient (AKShare) for {symbol}")
                df = self.index.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ IndexClient succeeded for {symbol}, rows={len(df)}")

                # Save to cache
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(symbol, df, f"AKShare (Index) v{self.index.version}", self.index.version)
                    except Exception as cache_error:
                        logger.warning(f"Failed to save Index data to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"AKShare (Index) v{self.index.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ IndexClient failed for {symbol}: {e}")

        # Try Level 3: Cache as last resort
        if not prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache as last resort for Index {symbol}")

                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for Index {symbol}, rows={len(df)}")
                    logger.warning(f"[MarketDataFetcher] ⚠️ Using cached data for Index {symbol} (all APIs failed)")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (Index)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.error(f"[MarketDataFetcher] ❌ Cache failed for Index {symbol}: {e}")

        # All sources failed for Index
        logger.error(f"[MarketDataFetcher] ❌ ALL SOURCES FAILED for Index {symbol}")
        raise NoDataAvailableError(f"All data sources failed for Index {symbol}")

    def _fetch_futures_data(
        self,
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        prefer_cache: bool,
        logger
    ) -> Dict[str, Any]:
        """Fetch Futures data with FuturesClient → Cache fallback."""

        # Try cache first if prefer_cache=True
        if prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache first (prefer_cache=True) for Futures {symbol}")

                # Parse dates
                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for Futures {symbol}, rows={len(df)}")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (Futures)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] Cache failed for Futures {symbol}: {e}")

        # Try Level 1: FuturesClient
        if self.futures:
            try:
                logger.info(f"[MarketDataFetcher] Attempting FuturesClient for {symbol}")
                df = self.futures.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ FuturesClient succeeded for {symbol}, rows={len(df)}")

                # Save to cache
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(symbol, df, f"AKShare (Futures) v{self.futures.version}", self.futures.version)
                    except Exception as cache_error:
                        logger.warning(f"Failed to save Futures data to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"AKShare (Futures) v{self.futures.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ FuturesClient failed for {symbol}: {e}")

        # Try Level 2: Cache as last resort
        if not prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache as last resort for Futures {symbol}")

                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=365)

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for Futures {symbol}, rows={len(df)}")
                    logger.warning(f"[MarketDataFetcher] ⚠️ Using cached data for Futures {symbol} (API failed)")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (Futures)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.error(f"[MarketDataFetcher] ❌ Cache failed for Futures {symbol}: {e}")

        # All sources failed for Futures
        logger.error(f"[MarketDataFetcher] ❌ ALL SOURCES FAILED for Futures {symbol}")
        raise NoDataAvailableError(f"All data sources failed for Futures {symbol}")

    def _fetch_options_data(
        self,
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        prefer_cache: bool,
        logger
    ) -> Dict[str, Any]:
        """Fetch Options data with OptionsClient → Cache fallback."""

        # Try cache first if prefer_cache=True
        if prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache first (prefer_cache=True) for Options {symbol}")

                # Parse dates
                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=90)  # Shorter for options

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for Options {symbol}, rows={len(df)}")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (Options)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] Cache failed for Options {symbol}: {e}")

        # Try Level 1: OptionsClient
        if self.options:
            try:
                logger.info(f"[MarketDataFetcher] Attempting OptionsClient for {symbol}")
                df = self.options.fetch_daily_data(symbol, start_date, end_date)
                retrieval_timestamp = datetime.utcnow()
                data_freshness = self._calculate_data_freshness(retrieval_timestamp)

                logger.info(f"[MarketDataFetcher] ✅ OptionsClient succeeded for {symbol}, rows={len(df)}")

                # Save to cache
                if self.cache_manager:
                    try:
                        self.cache_manager.save_to_cache(symbol, df, f"AKShare (Options) v{self.options.version}", self.options.version)
                    except Exception as cache_error:
                        logger.warning(f"Failed to save Options data to cache: {cache_error}")

                return {
                    'data': df,
                    'metadata': {
                        'api_source': f"AKShare (Options) v{self.options.version}",
                        'retrieval_timestamp': retrieval_timestamp,
                        'data_freshness': data_freshness
                    }
                }
            except Exception as e:
                logger.warning(f"[MarketDataFetcher] ❌ OptionsClient failed for {symbol}: {e}")

        # Try Level 2: Cache as last resort
        if not prefer_cache and self.cache_manager:
            try:
                logger.info(f"[MarketDataFetcher] Attempting Cache as last resort for Options {symbol}")

                if start_date:
                    start_dt = datetime.strptime(start_date.replace('-', ''), '%Y%m%d') if len(start_date) == 8 else datetime.strptime(start_date, '%Y-%m-%d')
                else:
                    start_dt = datetime.now() - timedelta(days=90)

                if end_date:
                    end_dt = datetime.strptime(end_date.replace('-', ''), '%Y%m%d') if len(end_date) == 8 else datetime.strptime(end_date, '%Y-%m-%d')
                else:
                    end_dt = datetime.now()

                df = self.cache_manager.get_from_cache(symbol, start_dt, end_dt)

                if not df.empty:
                    logger.info(f"[MarketDataFetcher] ✅ Cache hit for Options {symbol}, rows={len(df)}")
                    logger.warning(f"[MarketDataFetcher] ⚠️ Using cached data for Options {symbol} (API failed)")

                    retrieval_timestamp = df.iloc[0]['retrieval_timestamp'] if 'retrieval_timestamp' in df.columns else datetime.utcnow() - timedelta(hours=1)
                    if isinstance(retrieval_timestamp, str):
                        retrieval_timestamp = datetime.fromisoformat(retrieval_timestamp)

                    data_freshness = self._calculate_data_freshness(retrieval_timestamp)
                    api_source = df.iloc[0]['api_source'] if 'api_source' in df.columns else "Cache (Options)"

                    return {
                        'data': df,
                        'metadata': {
                            'api_source': f"Cache ({api_source})",
                            'retrieval_timestamp': retrieval_timestamp,
                            'data_freshness': data_freshness
                        }
                    }
            except Exception as e:
                logger.error(f"[MarketDataFetcher] ❌ Cache failed for Options {symbol}: {e}")

        # All sources failed for Options
        logger.error(f"[MarketDataFetcher] ❌ ALL SOURCES FAILED for Options {symbol}")
        raise NoDataAvailableError(f"All data sources failed for Options {symbol}")
