"""
MyInvest V0.3 - Overfitting Detection (T022, FR-017)
Detects when strategy performance degrades from training to testing.
"""

import logging
from typing import Dict, Tuple


logger = logging.getLogger(__name__)


class OverfittingDetector:
    """Overfitting detection using train/test Sharpe divergence (FR-017).

    Threshold: 0.5 (from specification)
    - If train_sharpe - test_sharpe > 0.5 → Overfitting warning

    Examples:
        - Train Sharpe=2.5, Test Sharpe=2.3 → Divergence=0.2 → OK
        - Train Sharpe=2.5, Test Sharpe=0.8 → Divergence=1.7 → OVERFITTED ⚠️
    """

    def __init__(self, threshold: float = 0.5):
        """Initialize overfitting detector.

        Args:
            threshold: Divergence threshold for overfitting warning (default: 0.5)
        """
        self.threshold = threshold

    def calculate_overfitting_score(
        self,
        train_metrics: Dict[str, float],
        test_metrics: Dict[str, float]
    ) -> float:
        """Calculate overfitting score (Sharpe ratio divergence).

        Args:
            train_metrics: Training period metrics (must contain 'sharpe_ratio')
            test_metrics: Testing period metrics (must contain 'sharpe_ratio')

        Returns:
            float: sharpe_divergence = train_sharpe - test_sharpe

        Formula (FR-017):
            divergence = training_sharpe - testing_sharpe

        Higher values indicate stronger overfitting signal.
        """
        train_sharpe = train_metrics.get('sharpe_ratio', 0)
        test_sharpe = test_metrics.get('sharpe_ratio', 0)

        divergence = train_sharpe - test_sharpe

        logger.debug(
            f"[OverfittingDetector] Train Sharpe={train_sharpe:.2f}, "
            f"Test Sharpe={test_sharpe:.2f}, Divergence={divergence:.2f}"
        )

        return divergence

    def is_overfitted(
        self,
        train_sharpe: float,
        test_sharpe: float,
        threshold: float = None
    ) -> bool:
        """Check if strategy is overfitted based on Sharpe divergence.

        Args:
            train_sharpe: Training period Sharpe ratio
            test_sharpe: Testing period Sharpe ratio
            threshold: Custom threshold (default: use instance threshold)

        Returns:
            bool: True if overfitted (divergence > threshold)

        Examples:
            >>> detector = OverfittingDetector(threshold=0.5)
            >>> detector.is_overfitted(train_sharpe=2.5, test_sharpe=0.8)
            True  # Divergence = 1.7 > 0.5
            >>> detector.is_overfitted(train_sharpe=2.5, test_sharpe=2.3)
            False  # Divergence = 0.2 < 0.5
        """
        threshold = threshold if threshold is not None else self.threshold
        divergence = train_sharpe - test_sharpe

        return divergence > threshold

    def generate_warning_message(
        self,
        train_sharpe: float,
        test_sharpe: float
    ) -> str:
        """Generate Chinese warning message for overfitting.

        Args:
            train_sharpe: Training Sharpe ratio
            test_sharpe: Testing Sharpe ratio

        Returns:
            str: Chinese warning message

        Example output:
            "警告：检测到过拟合风险！训练集夏普比率 2.50，测试集夏普比率 0.80，
             差距 1.70 超过阈值 0.5"
        """
        divergence = train_sharpe - test_sharpe

        if divergence > self.threshold:
            message = (
                f"⚠️ 警告：检测到过拟合风险！"
                f"训练集夏普比率 {train_sharpe:.2f}，"
                f"测试集夏普比率 {test_sharpe:.2f}，"
                f"差距 {divergence:.2f} 超过阈值 {self.threshold:.1f}"
            )
        else:
            message = (
                f"✓ 未检测到过拟合：训练集夏普比率 {train_sharpe:.2f}，"
                f"测试集夏普比率 {test_sharpe:.2f}，"
                f"差距 {divergence:.2f} 在可接受范围内（阈值 {self.threshold:.1f}）"
            )

        return message

    def assess_robustness(
        self,
        train_metrics: Dict[str, float],
        test_metrics: Dict[str, float]
    ) -> Dict[str, any]:
        """Comprehensive robustness assessment.

        Args:
            train_metrics: Training metrics
            test_metrics: Testing metrics

        Returns:
            Dict with assessment results:
                - is_overfitted: bool
                - divergence: float
                - warning_message: str (Chinese)
                - risk_level: 'low' | 'medium' | 'high'
                - recommendation: str (Chinese)
        """
        divergence = self.calculate_overfitting_score(train_metrics, test_metrics)
        is_overfitted = divergence > self.threshold

        # Determine risk level
        if divergence < 0.3:
            risk_level = 'low'
            risk_color = '🟢'
            recommendation = "策略表现稳定，可以考虑实盘应用"
        elif divergence < self.threshold:
            risk_level = 'medium'
            risk_color = '🟡'
            recommendation = "策略有轻微过拟合迹象，建议谨慎使用"
        else:
            risk_level = 'high'
            risk_color = '🔴'
            recommendation = "策略过拟合风险高，不建议实盘使用，需要重新优化"

        warning_message = self.generate_warning_message(
            train_metrics['sharpe_ratio'],
            test_metrics['sharpe_ratio']
        )

        return {
            'is_overfitted': is_overfitted,
            'divergence': divergence,
            'warning_message': warning_message,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'recommendation': recommendation,
            'train_sharpe': train_metrics['sharpe_ratio'],
            'test_sharpe': test_metrics['sharpe_ratio'],
            'threshold': self.threshold
        }
