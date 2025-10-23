"""
MyInvest V0.3 - Memory Monitoring and Adaptive Scaling (T016)
Monitors system memory usage and dynamically adjusts worker count.
"""

import logging
import psutil
from typing import Dict, Any
from math import floor


logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor system memory and provide adaptive worker scaling.

    Algorithm (from tasks.md T016):
    - If memory_usage < 75%: return base_workers
    - If memory_usage >= 75%: return max(2, base_workers - floor((memory_usage - 75) / 10))

    Examples:
    - 70% memory usage, 8 base workers → 8 workers (no reduction)
    - 85% memory usage, 8 base workers → 7 workers (reduce by 1)
    - 95% memory usage, 8 base workers → 6 workers (reduce by 2)
    - 105% memory usage, 8 base workers → 5 workers (reduce by 3)
    - But always keep minimum 2 workers
    """

    def __init__(
        self,
        warning_threshold: float = 75.0,
        critical_threshold: float = 90.0
    ):
        """Initialize memory monitor.

        Args:
            warning_threshold: Warning level (default: 75%)
            critical_threshold: Critical level (default: 90%)
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def get_memory_usage(self) -> float:
        """Get current system memory usage as percentage.

        Returns:
            float: Memory usage percentage (0-100+)
        """
        mem = psutil.virtual_memory()
        return mem.percent

    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information.

        Returns:
            Dict with total, available, used, percent
        """
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024 ** 3),
            'available_gb': mem.available / (1024 ** 3),
            'used_gb': mem.used / (1024 ** 3),
            'percent': mem.percent,
            'status': self.get_status(mem.percent)
        }

    def get_status(self, memory_percent: float) -> str:
        """Get memory status label.

        Args:
            memory_percent: Memory usage percentage

        Returns:
            'normal', 'warning', or 'critical'
        """
        if memory_percent < self.warning_threshold:
            return 'normal'
        elif memory_percent < self.critical_threshold:
            return 'warning'
        else:
            return 'critical'

    def get_available_workers(
        self,
        base_workers: int,
        current_usage: float = None
    ) -> int:
        """Calculate adjusted worker count based on memory usage.

        Implements the adaptive scaling algorithm from tasks.md T016.

        Args:
            base_workers: Desired number of workers (e.g., CPU count)
            current_usage: Current memory usage % (if None, will query)

        Returns:
            int: Adjusted worker count (minimum 2)

        Examples:
            >>> monitor = MemoryMonitor()
            >>> monitor.get_available_workers(8, current_usage=70)
            8  # No reduction - below threshold
            >>> monitor.get_available_workers(8, current_usage=85)
            7  # Reduce by 1
            >>> monitor.get_available_workers(8, current_usage=95)
            6  # Reduce by 2
        """
        if current_usage is None:
            current_usage = self.get_memory_usage()

        # Algorithm from tasks.md T016
        if current_usage < self.warning_threshold:
            # Normal operation - use all workers
            return base_workers
        else:
            # Memory pressure - reduce workers
            reduction = floor((current_usage - self.warning_threshold) / 10)
            adjusted_workers = base_workers - reduction

            # Enforce minimum of 2 workers
            return max(2, adjusted_workers)

    def log_status(self) -> None:
        """Log current memory status."""
        info = self.get_memory_info()
        status = info['status']

        if status == 'normal':
            logger.info(
                f"[MemoryMonitor] Memory: {info['percent']:.1f}% "
                f"({info['used_gb']:.1f}GB / {info['total_gb']:.1f}GB) - {status.upper()}"
            )
        elif status == 'warning':
            logger.warning(
                f"[MemoryMonitor] ⚠️ Memory: {info['percent']:.1f}% "
                f"({info['used_gb']:.1f}GB / {info['total_gb']:.1f}GB) - {status.upper()}"
            )
        else:  # critical
            logger.error(
                f"[MemoryMonitor] 🔴 Memory: {info['percent']:.1f}% "
                f"({info['used_gb']:.1f}GB / {info['total_gb']:.1f}GB) - {status.upper()}"
            )

    def should_reduce_workers(self, current_usage: float = None) -> bool:
        """Check if worker count should be reduced.

        Args:
            current_usage: Current memory usage % (if None, will query)

        Returns:
            bool: True if workers should be reduced
        """
        if current_usage is None:
            current_usage = self.get_memory_usage()

        return current_usage >= self.warning_threshold

    def get_cpu_count(self) -> int:
        """Get number of CPU cores available.

        Returns:
            int: Number of logical CPU cores
        """
        return psutil.cpu_count(logical=True)

    def get_recommended_workers(self) -> int:
        """Get recommended worker count based on current system state.

        Considers both CPU cores and memory availability.

        Returns:
            int: Recommended number of workers
        """
        cpu_count = self.get_cpu_count()
        memory_usage = self.get_memory_usage()

        # Start with CPU count as base
        recommended = self.get_available_workers(cpu_count, memory_usage)

        logger.info(
            f"[MemoryMonitor] Recommended workers: {recommended} "
            f"(CPU cores: {cpu_count}, Memory: {memory_usage:.1f}%)"
        )

        return recommended
