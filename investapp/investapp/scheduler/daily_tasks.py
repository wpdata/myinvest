"""Daily Automated Tasks Scheduler (T088-T091).

Runs at 08:30 Beijing time (before A-share market open at 09:30).
Generates recommendations for all approved strategies on watchlist symbols.
"""

import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz


class DailyScheduler:
    """Automated daily recommendation generator."""

    def __init__(self, db_path: str = "/Users/pw/ai/myinvest/data/myinvest.db"):
        """Initialize daily scheduler.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Shanghai'))

    def start(self):
        """Start the scheduled tasks."""
        # Schedule daily task at 08:30 Beijing time (weekdays only)
        trigger = CronTrigger(
            hour=8,
            minute=30,
            day_of_week='mon-fri',
            timezone='Asia/Shanghai'
        )

        self.scheduler.add_job(
            func=self.run_daily_tasks,
            trigger=trigger,
            id='daily_recommendations',
            name='Generate Daily Recommendations',
            replace_existing=True
        )

        self.scheduler.start()
        self.logger.info("✅ Daily scheduler started. Next run at 08:30 Beijing time.")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        self.logger.info("Scheduler stopped.")

    def run_daily_tasks(self):
        """Execute daily recommendation generation task (T089).

        This is the main task that runs at 08:30 every trading day.
        """
        start_time = datetime.now()
        self.logger.info("=== Starting Daily Task Execution ===")

        try:
            # Step 1: Get watchlist symbols
            watchlist = self._get_watchlist_symbols()
            self.logger.info(f"Watchlist: {len(watchlist)} symbols")

            if not watchlist:
                self.logger.warning("No symbols in watchlist. Skipping task.")
                self._log_execution(
                    status='PARTIAL',
                    symbols_processed=0,
                    recommendations_generated=0,
                    data_source='N/A',
                    error_message='Empty watchlist',
                    duration_seconds=0
                )
                return

            # Step 2: Get approved strategies
            approved_strategies = self._get_approved_strategies()
            self.logger.info(f"Approved strategies: {approved_strategies}")

            if not approved_strategies:
                self.logger.warning("No approved strategies. Skipping recommendation generation.")
                self._log_execution(
                    status='PARTIAL',
                    symbols_processed=len(watchlist),
                    recommendations_generated=0,
                    data_source='N/A',
                    error_message='No approved strategies',
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
                return

            # Step 3: Generate recommendations for each symbol
            total_recommendations = 0
            data_sources_used = set()
            errors = []

            for symbol in watchlist:
                try:
                    recs = self._generate_recommendations_for_symbol(
                        symbol, approved_strategies
                    )
                    total_recommendations += len(recs)

                    # Track data sources
                    for rec in recs:
                        if 'data_source' in rec:
                            data_sources_used.add(rec['data_source'])

                    self.logger.info(
                        f"✅ Generated {len(recs)} recommendations for {symbol}"
                    )

                except Exception as e:
                    self.logger.error(f"❌ Failed to generate recommendations for {symbol}: {e}")
                    errors.append(f"{symbol}: {str(e)[:50]}")

            # Step 4: Log execution summary
            duration = (datetime.now() - start_time).total_seconds()
            status = 'SUCCESS' if not errors else 'PARTIAL' if total_recommendations > 0 else 'FAILURE'

            self._log_execution(
                status=status,
                symbols_processed=len(watchlist),
                recommendations_generated=total_recommendations,
                data_source=', '.join(data_sources_used) if data_sources_used else 'N/A',
                error_message='; '.join(errors) if errors else None,
                duration_seconds=duration
            )

            self.logger.info(
                f"=== Daily Task Complete: {status} | "
                f"{total_recommendations} recommendations | "
                f"{duration:.1f}s ==="
            )

        except Exception as e:
            # Fatal error
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌❌ Daily task FAILED: {e}", exc_info=True)

            self._log_execution(
                status='FAILURE',
                symbols_processed=0,
                recommendations_generated=0,
                data_source='N/A',
                error_message=str(e)[:500],
                duration_seconds=duration
            )

    def _get_watchlist_symbols(self) -> List[str]:
        """Get watchlist symbols from database.

        Returns:
            List of stock symbols
        """
        # For V0.2, use a hardcoded watchlist
        # In future versions, this would come from a user watchlist table
        return [
            "600519.SH",  # Moutai
            "000001.SZ",  # Ping An Bank
            "600036.SH",  # China Merchants Bank
            "000858.SZ",  # Wuliangye
            "601318.SH"   # Ping An Insurance
        ]

    def _get_approved_strategies(self) -> List[str]:
        """Get list of approved strategy names.

        Returns:
            List of approved strategy names (e.g., ['Livermore', 'Kroll'])
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT DISTINCT br.strategy_name
                FROM strategy_approval sa
                JOIN backtest_results br ON sa.backtest_id = br.id
                WHERE sa.status = 'APPROVED'
            """)

            strategies = [row[0] for row in cursor.fetchall()]

            # If no approved strategies found, use default strategies
            if not strategies:
                self.logger.info("No approved strategies in database, using default strategies")
                strategies = ['Livermore', 'Kroll', 'Fusion']

        except Exception as e:
            self.logger.warning(f"Could not query approved strategies: {e}")
            # Default to all strategies if table doesn't exist or query fails
            strategies = ['Livermore', 'Kroll', 'Fusion']
        finally:
            conn.close()

        return strategies

    def _generate_recommendations_for_symbol(
        self,
        symbol: str,
        strategies: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for a symbol using approved strategies.

        Args:
            symbol: Stock symbol
            strategies: List of approved strategy names

        Returns:
            List of recommendation dictionaries
        """
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../investlib-quant'))

        from investlib_quant.livermore_strategy import LivermoreStrategy
        from investlib_quant.kroll_strategy import KrollStrategy
        from investlib_quant.fusion_strategy import FusionStrategy

        recommendations = []

        # Map strategy names to classes
        strategy_map = {
            'Livermore': LivermoreStrategy,
            'Kroll': KrollStrategy,
            'Fusion': FusionStrategy
        }

        for strategy_name in strategies:
            if strategy_name not in strategy_map:
                self.logger.warning(f"Unknown strategy: {strategy_name}")
                continue

            try:
                # Initialize strategy
                strategy_class = strategy_map[strategy_name]
                strategy = strategy_class()

                # Generate recommendation
                result = strategy.analyze(
                    symbol=symbol,
                    start_date=None,  # Use default lookback
                    end_date=None,
                    capital=100000,
                    use_cache=True
                )

                # Mark as automated
                result['is_automated'] = True
                result['is_read'] = False
                result['generated_at'] = datetime.now().isoformat()

                # Save to database
                self._save_recommendation(result)

                recommendations.append(result)

            except Exception as e:
                self.logger.error(f"Strategy {strategy_name} failed for {symbol}: {e}")

        return recommendations

    def _save_recommendation(self, recommendation: Dict[str, Any]):
        """Save recommendation to database.

        Args:
            recommendation: Recommendation dictionary
        """
        import uuid
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Generate UUID for recommendation
            rec_id = str(uuid.uuid4())

            # Extract required fields from recommendation
            # Convert list fields to strings
            key_factors = recommendation.get('key_factors', '')
            if isinstance(key_factors, list):
                key_factors = '; '.join(str(f) for f in key_factors)

            reasoning = recommendation.get('reasoning', 'Automated recommendation')
            if isinstance(reasoning, list):
                reasoning = '; '.join(str(r) for r in reasoning)

            cursor.execute("""
                INSERT INTO investment_recommendations (
                    recommendation_id, symbol, action, entry_price,
                    stop_loss, take_profit, position_size_pct, max_loss_amount,
                    expected_return_pct, advisor_name, advisor_version,
                    strategy_name, reasoning, confidence, key_factors,
                    market_data_timestamp, data_source, created_timestamp,
                    data_freshness, is_automated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec_id,
                recommendation.get('symbol'),
                recommendation.get('action', 'HOLD'),
                recommendation.get('entry_price', 0.0),
                recommendation.get('stop_loss', 0.0),
                recommendation.get('take_profit', 0.0),
                recommendation.get('position_size_pct', 0.0),
                recommendation.get('max_loss_amount', 0.0),
                recommendation.get('expected_return_pct', 0.0),
                recommendation.get('advisor_name', 'AutoScheduler'),
                recommendation.get('advisor_version', 'v0.2'),
                recommendation.get('strategy', 'Unknown'),
                reasoning,
                recommendation.get('confidence', 'MEDIUM'),
                key_factors,
                recommendation.get('data_timestamp', datetime.now().isoformat()),
                recommendation.get('data_source', 'Unknown'),
                datetime.now().isoformat(),
                recommendation.get('data_freshness', 'realtime'),
                recommendation.get('is_automated', True)
            ))

            conn.commit()
            self.logger.debug(f"Saved recommendation: {recommendation.get('symbol')} - {recommendation.get('action')}")

        except Exception as e:
            self.logger.error(f"Failed to save recommendation: {e}")
            self.logger.exception(e)
        finally:
            conn.close()

    def _log_execution(
        self,
        status: str,
        symbols_processed: int,
        recommendations_generated: int,
        data_source: str,
        error_message: str = None,
        duration_seconds: float = 0
    ):
        """Log scheduler execution to database (T091).

        Args:
            status: Execution status (SUCCESS/FAILURE/PARTIAL)
            symbols_processed: Number of symbols processed
            recommendations_generated: Number of recommendations generated
            data_source: Data source used (Tushare/AKShare/Cache)
            error_message: Error message if any
            duration_seconds: Execution duration in seconds
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO scheduler_log (
                    execution_time, status, symbols_processed,
                    recommendations_generated, data_source,
                    error_message, duration_seconds, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                status,
                symbols_processed,
                recommendations_generated,
                data_source,
                error_message,
                duration_seconds,
                datetime.now().isoformat()
            ))

            conn.commit()
            self.logger.info(f"Logged execution: {status}")

        except Exception as e:
            self.logger.error(f"Failed to log execution: {e}")
        finally:
            conn.close()
