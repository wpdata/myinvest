"""Livermore AI Advisor Implementation.

Generates explainable investment recommendations using Livermore strategy principles.

V0.2 Update: Now logs and includes data provenance (US5 - T015)
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import logging


class LivermoreAdvisor:
    """AI Advisor implementing Livermore trend-following strategy."""

    def __init__(self, prompt_version: str = "v1.0.0"):
        """Initialize Livermore advisor."""
        self.advisor_name = "Livermore"
        self.advisor_version = prompt_version
        self.strategy_name = "Trend Following"
        self.logger = logging.getLogger(__name__)

    def generate_recommendation(
        self,
        signal: Dict[str, Any],
        capital: float = 100000.0
    ) -> Dict[str, Any]:
        """Generate explainable investment recommendation.

        V0.2 Update (T015): Now logs and includes data provenance metadata.

        Args:
            signal: Trading signal from LivermoreStrategy.analyze()
            capital: Total capital available

        Returns:
            Investment recommendation with data provenance

        Raises:
            ValueError: If signal uses test fixtures in production
        """
        # Extract data metadata from signal (added in T013)
        data_source = signal.get('data_source', 'UNKNOWN')
        data_timestamp = signal.get('data_timestamp', None)
        data_freshness = signal.get('data_freshness', 'unknown')

        # VALIDATION: Ensure no test fixtures in production (US5 - T015)
        if "test_fixture" in data_source.lower():
            error_msg = (
                f"CRITICAL: Production recommendation using test fixtures! "
                f"data_source={data_source}. This violates Constitution Principle XI (Real Data Mandate). "
                f"All production recommendations MUST use real market data from Tushare/AKShare/Cache."
            )
            self.logger.error(f"[LivermoreAdvisor] {error_msg}")
            raise ValueError(error_msg)

        # Log data provenance (US5 - T015)
        symbol = signal.get('symbol', 'UNKNOWN')
        self.logger.info(
            f"[LivermoreAdvisor] Generating recommendation for {symbol} "
            f"with {data_source} data (freshness={data_freshness})"
        )

        if data_freshness == 'historical':
            self.logger.warning(
                f"[LivermoreAdvisor] ⚠️ Using historical data for {symbol} "
                f"(timestamp={data_timestamp}). Consider refreshing data for more accurate recommendations."
            )

        # Build reasoning with data context
        reasoning = self._build_reasoning(signal)

        # Include data provenance in recommendation (NEW in V0.2 - T015)
        recommendation = {
            "advisor_name": self.advisor_name,
            "advisor_version": self.advisor_version,
            "strategy_name": self.strategy_name,
            "symbol": symbol,
            "action": signal['action'],
            "entry_price": signal['entry_price'],
            "stop_loss": signal['stop_loss'],
            "take_profit": signal['take_profit'],
            "position_size_pct": signal['position_size_pct'],
            "max_loss": signal.get('max_loss_amount', signal.get('max_loss', 0)),
            "reasoning": reasoning,
            "confidence": signal.get('confidence', 'MEDIUM'),
            "key_factors": signal.get('key_factors', []),
            "generated_at": datetime.utcnow().isoformat(),
            "capital_context": capital,
            # Data provenance (NEW in V0.2 - US5)
            "data_source": data_source,
            "data_timestamp": data_timestamp,
            "data_freshness": data_freshness,
            "data_points": signal.get('data_points', None),
        }

        self.logger.info(
            f"[LivermoreAdvisor] ✅ Generated {signal['action']} recommendation for {symbol} "
            f"with {signal.get('confidence', 'MEDIUM')} confidence"
        )

        return recommendation

    def _build_reasoning(self, signal: Dict[str, Any]) -> str:
        """Build reasoning explanation."""
        action = signal['action']
        confidence = signal.get('confidence', 'MEDIUM')
        factors = signal.get('key_factors', [])

        parts = [f"基于Livermore策略，建议{action}（{confidence}置信度）。"]

        if factors:
            parts.append("关键因素：" + "、".join(factors))

        entry = signal['entry_price']
        stop = signal['stop_loss']
        profit = signal['take_profit']
        risk = abs(entry - stop)
        reward = abs(profit - entry)
        ratio = reward / risk if risk > 0 else 0

        parts.append(
            f"入场{entry}，止损{stop}，止盈{profit}。"
            f"风险收益比1:{ratio:.1f}。"
        )

        parts.append(f"仓位{signal['position_size_pct']:.1f}%，最大损失{signal['max_loss']:.0f}元。")

        return " ".join(parts)
