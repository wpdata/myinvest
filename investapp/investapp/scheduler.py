"""Automated Daily Scheduler for V0.3 (T011 - Watchlist Integration).

V0.3 Enhancement: Dynamic watchlist integration with multi-asset support.

Runs automated analysis every trading day at 8:00 PM (post-market close):
- Reads active symbols from watchlist database (no hardcoded lists)
- Supports stocks, futures, and options with asset-specific timing
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
from investlib_data.watchlist_db import WatchlistDB


logger = logging.getLogger(__name__)


class DailyScheduler:
    """Automated daily scheduler for investment analysis."""

    def __init__(
        self,
        symbols: List[str] = None,
        run_time: str = "20:00",  # 8:00 PM after market close
        capital: float = 100000.0,
        enabled: bool = True,
        db_path: str = "./data/myinvest.db",
        use_watchlist: bool = True
    ):
        """Initialize scheduler with V0.3 watchlist integration.

        Args:
            symbols: Legacy: List of symbols to analyze (deprecated - use watchlist instead)
            run_time: Daily run time in HH:MM format (default: 20:00)
            capital: Total capital for position sizing (default: 100000)
            enabled: Enable/disable scheduler (default: True)
            db_path: Path to database (default: ./data/myinvest.db)
            use_watchlist: Use watchlist database instead of hardcoded symbols (default: True)
        """
        self.run_time = run_time
        self.capital = capital
        self.enabled = enabled
        self.use_watchlist = use_watchlist
        self.db_path = db_path

        # V0.3: Initialize watchlist database connection
        self.watchlist_db = WatchlistDB(db_path)

        # V0.3: Load symbols from watchlist or use legacy list
        if use_watchlist:
            self.symbols = self._load_symbols_from_watchlist()
            logger.info(f"[DailyScheduler] V0.3: Loaded {len(self.symbols)} active symbols from watchlist")
        else:
            # Legacy fallback for backward compatibility
            self.symbols = symbols or [
                "600519.SH",  # Moutai
                "000858.SZ",  # Wuliangye
                "600036.SH",  # China Merchants Bank
                "601318.SH",  # Ping An Insurance
                "000001.SZ"   # Ping An Bank
            ]
            logger.warning(f"[DailyScheduler] Legacy mode: Using hardcoded symbols ({len(self.symbols)})")

        # Initialize scheduler with SQLAlchemy job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=DATABASE_URL)
        }
        self.scheduler = BackgroundScheduler(jobstores=jobstores)

        # Strategy
        self.fusion = FusionStrategy()

        logger.info(f"[DailyScheduler] Initialized with {len(self.symbols)} symbols, run_time={run_time}")

    def _load_symbols_from_watchlist(self) -> List[str]:
        """Load active symbols from watchlist database (V0.3).

        Returns:
            List of active symbol strings
        """
        try:
            watchlist_items = self.watchlist_db.get_all_symbols(status='active')
            symbols = [item['symbol'] for item in watchlist_items]
            logger.info(f"[DailyScheduler] Loaded {len(symbols)} active symbols from watchlist")
            return symbols
        except Exception as e:
            logger.error(f"[DailyScheduler] Failed to load watchlist: {e}. Using empty list.")
            return []

    def _detect_asset_type(self, symbol: str) -> str:
        """Detect asset type from symbol format (V0.3 - FR-078).

        Args:
            symbol: Symbol string (e.g., '600519.SH', 'IF2506.CFFEX', '10005102.SH')

        Returns:
            'stock', 'futures', or 'option'
        """
        # Check watchlist database first for accurate type
        try:
            watchlist_items = self.watchlist_db.get_all_symbols(status='all')
            for item in watchlist_items:
                if item['symbol'] == symbol:
                    return item['contract_type']
        except Exception as e:
            logger.warning(f"[DailyScheduler] Could not query watchlist for {symbol}: {e}")

        # Fallback: Pattern-based detection
        if '.CFFEX' in symbol or '.CZCE' in symbol or '.DCE' in symbol or '.SHFE' in symbol:
            return 'futures'
        elif symbol.startswith('1000'):  # Options typically start with 1000
            return 'option'
        else:
            return 'stock'

    def _get_trading_hours(self, asset_type: str) -> Dict[str, str]:
        """Get trading hours for different asset types (V0.3 - FR-079).

        Args:
            asset_type: 'stock', 'futures', or 'option'

        Returns:
            Dict with 'start' and 'end' times
        """
        trading_hours = {
            'stock': {
                'start': '09:30',
                'end': '15:00',
                'description': 'A-share market hours'
            },
            'futures': {
                'start': '09:00',
                'end': '15:15',  # Day session (night session: 21:00-02:30)
                'description': 'CFFEX futures day session'
            },
            'option': {
                'start': '09:30',
                'end': '15:00',  # Align with underlying stock
                'description': 'Stock options (align with underlying)'
            }
        }
        return trading_hours.get(asset_type, trading_hours['stock'])

    def refresh_symbols(self) -> int:
        """Refresh symbols from watchlist without restarting scheduler (V0.3).

        Returns:
            Number of active symbols loaded
        """
        if self.use_watchlist:
            old_count = len(self.symbols)
            self.symbols = self._load_symbols_from_watchlist()
            new_count = len(self.symbols)

            logger.info(
                f"[DailyScheduler] Watchlist refreshed: {old_count} → {new_count} symbols "
                f"({new_count - old_count:+d})"
            )
            return new_count
        else:
            logger.warning("[DailyScheduler] Cannot refresh in legacy mode (use_watchlist=False)")
            return len(self.symbols)

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

        V0.3: Refreshes watchlist before each run, supports multi-asset types.

        Returns:
            Summary dict with success/failure counts
        """
        session = SessionLocal()
        start_time = datetime.now()

        logger.info(f"[DailyScheduler] 🚀 Starting daily analysis at {start_time}")

        # V0.3: Refresh symbols from watchlist before each run
        if self.use_watchlist:
            symbol_count = self.refresh_symbols()
            logger.info(f"[DailyScheduler] Watchlist refreshed: {symbol_count} active symbols")

        results = {
            'start_time': start_time,
            'symbols_analyzed': 0,
            'recommendations_generated': 0,
            'errors': 0,
            'error_details': [],
            'asset_types': {'stock': 0, 'futures': 0, 'option': 0}  # V0.3: Track asset type distribution
        }

        try:
            for symbol in self.symbols:
                try:
                    # V0.3: Detect asset type and get trading hours
                    asset_type = self._detect_asset_type(symbol)
                    trading_hours = self._get_trading_hours(asset_type)
                    results['asset_types'][asset_type] += 1

                    logger.info(
                        f"[DailyScheduler] Analyzing {symbol} "
                        f"({asset_type}, hours: {trading_hours['start']}-{trading_hours['end']})..."
                    )

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

            # V0.3: Enhanced log message with asset type breakdown
            asset_breakdown = ", ".join([
                f"{count} {atype}{'s' if count != 1 else ''}"
                for atype, count in results['asset_types'].items()
                if count > 0
            ])

            log_message = (
                f"Analyzed {results['symbols_analyzed']} symbols ({asset_breakdown}), "
                f"generated {results['recommendations_generated']} recommendations"
            )

            log_entry = SchedulerLog(
                run_timestamp=start_time,
                status=SchedulerStatus.SUCCESS if results['errors'] == 0 else SchedulerStatus.PARTIAL_SUCCESS,
                symbols_analyzed=results['symbols_analyzed'],
                recommendations_generated=results['recommendations_generated'],
                errors_encountered=results['errors'],
                duration_seconds=duration,
                log_message=log_message
            )
            session.add(log_entry)
            session.commit()

            results['end_time'] = end_time
            results['duration_seconds'] = duration

            logger.info(
                f"[DailyScheduler] ✅ Completed in {duration:.1f}s: "
                f"{results['symbols_analyzed']} analyzed ({asset_breakdown}), "
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
        """Get scheduler status with V0.3 watchlist information.

        Returns:
            Status dictionary
        """
        status = {
            'running': self.scheduler.running if self.scheduler else False,
            'enabled': self.enabled,
            'run_time': self.run_time,
            'symbols_count': len(self.symbols),
            'symbols': self.symbols,
            'next_run': self.scheduler.get_jobs()[0].next_run_time if self.scheduler and self.scheduler.get_jobs() else None,
            'use_watchlist': self.use_watchlist  # V0.3
        }

        # V0.3: Add watchlist statistics
        if self.use_watchlist:
            try:
                all_watchlist = self.watchlist_db.get_all_symbols(status='all')
                active_count = sum(1 for item in all_watchlist if item['status'] == 'active')
                paused_count = len(all_watchlist) - active_count

                # Count by asset type
                asset_counts = {'stock': 0, 'futures': 0, 'option': 0}
                for item in all_watchlist:
                    if item['status'] == 'active':
                        asset_type = item.get('contract_type', 'stock')
                        asset_counts[asset_type] = asset_counts.get(asset_type, 0) + 1

                status['watchlist'] = {
                    'total': len(all_watchlist),
                    'active': active_count,
                    'paused': paused_count,
                    'asset_types': asset_counts
                }
            except Exception as e:
                logger.warning(f"[DailyScheduler] Could not fetch watchlist status: {e}")
                status['watchlist'] = {'error': str(e)}

        return status


# Global scheduler instance (singleton)
_scheduler_instance: Optional[DailyScheduler] = None


def get_scheduler() -> DailyScheduler:
    """Get global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DailyScheduler()
    return _scheduler_instance


def init_scheduler(
    symbols: List[str] = None,
    run_time: str = "20:00",
    enabled: bool = True,
    db_path: str = "./data/myinvest.db",
    use_watchlist: bool = True
) -> DailyScheduler:
    """Initialize and start scheduler with V0.3 watchlist support.

    Args:
        symbols: Legacy: List of symbols to track (deprecated - use watchlist)
        run_time: Daily run time (HH:MM)
        enabled: Enable scheduler
        db_path: Path to database (default: ./data/myinvest.db)
        use_watchlist: Use watchlist database (default: True)

    Returns:
        Scheduler instance
    """
    global _scheduler_instance
    _scheduler_instance = DailyScheduler(
        symbols=symbols,
        run_time=run_time,
        enabled=enabled,
        db_path=db_path,
        use_watchlist=use_watchlist
    )
    if enabled:
        _scheduler_instance.start()
    return _scheduler_instance
