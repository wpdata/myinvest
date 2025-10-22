"""CLI commands for investlib-data."""

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from investlib_data.models import Base
from investlib_data.import_csv import CSVImporter
import os
import json


def get_database_url():
    """Get database URL from environment or default."""
    return os.getenv("DATABASE_URL", "sqlite:///data/myinvest.db")


@click.group()
def cli():
    """investlib-data: Market data and investment record management."""
    pass


@cli.command()
@click.option('--dry-run', is_flag=True, help='Preview without executing')
def init_db(dry_run):
    """Initialize database schema."""
    db_url = get_database_url()

    if dry_run:
        click.echo(f"[DRY RUN] Would create database at: {db_url}")
        click.echo(f"[DRY RUN] Tables to create:")
        for table in Base.metadata.sorted_tables:
            click.echo(f"  - {table.name}")
        return

    try:
        engine = create_engine(db_url)

        # Create all tables
        Base.metadata.create_all(engine)

        click.echo(f"✅ Database initialized at: {db_url}")
        click.echo(f"Created {len(Base.metadata.sorted_tables)} tables:")
        for table in Base.metadata.sorted_tables:
            click.echo(f"  ✓ {table.name}")

    except Exception as e:
        click.echo(f"❌ Error initializing database: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--file', '-f', required=True, help='CSV file path')
@click.option('--dry-run', is_flag=True, help='Preview without executing')
@click.option('--output', type=click.Choice(['text', 'json']), default='text')
def import_csv(file, dry_run, output):
    """Import investment records from CSV."""
    if dry_run:
        if output == 'json':
            click.echo(json.dumps({"dry_run": True, "file": file}))
        else:
            click.echo(f"[DRY RUN] Would import from: {file}")
        return

    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    importer = CSVImporter()
    
    try:
        result = importer.save_to_database(file, session)
        if output == 'json':
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Import complete.")
            click.echo(f"  Imported: {result['imported']}")
            click.echo(f"  Rejected: {result['rejected']}")
            if result['errors']:
                click.echo("Errors:")
                for error in result['errors']:
                    click.echo(f"  - {error}")
        
        if result['rejected'] > 0:
            raise click.Abort()
            
    except Exception as e:
        click.echo(f"❌ Error during CSV import: {e}", err=True)
        raise click.Abort()
    finally:
        session.close()


@cli.command()
@click.option('--symbol', required=True, help='Stock symbol (e.g., 600519.SH)')
@click.option('--start', help='Start date (YYYYMMDD format)')
@click.option('--end', help='End date (YYYYMMDD format)')
@click.option('--output', type=click.Choice(['text', 'json']), default='text')
def fetch_market(symbol, start, end, output):
    """Fetch market data for a symbol."""
    try:
        from investlib_data.market_api import MarketDataFetcher

        fetcher = MarketDataFetcher()
        result = fetcher.fetch_with_fallback(symbol, start, end)

        if output == 'json':
            data_dict = result['data'].to_dict(orient='records')
            click.echo(json.dumps({
                'symbol': symbol,
                'data': data_dict,
                'metadata': {
                    'api_source': result['metadata']['api_source'],
                    'retrieval_timestamp': result['metadata']['retrieval_timestamp'].isoformat(),
                    'data_freshness': result['metadata']['data_freshness'],
                    'record_count': len(data_dict)
                }
            }, indent=2))
        else:
            click.echo(f"✅ Fetched market data for {symbol}")
            click.echo(f"  Source: {result['metadata']['api_source']}")
            click.echo(f"  Freshness: {result['metadata']['data_freshness']}")
            click.echo(f"  Records: {len(result['data'])}")
            click.echo(f"  Date range: {result['data']['timestamp'].min()} to {result['data']['timestamp'].max()}")

    except Exception as e:
        click.echo(f"❌ Error fetching market data: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
