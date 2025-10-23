"""
MyInvest V0.3 - Parameter Optimization Library
Automated grid search with walk-forward validation and overfitting detection.
"""

__version__ = "0.3.0"

from investlib_optimizer.grid_search import GridSearchOptimizer
from investlib_optimizer.walk_forward import WalkForwardValidator
from investlib_optimizer.overfitting import OverfittingDetector
from investlib_optimizer.visualizer import ParameterVisualizer

__all__ = [
    "GridSearchOptimizer",
    "WalkForwardValidator",
    "OverfittingDetector",
    "ParameterVisualizer"
]
