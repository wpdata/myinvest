"""Scheduler Application Launcher.

Run this to start the automated daily scheduler in the background.
The scheduler will run at 08:30 Beijing time every trading day.
"""

import logging
import sys
import os
from investapp.scheduler.daily_tasks import DailyScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/pw/ai/myinvest/logs/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Start the scheduler."""
    logger.info("=" * 60)
    logger.info("MyInvest V0.2 - Daily Scheduler Starting")
    logger.info("=" * 60)

    # Initialize scheduler
    db_path = "/Users/pw/ai/myinvest/data/myinvest.db"
    scheduler = DailyScheduler(db_path=db_path)

    try:
        # Start scheduler
        scheduler.start()

        logger.info("✅ Scheduler is running. Next execution at 08:30 Beijing time.")
        logger.info("Press Ctrl+C to stop.")

        # Keep the script running
        import time
        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop()
        logger.info("✅ Scheduler stopped.")

    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}", exc_info=True)
        scheduler.stop()


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('/Users/pw/ai/myinvest/logs', exist_ok=True)

    main()
