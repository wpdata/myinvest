"""CLI interface for investlib-quant."""

import click
import json
import sys
import pandas as pd
from investlib_quant.strategies.livermore import LivermoreStrategy


@click.group()
def cli():
    """investlib-quant CLI - Quantitative trading strategies."""
    pass


@cli.command()
@click.option('--strategy', type=click.Choice(['livermore']), default='livermore', help='策略名称')
@click.option('--data', required=True, type=click.Path(exists=True), help='市场数据文件（CSV 或 JSON）')
@click.option('--output', type=click.Choice(['json', 'text']), default='json', help='输出格式')
@click.option('--dry-run', is_flag=True, help='试运行模式')
def signal(strategy, data, output, dry_run):
    """根据市场数据生成交易信号。

    示例:
        investlib-quant signal --strategy livermore --data market_data.csv
        investlib-quant signal --strategy livermore --data market_data.json --output text
    """
    if dry_run:
        click.echo(f"[DRY RUN] 将使用 {strategy} 策略分析数据文件: {data}")
        return

    try:
        # 加载数据
        if data.endswith('.csv'):
            df = pd.read_csv(data)
        elif data.endswith('.json'):
            df = pd.read_json(data)
        else:
            click.echo("错误: 仅支持 CSV 或 JSON 格式", err=True)
            sys.exit(1)

        # 初始化策略
        if strategy == 'livermore':
            strat = LivermoreStrategy()
        else:
            click.echo(f"错误: 未知策略 {strategy}", err=True)
            sys.exit(1)

        # 生成信号
        signal_result = strat.generate_signal(df)

        if not signal_result:
            click.echo("错误: 数据不足，无法生成信号", err=True)
            sys.exit(1)

        # 输出结果
        if output == 'json':
            click.echo(json.dumps(signal_result, indent=2, ensure_ascii=False))
        else:
            click.echo(f"策略: {strat.name}")
            click.echo(f"操作: {signal_result['action']}")
            if signal_result['action'] == 'BUY':
                click.echo(f"入场价: {signal_result['entry_price']}")
                click.echo(f"止损价: {signal_result['stop_loss']}")
                click.echo(f"止盈价: {signal_result['take_profit']}")
                click.echo(f"仓位建议: {signal_result['position_size_pct']}%")
                click.echo(f"置信度: {signal_result['confidence']}")
                click.echo(f"推理: {json.dumps(signal_result['reasoning'], indent=2, ensure_ascii=False)}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """显示版本信息。"""
    click.echo("investlib-quant v0.1.0")
    click.echo("Quantitative trading strategies library")


if __name__ == '__main__':
    cli()
