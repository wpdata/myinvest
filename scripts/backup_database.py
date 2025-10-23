#!/usr/bin/env python3
"""
MyInvest V0.3 Database Backup Script
Creates timestamped backups and verifies integrity before migrations.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def backup_database(
    db_path: str = './data/myinvest.db',
    backup_dir: str = './data/backups',
    verify: bool = True
) -> str:
    """
    Create timestamped backup of SQLite database.

    Args:
        db_path: Path to source database file
        backup_dir: Directory to store backups
        verify: Whether to run integrity check on backup

    Returns:
        str: Path to backup file

    Raises:
        FileNotFoundError: If source database doesn't exist
        sqlite3.DatabaseError: If integrity check fails
    """
    # Ensure paths are absolute
    db_path = os.path.abspath(db_path)
    backup_dir = os.path.abspath(backup_dir)

    # Check source database exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f'Database not found: {db_path}')

    # Create backup directory if it doesn't exist
    Path(backup_dir).mkdir(parents=True, exist_ok=True)

    # Generate timestamped backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'myinvest_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)

    # Perform backup
    print(f'Creating backup: {backup_path}')
    shutil.copy2(db_path, backup_path)

    # Get file sizes
    original_size = os.path.getsize(db_path)
    backup_size = os.path.getsize(backup_path)

    print(f'✓ Backup created successfully')
    print(f'  Original: {original_size:,} bytes')
    print(f'  Backup:   {backup_size:,} bytes')

    # Verify backup integrity
    if verify:
        print(f'Verifying backup integrity...')
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()

            # Run integrity check
            cursor.execute('PRAGMA integrity_check;')
            result = cursor.fetchone()[0]

            if result == 'ok':
                print(f'✓ Integrity check passed')
            else:
                raise sqlite3.DatabaseError(f'Integrity check failed: {result}')

            # Get table count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            table_count = cursor.fetchone()[0]
            print(f'  Tables: {table_count}')

            conn.close()
        except Exception as e:
            # Clean up failed backup
            if os.path.exists(backup_path):
                os.remove(backup_path)
            raise sqlite3.DatabaseError(f'Backup verification failed: {e}')

    return backup_path


def restore_database(
    backup_path: str,
    db_path: str = './data/myinvest.db',
    force: bool = False
) -> None:
    """
    Restore database from backup.

    Args:
        backup_path: Path to backup file
        db_path: Path to destination database
        force: Overwrite existing database without confirmation

    Raises:
        FileNotFoundError: If backup doesn't exist
        InterruptedError: If user cancels restore
    """
    backup_path = os.path.abspath(backup_path)
    db_path = os.path.abspath(db_path)

    if not os.path.exists(backup_path):
        raise FileNotFoundError(f'Backup not found: {backup_path}')

    # Confirm if database exists
    if os.path.exists(db_path) and not force:
        response = input(f'⚠ Database exists at {db_path}. Overwrite? (yes/no): ')
        if response.lower() != 'yes':
            raise InterruptedError('Restore cancelled by user')

    # Perform restore
    print(f'Restoring from: {backup_path}')
    print(f'Destination: {db_path}')

    shutil.copy2(backup_path, db_path)

    print(f'✓ Database restored successfully')


def list_backups(backup_dir: str = './data/backups') -> list:
    """
    List all available backups sorted by date (newest first).

    Args:
        backup_dir: Directory containing backups

    Returns:
        List of (filename, filepath, size, modified_time) tuples
    """
    backup_dir = os.path.abspath(backup_dir)

    if not os.path.exists(backup_dir):
        return []

    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.db'):
            filepath = os.path.join(backup_dir, filename)
            size = os.path.getsize(filepath)
            mtime = os.path.getmtime(filepath)
            backups.append((filename, filepath, size, mtime))

    # Sort by modification time (newest first)
    backups.sort(key=lambda x: x[3], reverse=True)

    return backups


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='MyInvest Database Backup Utility')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--db', default='./data/myinvest.db', help='Database path')
    backup_parser.add_argument('--dir', default='./data/backups', help='Backup directory')
    backup_parser.add_argument('--no-verify', action='store_true', help='Skip integrity check')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup', help='Backup file path')
    restore_parser.add_argument('--db', default='./data/myinvest.db', help='Destination database path')
    restore_parser.add_argument('--force', action='store_true', help='Overwrite without confirmation')

    # List command
    list_parser = subparsers.add_parser('list', help='List available backups')
    list_parser.add_argument('--dir', default='./data/backups', help='Backup directory')

    args = parser.parse_args()

    if args.command == 'backup':
        try:
            backup_path = backup_database(
                db_path=args.db,
                backup_dir=args.dir,
                verify=not args.no_verify
            )
            print(f'\n✓ Backup complete: {backup_path}')
            sys.exit(0)
        except Exception as e:
            print(f'\n✗ Backup failed: {e}', file=sys.stderr)
            sys.exit(1)

    elif args.command == 'restore':
        try:
            restore_database(
                backup_path=args.backup,
                db_path=args.db,
                force=args.force
            )
            sys.exit(0)
        except Exception as e:
            print(f'\n✗ Restore failed: {e}', file=sys.stderr)
            sys.exit(1)

    elif args.command == 'list':
        backups = list_backups(args.dir)
        if not backups:
            print(f'No backups found in {args.dir}')
        else:
            print(f'Available backups in {args.dir}:\n')
            for filename, filepath, size, mtime in backups:
                timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f'  {filename}')
                print(f'    Size: {size:,} bytes')
                print(f'    Date: {timestamp}')
                print()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
