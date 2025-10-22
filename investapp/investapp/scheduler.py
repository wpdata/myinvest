"""Automated Daily Scheduler for V0.2 (T079-T081).

Runs automated analysis every trading day at 8:00 PM (post-market close):
- Fetches fresh market data
- Runs Fusion Strategy (Livermore + Kroll)
- Generates investment recommendations
- Logs to database and scheduler_log table
- Sends notifications (if configured)

Uses APScheduler with persistent job store.
"""

import logging
from datetime import datetime, time
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy.orm import Session

from investlib_quant.fusion_strategy import FusionStrategy
from investlib_data.database import SessionLocal, DATABASE_URL
from investlib_data.models import InvestmentRecommendation, SchedulerLog, SchedulerStatus


logger = logging.getLogger(__name__)


class DailyScheduler:
    """Automated daily scheduler for investment analysis."""

    def __init__(
        self,
        symbols: List[str] = None,
        run_time: str = "20:00",  # 8:00 PM after market close
        capital: float = 100000.0,
        enabled: bool = True
    ):
        """Initialize scheduler.

        Args:
            symbols: List of symbols to analyze (default: A-share blue chips)
            run_time: Daily run time in HH:MM format (default: 20:00)
            capital: Total capital for position sizing (default: 100000)
            enabled: Enable/disable scheduler (default: True)
        """
        self.symbols = symbols or [
            "600519.SH",  # Moutai
            "000858.SZ",  # Wuliangye
            "600036.SH",  # China Merchants Bank
            "601318.SH",  # Ping An Insurance
            "000001.SZ"   # Ping An Bank
        ]
        self.run_time = run_time
        self.capital = capital
        self.enabled = enabled

        # Initialize scheduler with SQLAlchemy job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=DATABASE_URL)
        }
        self.scheduler = BackgroundScheduler(jobstores=jobstores)

        # Strategy
        self.fusion = FusionStrategy()

        logger.info(f"[DailyScheduler] Initialized with {len(self.symbols)} symbols, run_time={run_time}")

    def start(self) -> None:
        """Start the scheduler."""
        if not self.enabled:
            logger.warning("[DailyScheduler] Scheduler is disabled")
            return

        # Parse run time
        hour, minute = map(int, self.run_time.split(':'))

        # Add daily job
        self.scheduler.add_job(
            func=self.run_daily_analysis,
            trigger=CronTrigger(hour=hour, minute=minute),  # Daily at specified time
            id='daily_analysis',
            name='Daily Investment Analysis',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"[DailyScheduler] ✅ Started - will run daily at {self.run_time}")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("[DailyScheduler] Stopped")

    def run_daily_analysis(self) -> Dict[str, Any]:
        """Run daily analysis for all symbols (scheduled task).

        Returns:
            Summary dict with success/failure counts
        """
        session = SessionLocal()
        start_time = datetime.now()

        logger.info(f"[DailyScheduler] 🚀 Starting daily analysis at {start_time}")

        results = {
            'start_time': start_time,
            'symbols_analyzed': 0,
            'recommendations_generated': 0,
            'errors': 0,
            'error_details': []
        }

        try:
            for symbol in self.symbols:
                try:
                    logger.info(f"[DailyScheduler] Analyzing {symbol}...")

                    # Run fusion strategy
                    signal = self.fusion.analyze(
                        symbol=symbol,
                        capital=self.capital,
                        use_cache=False  # Force fresh data for daily run
                    )

                    # Save recommendation to database
                    self._save_recommendation(session, signal)

                    results['symbols_analyzed'] += 1
                    if signal['action'] != 'HOLD':
                        results['recommendations_generated'] += 1

                    logger.info(f"[DailyScheduler] ✅ {symbol}: {signal['action']} ({signal['confidence']})")

                except Exception as e:
                    logger.error(f"[DailyScheduler] ❌ Failed to analyze {symbol}: {e}")
                    results['errors'] += 1
                    results['error_details'].append({'symbol': symbol, 'error': str(e)})

            # Log scheduler run
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            log_entry = SchedulerLog(
                run_timestamp=start_time,
                status=SchedulerStatus.SUCCESS if results['errors'] == 0 else SchedulerStatus.PARTIAL_SUCCESS,
                symbols_analyzed=results['symbols_analyzed'],
                recommendations_generated=results['recommendations_generated'],
                errors_encountered=results['errors'],
                duration_seconds=duration,
                log_message=f"Analyzed {results['symbols_analyzed']} symbols, generated {results['recommendations_generated']} recommendations"
            )
            session.add(log_entry)
            session.commit()

            results['end_time'] = end_time
            results['duration_seconds'] = duration

            logger.info(
                f"[DailyScheduler] ✅ Completed in {duration:.1f}s: "
                f"{results['symbols_analyzed']} analyzed, "
                f"{results['recommendations_generated']} recommendations, "
                f"{results['errors']} errors"
            )

        except Exception as e:
            logger.error(f"[DailyScheduler] ❌ Critical error in daily analysis: {e}")
            results['critical_error'] = str(e)

            # Log failure
            log_entry = SchedulerLog(
                run_timestamp=start_time,
                status=SchedulerStatus.FAILURE,
                symbols_analyzed=results['symbols_analyzed'],
                recommendations_generated=results['recommendations_generated'],
                errors_encountered=results['errors'] + 1,
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                log_message=f"FAILED: {str(e)}"
            )
            session.add(log_entry)
            session.commit()

        finally:
            session.close()

        return results

    def run_now(self) -> Dict[str, Any]:
        """Run analysis immediately (manual trigger).

        Returns:
            Results dictionary from run_daily_analysis()
        """
        logger.info("[DailyScheduler] Manual trigger - running analysis now")
        return self.run_daily_analysis()

    def _save_recommendation(self, session: Session, signal: Dict[str, Any]) -> None:
        """Save recommendation to database.

        Args:
            session: Database session
            signal: Signal dictionary from fusion strategy
        """
        rec = InvestmentRecommendation(
            symbol=signal['symbol'],
            action=signal['action'],
            confidence=signal['confidence'],
            entry_price=signal.get('entry_price'),
            stop_loss=signal.get('stop_loss'),
            take_profit=signal.get('take_profit'),
            position_size_pct=signal.get('position_size_pct'),
            reasoning="; ".join(signal.get('fusion_factors', [])),
            data_source=signal.get('data_source'),
            market_data_timestamp=datetime.fromisoformat(signal['data_timestamp']) if signal.get('data_timestamp') else None,
            data_freshness=signal.get('data_freshness'),
            is_automated=True,  # Automated by scheduler
            created_at=datetime.now()
        )
        session.add(rec)
        session.commit()

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status.

        Returns:
            Status dictionary
        """
        return {
            'running': self.scheduler.running if self.scheduler else False,
            'enabled': self.enabled,
            'run_time': self.run_time,
            'symbols_count': len(self.symbols),
            'symbols': self.symbols,
            'next_run': self.scheduler.get_jobs()[0].next_run_time if self.scheduler and self.scheduler.get_jobs() else None
        }


# Global scheduler instance (singleton)
_scheduler_instance: Optional[DailyScheduler] = None


def get_scheduler() -> DailyScheduler:
    """Get global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DailyScheduler()
    return _scheduler_instance


def init_scheduler(symbols: List[str] = None, run_time: str = "20:00", enabled: bool = True) -> DailyScheduler:
    """Initialize and start scheduler.

    Args:
        symbols: List of symbols to track
        run_time: Daily run time (HH:MM)
        enabled: Enable scheduler

    Returns:
        Scheduler instance
    """
    global _scheduler_instance
    _scheduler_instance = DailyScheduler(symbols=symbols, run_time=run_time, enabled=enabled)
    if enabled:
        _scheduler_instance.start()
    return _scheduler_instance
