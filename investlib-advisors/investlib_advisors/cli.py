"""CLI commands for investlib-advisors."""

import click
import json

@click.group()
def cli():
    """investlib-advisors: AI advisor implementations."""
    pass

@cli.command(name="list-advisors")
def list_advisors():
    """List available AI advisors."""
    advisors = ["livermore"]
    click.echo(json.dumps(advisors))

@cli.command()
@click.option('--advisor', required=True, type=click.Choice(["livermore"]), help='Advisor to use.')
@click.option('--context', required=True, help='JSON file with signal context.')
@click.option('--capital', default=100000.0, help='Total capital (default: 100000)')
@click.option('--output', type=click.Choice(['text', 'json']), default='text')
def ask(advisor, context, capital, output):
    """Get investment recommendation from AI advisor.

    Example:
        investlib-advisors ask --advisor livermore --context signal.json
    """
    try:
        # Load context
        with open(context, 'r') as f:
            signal_data = json.load(f)

        # Generate recommendation
        if advisor == "livermore":
            from investlib_advisors.livermore_advisor import LivermoreAdvisor
            adv = LivermoreAdvisor()
            recommendation = adv.generate_recommendation(signal_data, capital)
        else:
            raise ValueError(f"Unknown advisor: {advisor}")

        # Output
        if output == 'json':
            click.echo(json.dumps(recommendation, indent=2, default=str))
        else:
            click.echo(f"\n{'='*60}")
            click.echo(f"投资建议 - {recommendation['advisor_name']} {recommendation['advisor_version']}")
            click.echo(f"{'='*60}")
            click.echo(f"股票代码：{recommendation['symbol']}")
            click.echo(f"操作建议：{recommendation['action']} ({recommendation['confidence']}置信度)")
            click.echo(f"\n价格水平：")
            click.echo(f"  入场价：{recommendation['entry_price']}")
            click.echo(f"  止损价：{recommendation['stop_loss']}")
            click.echo(f"  止盈价：{recommendation['take_profit']}")
            click.echo(f"\n仓位管理：")
            click.echo(f"  建议仓位：{recommendation['position_size_pct']}%")
            click.echo(f"  最大损失：{recommendation['max_loss']} 元")
            click.echo(f"\n分析说明：")
            click.echo(f"  {recommendation['reasoning']}")

    except FileNotFoundError:
        click.echo(f"❌ Error: Context file not found: {context}", err=True)
        raise click.Abort()
    except json.JSONDecodeError:
        click.echo(f"❌ Error: Invalid JSON in context file", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
