"""
MyInvest V0.3 - Shared Memory Market Data Cache (T013)
Zero-copy shared memory for parallel backtest workers.

SCOPE: Inter-process data sharing for parallel backtesting (NOT API response caching).
This cache allows multiple worker processes to read the same market data without
serialization overhead (pickle).

For API response caching, see T073 (investlib-data/cache.py).
"""

import logging
import numpy as np
import pandas as pd
from multiprocessing import shared_memory
from typing import Dict, Tuple, Optional, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class SharedMarketDataCache:
    """Zero-copy shared memory cache for market data across parallel workers.

    This cache is specifically for sharing pre-fetched market data between
    parallel backtest worker processes. It uses Python 3.8+ shared_memory
    to avoid expensive pickle serialization.

    Architecture:
    1. Main process: Fetches market data → Creates shared memory blocks
    2. Worker processes: Attach to shared memory → Read data (zero-copy)
    3. Main process: Cleanup shared memory after all workers complete

    Example:
        # Main process
        cache = SharedMarketDataCache()
        shm_name = cache.create_shared_cache('600519.SH', market_data_df)

        # Worker process
        df = cache.attach_to_shared_cache('600519.SH', metadata)

        # Main process (after all workers done)
        cache.cleanup()
    """

    def __init__(self):
        """Initialize shared memory cache manager."""
        self.shared_blocks: Dict[str, shared_memory.SharedMemory] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def create_shared_cache(
        self,
        symbol: str,
        dataframe: pd.DataFrame,
        columns: list = None
    ) -> str:
        """Create shared memory block for market data.

        Converts DataFrame to NumPy array and stores in shared memory.
        Only numeric columns are stored (open, high, low, close, volume).

        Args:
            symbol: Stock symbol (e.g., '600519.SH')
            dataframe: Market data DataFrame with OHLCV columns
            columns: Columns to store (default: ['open', 'high', 'low', 'close', 'volume'])

        Returns:
            str: Shared memory block name

        Raises:
            ValueError: If required columns missing or data empty
        """
        if dataframe.empty:
            raise ValueError(f"Cannot create shared cache for {symbol}: DataFrame is empty")

        # Default to OHLCV columns
        if columns is None:
            columns = ['open', 'high', 'low', 'close', 'volume']

        # Validate columns exist
        missing_cols = [col for col in columns if col not in dataframe.columns]
        if missing_cols:
            raise ValueError(
                f"Missing required columns for {symbol}: {missing_cols}. "
                f"Available: {list(dataframe.columns)}"
            )

        # Extract numeric data
        numeric_data = dataframe[columns].values.astype(np.float64)

        # Store timestamp separately (as string array for simplicity)
        timestamps = dataframe['timestamp'].astype(str).values if 'timestamp' in dataframe.columns else None

        # Create shared memory block
        shm_name = f"mkt_{symbol.replace('.', '_')}_{id(self)}"
        nbytes = numeric_data.nbytes

        try:
            shm = shared_memory.SharedMemory(create=True, size=nbytes, name=shm_name)

            # Copy data to shared memory
            shared_array = np.ndarray(
                numeric_data.shape,
                dtype=np.float64,
                buffer=shm.buf
            )
            shared_array[:] = numeric_data[:]

            # Store metadata
            self.metadata[symbol] = {
                'shm_name': shm_name,
                'shape': numeric_data.shape,
                'dtype': str(np.float64),
                'columns': columns,
                'timestamps': timestamps.tolist() if timestamps is not None else None,
                'row_count': len(dataframe),
                'created_at': datetime.now().isoformat()
            }

            self.shared_blocks[symbol] = shm

            logger.info(
                f"[SharedCache] Created shared memory for {symbol}: "
                f"{nbytes:,} bytes ({numeric_data.shape[0]} rows × {numeric_data.shape[1]} cols)"
            )

            return shm_name

        except Exception as e:
            logger.error(f"[SharedCache] Failed to create shared memory for {symbol}: {e}")
            # Cleanup on failure
            if shm_name in self.shared_blocks:
                try:
                    self.shared_blocks[shm_name].close()
                    self.shared_blocks[shm_name].unlink()
                except:
                    pass
            raise

    def attach_to_shared_cache(
        self,
        symbol: str,
        metadata: Dict[str, Any]
    ) -> pd.DataFrame:
        """Attach to existing shared memory and reconstruct DataFrame.

        This method is called by worker processes to access shared market data.

        Args:
            symbol: Stock symbol
            metadata: Metadata dict from create_shared_cache (contains shm_name, shape, columns, etc.)

        Returns:
            pd.DataFrame: Reconstructed market data

        Raises:
            ValueError: If metadata invalid or shared memory not found
        """
        if 'shm_name' not in metadata:
            raise ValueError(f"Metadata for {symbol} missing 'shm_name' field")

        shm_name = metadata['shm_name']
        shape = tuple(metadata['shape'])
        columns = metadata['columns']
        timestamps = metadata.get('timestamps')

        try:
            # Attach to existing shared memory
            shm = shared_memory.SharedMemory(name=shm_name)

            # Create NumPy array view (zero-copy!)
            shared_array = np.ndarray(
                shape,
                dtype=np.float64,
                buffer=shm.buf
            )

            # Reconstruct DataFrame
            df = pd.DataFrame(shared_array.copy(), columns=columns)

            # Add timestamps if available
            if timestamps:
                df['timestamp'] = timestamps

            logger.debug(
                f"[SharedCache] Worker attached to shared memory for {symbol}: "
                f"{len(df)} rows"
            )

            # Note: Worker should NOT close the shared memory
            # Only the main process (creator) should cleanup

            return df

        except FileNotFoundError:
            raise ValueError(
                f"Shared memory block '{shm_name}' not found for {symbol}. "
                f"Ensure main process created it before workers started."
            )
        except Exception as e:
            logger.error(f"[SharedCache] Failed to attach to shared memory for {symbol}: {e}")
            raise

    def get_metadata(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a symbol's shared cache.

        Args:
            symbol: Stock symbol

        Returns:
            Metadata dict or None if not found
        """
        return self.metadata.get(symbol)

    def cleanup(self) -> None:
        """Clean up all shared memory blocks.

        CRITICAL: This must be called by the main process after all workers complete.
        Workers should NOT call this method.
        """
        for symbol, shm in self.shared_blocks.items():
            try:
                shm.close()
                shm.unlink()
                logger.info(f"[SharedCache] Cleaned up shared memory for {symbol}")
            except Exception as e:
                logger.warning(f"[SharedCache] Failed to cleanup {symbol}: {e}")

        self.shared_blocks.clear()
        self.metadata.clear()

    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics.

        Returns:
            Dict with total_bytes and per-symbol breakdown
        """
        usage = {'total_bytes': 0, 'symbols': {}}

        for symbol, meta in self.metadata.items():
            shape = meta['shape']
            nbytes = np.prod(shape) * 8  # float64 = 8 bytes
            usage['symbols'][symbol] = nbytes
            usage['total_bytes'] += nbytes

        return usage


def backtest_single_stock_worker(
    symbol: str,
    metadata: Dict[str, Any],
    start_date: str,
    end_date: str,
    strategy_class,
    strategy_params: Dict[str, Any],
    capital: float
) -> Dict[str, Any]:
    """Worker function for parallel backtest execution.

    This function runs in a separate process and uses shared memory to access
    market data without serialization overhead.

    Args:
        symbol: Stock symbol
        metadata: Shared memory metadata from SharedMarketDataCache
        start_date: Backtest start date
        end_date: Backtest end date
        strategy_class: Strategy class (not instance - will be instantiated in worker)
        strategy_params: Strategy initialization parameters
        capital: Initial capital

    Returns:
        Dict with backtest results for this symbol
    """
    try:
        # Attach to shared memory
        cache = SharedMarketDataCache()
        market_data = cache.attach_to_shared_cache(symbol, metadata)

        # Initialize strategy in worker process
        strategy = strategy_class(**strategy_params)

        # Run backtest on this symbol only
        from investlib_backtest.engine.backtest_runner import BacktestRunner

        runner = BacktestRunner()
        result = runner.run_single_stock(
            symbol=symbol,
            data=market_data,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            capital=capital
        )

        return {
            'symbol': symbol,
            'success': True,
            'result': result
        }

    except Exception as e:
        logger.error(f"[Worker] Backtest failed for {symbol}: {e}")
        return {
            'symbol': symbol,
            'success': False,
            'error': str(e)
        }
