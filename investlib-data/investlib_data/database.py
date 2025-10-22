"""Database initialization and session management."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from investlib_data.models import Base
import click


# Database URL from environment or default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/myinvest.db")


def get_engine(database_url: str = None, echo: bool = False):
    """Create SQLAlchemy engine.

    Args:
        database_url: Database URL (default from env or SQLite)
        echo: Echo SQL statements

    Returns:
        SQLAlchemy Engine
    """
    url = database_url or DATABASE_URL

    # Special handling for SQLite
    if url.startswith("sqlite"):
        # Use StaticPool for in-memory databases
        if ":memory:" in url:
            return create_engine(
                url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            # File-based SQLite
            # Create data directory if it doesn't exist
            if "data/" in url:
                os.makedirs("data", exist_ok=True)

            return create_engine(
                url,
                echo=echo,
                connect_args={"check_same_thread": False}
            )
    else:
        # PostgreSQL or other databases
        # Increase pool size to handle concurrent requests
        return create_engine(
            url,
            echo=echo,
            pool_size=20,        # Increase from default 5 to 20
            max_overflow=40,     # Increase from default 10 to 40
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600    # Recycle connections after 1 hour
        )


def create_all_tables(engine, echo: bool = True):
    """Create all tables defined in models.

    Args:
        engine: SQLAlchemy Engine
        echo: Print creation messages
    """
    if echo:
        click.echo("Creating database tables...")

    Base.metadata.create_all(engine)

    if echo:
        click.echo("✓ All tables created successfully")
        click.echo(f"  Tables: {', '.join(Base.metadata.tables.keys())}")


def drop_all_tables(engine, echo: bool = True):
    """Drop all tables (WARNING: destructive operation).

    Args:
        engine: SQLAlchemy Engine
        echo: Print deletion messages
    """
    if echo:
        click.echo("⚠️  Dropping all tables...")

    Base.metadata.drop_all(engine)

    if echo:
        click.echo("✓ All tables dropped")


def get_session_factory(database_url: str = None):
    """Create session factory.

    Args:
        database_url: Database URL

    Returns:
        SQLAlchemy sessionmaker
    """
    engine = get_engine(database_url)
    return sessionmaker(bind=engine)


# Global session factory (initialized on first import)
SessionLocal = get_session_factory()


def get_db() -> Session:
    """Get database session (context manager compatible).

    Usage:
        with get_db() as session:
            session.query(...)

    Or:
        session = get_db()
        try:
            session.query(...)
        finally:
            session.close()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def verify_database(engine) -> dict:
    """Verify database structure and return status.

    Args:
        engine: SQLAlchemy Engine

    Returns:
        dict with verification results
    """
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = set(Base.metadata.tables.keys())
    actual_tables = set(tables)

    missing = expected_tables - actual_tables
    extra = actual_tables - expected_tables

    return {
        "exists": len(tables) > 0,
        "expected_count": len(expected_tables),
        "actual_count": len(actual_tables),
        "tables": tables,
        "missing": list(missing),
        "extra": list(extra),
        "valid": len(missing) == 0 and len(actual_tables) >= len(expected_tables)
    }


def init_database(database_url: str = None, drop_existing: bool = False, dry_run: bool = False):
    """Initialize database with all tables.

    Args:
        database_url: Database URL (default from env)
        drop_existing: Drop existing tables first (WARNING: destructive)
        dry_run: Preview actions without executing

    Returns:
        True if successful, False otherwise
    """
    url = database_url or DATABASE_URL

    if dry_run:
        click.echo("[DRY RUN] Database initialization preview:")
        click.echo(f"  Database URL: {url}")
        click.echo(f"  Drop existing: {drop_existing}")
        click.echo(f"  Tables to create: {', '.join(Base.metadata.tables.keys())}")
        return True

    try:
        engine = get_engine(url)

        if drop_existing:
            drop_all_tables(engine, echo=True)

        create_all_tables(engine, echo=True)

        # Verify
        status = verify_database(engine)

        if status['valid']:
            click.echo(f"\n✓ Database initialized successfully")
            click.echo(f"  URL: {url}")
            click.echo(f"  Tables: {len(status['tables'])}")
            return True
        else:
            click.echo(f"\n✗ Database verification failed")
            if status['missing']:
                click.echo(f"  Missing tables: {', '.join(status['missing'])}")
            return False

    except Exception as e:
        click.echo(f"\n✗ Database initialization failed: {e}", err=True)
        return False
