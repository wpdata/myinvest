"""CLI interface for investlib-advisors."""

import click
import json
import sys
from investlib_advisors.agents.livermore_agent import LivermoreAdvisor


@click.group()
def cli():
    """investlib-advisors CLI - AI investment advisors."""
    pass


@cli.command()
@click.option('--advisor', type=click.Choice(['livermore']), default='livermore', help='顾问名称')
@click.option('--signal-file', required=True, type=click.Path(exists=True), help='信号 JSON 文件')
@click.option('--output', type=click.Choice(['json', 'text']), default='json', help='输出格式')
@click.option('--dry-run', is_flag=True, help='试运行模式')
def ask(advisor, signal_file, output, dry_run):
    """咨询 AI 顾问意见。

    示例:
        investlib-advisors ask --advisor livermore --signal-file signal.json
        investlib-advisors ask --advisor livermore --signal-file signal.json --output text

    signal.json 格式:
    {
        "symbol": "600519.SH",
        "signal": {...},
        "market_context": {...},
        "portfolio_state": {...}
    }
    """
    if dry_run:
        click.echo(f"[DRY RUN] 将咨询 {advisor} 顾问，输入文件: {signal_file}")
        return

    try:
        # 加载信号文件
        with open(signal_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        # 验证输入
        required_keys = ['symbol', 'signal', 'market_context', 'portfolio_state']
        for key in required_keys:
            if key not in input_data:
                click.echo(f"错误: 输入文件缺少字段 '{key}'", err=True)
                sys.exit(1)

        # 初始化顾问
        if advisor == 'livermore':
            adv = LivermoreAdvisor()
        else:
            click.echo(f"错误: 未知顾问 {advisor}", err=True)
            sys.exit(1)

        click.echo(f"正在咨询 {advisor} 顾问...", err=True)

        # 获取建议
        recommendation = adv.get_recommendation(
            symbol=input_data['symbol'],
            signal=input_data['signal'],
            market_context=input_data['market_context'],
            portfolio_state=input_data['portfolio_state']
        )

        # 输出结果
        if output == 'json':
            click.echo(json.dumps(recommendation, indent=2, ensure_ascii=False))
        else:
            click.echo(f"\n顾问: {recommendation['advisor']} (版本 {recommendation['advisor_version']})")
            click.echo(f"建议: {recommendation['recommendation']}")
            click.echo(f"置信度: {recommendation['confidence']}")
            click.echo(f"\n推理过程:")
            click.echo(f"  {recommendation['reasoning']}")
            click.echo(f"\n关键因素:")
            for factor in recommendation.get('key_factors', []):
                click.echo(f"  - {factor}")

            if recommendation.get('modifications'):
                click.echo(f"\n建议修改:")
                click.echo(f"  {json.dumps(recommendation['modifications'], indent=2, ensure_ascii=False)}")

            if recommendation.get('historical_precedent'):
                click.echo(f"\n历史案例:")
                click.echo(f"  {recommendation['historical_precedent']}")

    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """显示版本信息。"""
    click.echo("investlib-advisors v0.1.0")
    click.echo("AI investment advisors library")


if __name__ == '__main__':
    cli()
