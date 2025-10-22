"""CLI commands for investlib-quant."""

import click
import json
import pandas as pd
from investlib_quant.signal_generator import SignalGenerator


@click.group()
def cli():
    """investlib-quant: Quantitative strategy analysis."""
    pass


@cli.command()
@click.option('--symbol', required=True, help='Stock symbol to analyze (e.g., 600519.SH)')
@click.option('--market-data', required=True, help='CSV file with market data (OHLCV)')
@click.option('--capital', default=100000.0, help='Total capital (default: 100000)')
@click.option('--strategy', default='livermore', help='Strategy to use (default: livermore)')
@click.option('--output', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--dry-run', is_flag=True, help='Preview without generating signal')
def analyze(symbol, market_data, capital, strategy, output, dry_run):
    """Analyze a stock and generate trading signal.

    Example:
        investlib-quant analyze --symbol 600519.SH --market-data data.csv --capital 100000
    """
    if dry_run:
        if output == 'json':
            click.echo(json.dumps({
                "dry_run": True,
                "symbol": symbol,
                "market_data": market_data,
                "capital": capital,
                "strategy": strategy
            }, indent=2))
        else:
            click.echo(f"[DRY RUN] Would analyze {symbol} with {strategy} strategy")
            click.echo(f"  Market data: {market_data}")
            click.echo(f"  Capital: {capital}")
        return

    try:
        # Load market data
        df = pd.read_csv(market_data)

        # Validate required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Convert timestamp to datetime
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Generate signal
        if strategy != 'livermore':
            raise ValueError(f"Strategy '{strategy}' not supported. Use 'livermore'.")

        generator = SignalGenerator()
        signal = generator.generate_trading_signal(
            symbol=symbol,
            market_data=df,
            capital=capital
        )

        # Output result
        if output == 'json':
            click.echo(json.dumps(signal, indent=2, default=str))
        else:
            click.echo(f"\n{'='*60}")
            click.echo(f"Trading Signal for {symbol}")
            click.echo(f"{'='*60}")
            click.echo(f"Action:          {signal['action']} ({signal['confidence']} confidence)")
            click.echo(f"Entry Price:     {signal['entry_price']}")
            click.echo(f"Stop Loss:       {signal['stop_loss']}")
            click.echo(f"Take Profit:     {signal['take_profit']}")
            click.echo(f"Position Size:   {signal['position_size_pct']}%")
            click.echo(f"Max Loss:        {signal['max_loss']} (RED)")
            click.echo(f"Risk/Reward:     1:{signal['risk_reward_ratio']}")
            click.echo(f"\nKey Factors:")
            for factor in signal['key_factors']:
                click.echo(f"  - {factor}")

            if not signal['validation']['valid']:
                click.echo(f"\n⚠ Validation Errors:")
                for error in signal['validation']['errors']:
                    click.echo(f"  - {error}")

    except FileNotFoundError:
        click.echo(f"❌ Error: Market data file not found: {market_data}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--input', required=True, help='CSV file with market data for multiple symbols')
@click.option('--capital', default=100000.0, help='Total capital (default: 100000)')
@click.option('--output', type=click.Choice(['text', 'json']), default='text')
@click.option('--dry-run', is_flag=True, help='Preview without generating signals')
def signals(input, capital, output, dry_run):
    """Generate trading signals for multiple symbols from CSV.

    CSV format: symbol,timestamp,open,high,low,close,volume
    """
    if dry_run:
        if output == 'json':
            click.echo(json.dumps({"dry_run": True, "input": input}, indent=2))
        else:
            click.echo(f"[DRY RUN] Would generate signals from: {input}")
        return

    try:
        # Load data
        df = pd.read_csv(input)

        # Group by symbol
        if 'symbol' not in df.columns:
            raise ValueError("CSV must have 'symbol' column")

        symbols = df['symbol'].unique()
        market_data_dict = {}

        for symbol in symbols:
            symbol_data = df[df['symbol'] == symbol].copy()
            market_data_dict[symbol] = symbol_data

        # Generate signals
        generator = SignalGenerator()
        signals_result = generator.generate_signals_batch(
            symbols=list(symbols),
            market_data_dict=market_data_dict,
            capital=capital
        )

        # Output
        if output == 'json':
            click.echo(json.dumps(signals_result, indent=2, default=str))
        else:
            click.echo(f"\nGenerated {len(signals_result)} signals:")
            for symbol, signal in signals_result.items():
                if 'error' in signal:
                    click.echo(f"\n{symbol}: ❌ {signal['error']}")
                else:
                    click.echo(f"\n{symbol}: {signal['action']} @ {signal['entry_price']}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
