"""
MyInvest V0.3 - Watchlist Database Access Layer
CRUD operations for watchlist management (User Story 1).
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import csv
from pathlib import Path


class WatchlistDB:
    """Database access layer for watchlist management."""

    def __init__(self, db_path: str = './data/myinvest.db'):
        """
        Initialize watchlist database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_symbol(
        self,
        symbol: str,
        group_name: str = 'default',
        contract_type: str = 'stock',
        status: str = 'active'
    ) -> int:
        """
        Add a symbol to the watchlist.

        Args:
            symbol: Stock/futures/option symbol (e.g., '600519.SH', 'IF2506.CFFEX')
            group_name: Group name for categorization (e.g., 'Core Holdings', 'Tech Stocks')
            contract_type: 'stock', 'futures', or 'option'
            status: 'active' or 'paused'

        Returns:
            int: ID of the inserted row

        Raises:
            sqlite3.IntegrityError: If symbol already exists
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO watchlist (symbol, group_name, contract_type, status)
                VALUES (?, ?, ?, ?)
            """, (symbol, group_name, contract_type, status))

            row_id = cursor.lastrowid
            conn.commit()
            return row_id
        except sqlite3.IntegrityError as e:
            # Check if symbol already exists
            cursor.execute("SELECT id FROM watchlist WHERE symbol = ?", (symbol,))
            existing = cursor.fetchone()
            if existing:
                raise ValueError(f"Symbol {symbol} already exists in watchlist")
            raise e
        finally:
            conn.close()

    def remove_symbol(self, symbol: str) -> bool:
        """
        Remove a symbol from the watchlist.

        Args:
            symbol: Symbol to remove

        Returns:
            bool: True if symbol was removed, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def update_symbol_group(self, symbol: str, new_group: str) -> bool:
        """
        Update the group name for a symbol.

        Args:
            symbol: Symbol to update
            new_group: New group name

        Returns:
            bool: True if updated, False if symbol not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE watchlist
            SET group_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (new_group, symbol))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def set_symbol_status(self, symbol: str, status: str) -> bool:
        """
        Set status for a symbol (active/paused).

        Args:
            symbol: Symbol to update
            status: 'active' or 'paused'

        Returns:
            bool: True if updated, False if symbol not found

        Raises:
            ValueError: If status is invalid
        """
        if status not in ('active', 'paused'):
            raise ValueError(f"Invalid status '{status}'. Must be 'active' or 'paused'")

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE watchlist
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (status, symbol))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def get_all_symbols(self, status: str = 'active') -> List[Dict[str, any]]:
        """
        Get all symbols from watchlist.

        Args:
            status: Filter by status ('active', 'paused', or 'all')

        Returns:
            List of dicts with symbol information
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if status == 'all':
            cursor.execute("""
                SELECT id, symbol, group_name, contract_type, status, created_at, updated_at
                FROM watchlist
                ORDER BY group_name, symbol
            """)
        else:
            cursor.execute("""
                SELECT id, symbol, group_name, contract_type, status, created_at, updated_at
                FROM watchlist
                WHERE status = ?
                ORDER BY group_name, symbol
            """, (status,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_symbols_by_group(self, group_name: str, status: str = 'active') -> List[Dict[str, any]]:
        """
        Get symbols filtered by group name.

        Args:
            group_name: Group name to filter by
            status: Filter by status ('active', 'paused', or 'all')

        Returns:
            List of dicts with symbol information
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if status == 'all':
            cursor.execute("""
                SELECT id, symbol, group_name, contract_type, status, created_at, updated_at
                FROM watchlist
                WHERE group_name = ?
                ORDER BY symbol
            """, (group_name,))
        else:
            cursor.execute("""
                SELECT id, symbol, group_name, contract_type, status, created_at, updated_at
                FROM watchlist
                WHERE group_name = ? AND status = ?
                ORDER BY symbol
            """, (group_name, status))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_all_groups(self) -> List[str]:
        """
        Get list of all unique group names.

        Returns:
            List of group names sorted alphabetically
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT group_name
            FROM watchlist
            ORDER BY group_name
        """)

        rows = cursor.fetchall()
        conn.close()

        return [row['group_name'] for row in rows]

    def batch_import_from_csv(
        self,
        file_path: str,
        skip_duplicates: bool = True
    ) -> Tuple[int, List[str]]:
        """
        Import symbols from CSV file.

        CSV Format (with header):
            symbol,group_name,contract_type
            600519.SH,Core Holdings,stock
            000001.SZ,Tech Stocks,stock
            IF2506.CFFEX,Futures,futures

        Args:
            file_path: Path to CSV file
            skip_duplicates: If True, skip existing symbols; if False, raise error

        Returns:
            Tuple of (success_count, error_list)
            - success_count: Number of successfully imported symbols
            - error_list: List of error messages for failed imports

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        success_count = 0
        error_list = []

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Validate required columns
                if 'symbol' not in reader.fieldnames:
                    raise ValueError("CSV must contain 'symbol' column")

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    symbol = row.get('symbol', '').strip()
                    group_name = row.get('group_name', 'default').strip()
                    contract_type = row.get('contract_type', 'stock').strip()

                    if not symbol:
                        error_list.append(f"Row {row_num}: Missing symbol")
                        continue

                    try:
                        self.add_symbol(
                            symbol=symbol,
                            group_name=group_name or 'default',
                            contract_type=contract_type or 'stock',
                            status='active'
                        )
                        success_count += 1
                    except ValueError as e:
                        if skip_duplicates and "already exists" in str(e):
                            # Skip duplicate
                            continue
                        else:
                            error_list.append(f"Row {row_num} ({symbol}): {str(e)}")
                    except Exception as e:
                        error_list.append(f"Row {row_num} ({symbol}): {str(e)}")

        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")

        return success_count, error_list

    def get_symbol_count(self, status: str = 'active') -> int:
        """
        Get count of symbols in watchlist.

        Args:
            status: Filter by status ('active', 'paused', or 'all')

        Returns:
            int: Count of symbols
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if status == 'all':
            cursor.execute("SELECT COUNT(*) as count FROM watchlist")
        else:
            cursor.execute("SELECT COUNT(*) as count FROM watchlist WHERE status = ?", (status,))

        result = cursor.fetchone()
        conn.close()

        return result['count'] if result else 0

    def batch_update_status(self, symbols: List[str], status: str) -> int:
        """
        Batch update status for multiple symbols.

        Args:
            symbols: List of symbols to update
            status: New status ('active' or 'paused')

        Returns:
            int: Number of symbols updated

        Raises:
            ValueError: If status is invalid
        """
        if status not in ('active', 'paused'):
            raise ValueError(f"Invalid status '{status}'. Must be 'active' or 'paused'")

        if not symbols:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        placeholders = ','.join(['?'] * len(symbols))
        cursor.execute(f"""
            UPDATE watchlist
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE symbol IN ({placeholders})
        """, [status] + symbols)

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected
