"""CLI interface for investlib-data."""

import click
import json
import sys
from datetime import datetime
from investlib_data.database import SessionLocal
from investlib_data.services.data_service import DataService


@click.group()
def cli():
    """investlib-data CLI - Market data management."""
    pass


@cli.command()
@click.option('--symbol', required=True, help='股票代码，如 600519.SH')
@click.option('--start', help='开始日期 YYYYMMDD 或 YYYY-MM-DD')
@click.option('--end', help='结束日期 YYYYMMDD 或 YYYY-MM-DD')
@click.option('--output', type=click.Choice(['json', 'csv']), default='json', help='输出格式')
@click.option('--no-cache', is_flag=True, help='不使用缓存，强制调用 API')
@click.option('--dry-run', is_flag=True, help='试运行模式，仅显示将要执行的操作')
def fetch(symbol, start, end, output, no_cache, dry_run):
    """获取市场数据。

    示例:
        investlib-data fetch --symbol 600519.SH --start 20240101 --end 20241231
        investlib-data fetch --symbol 600519.SH --output json
        investlib-data fetch --symbol 600519.SH --no-cache --dry-run
    """
    if dry_run:
        click.echo(f"[DRY RUN] 将获取 {symbol} 的数据")
        click.echo(f"  开始日期: {start or '默认（1年前）'}")
        click.echo(f"  结束日期: {end or '默认（今天）'}")
        click.echo(f"  使用缓存: {not no_cache}")
        click.echo(f"  输出格式: {output}")
        return

    session = SessionLocal()
    try:
        service = DataService(session)

        click.echo(f"正在获取 {symbol} 的市场数据...", err=True)

        result = service.get_market_data(
            symbol=symbol,
            start_date=start,
            end_date=end,
            use_cache=not no_cache
        )

        df = result['data']
        metadata = result['metadata']

        # 输出元数据到 stderr
        click.echo(f"数据来源: {metadata['source']}", err=True)
        click.echo(f"API 源: {metadata['api_source']}", err=True)
        click.echo(f"数据新鲜度: {metadata['data_freshness']}", err=True)
        click.echo(f"缓存命中: {metadata['cache_hit']}", err=True)
        if 'warning' in metadata:
            click.echo(f"警告: {metadata['warning']}", err=True)

        # 输出数据到 stdout
        if output == 'json':
            output_data = {
                "symbol": symbol,
                "data": df.to_dict(orient='records'),
                "metadata": {
                    "source": metadata['source'],
                    "api_source": metadata['api_source'],
                    "retrieval_timestamp": metadata['retrieval_timestamp'].isoformat(),
                    "data_freshness": metadata['data_freshness'],
                    "cache_hit": metadata['cache_hit'],
                    "record_count": len(df)
                }
            }
            click.echo(json.dumps(output_data, indent=2, ensure_ascii=False))
        else:
            # CSV 输出
            click.echo(df.to_csv(index=False))

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command("init-db")
@click.option('--drop-existing', is_flag=True, help='删除现有表（警告：破坏性操作）')
@click.option('--dry-run', is_flag=True, help='预览操作，不实际执行')
@click.option('--database-url', help='数据库 URL（默认使用环境变量）')
def init_db(drop_existing, dry_run, database_url):
    """初始化数据库，创建所有表。

    示例:
        investlib-data init-db
        investlib-data init-db --dry-run
        investlib-data init-db --drop-existing
        investlib-data init-db --database-url sqlite:///test.db
    """
    from investlib_data.database import init_database

    success = init_database(
        database_url=database_url,
        drop_existing=drop_existing,
        dry_run=dry_run
    )

    sys.exit(0 if success else 1)


@cli.command()
def cache_stats():
    """查看缓存统计信息。"""
    session = SessionLocal()
    try:
        service = DataService(session)
        stats = service.get_cache_info()

        click.echo("缓存统计:")
        click.echo(f"  总记录数: {stats['total_records']}")
        click.echo(f"  活跃记录: {stats['active_records']}")
        click.echo(f"  过期记录: {stats['expired_records']}")
        click.echo(f"  覆盖标的: {stats['unique_symbols']}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
@click.option('--dry-run', is_flag=True, help='试运行，不实际删除')
def cleanup_cache(dry_run):
    """清理过期的缓存数据。"""
    session = SessionLocal()
    try:
        service = DataService(session)

        if dry_run:
            stats = service.get_cache_info()
            click.echo(f"[DRY RUN] 将删除 {stats['expired_records']} 条过期记录")
            return

        deleted_count = service.cleanup_cache()
        click.echo(f"已删除 {deleted_count} 条过期记录")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@cli.command()
def version():
    """显示版本信息。"""
    click.echo("investlib-data v0.1.0")
    click.echo("Market data management library for MyInvest")


if __name__ == '__main__':
    cli()
