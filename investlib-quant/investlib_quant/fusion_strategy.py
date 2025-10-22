"""Multi-Strategy Fusion (T046-T048).

Combines Livermore (trend-following) + Kroll (risk-focused) strategies with weighted voting.

Fusion Logic:
1. Run both strategies in parallel
2. Weight signals: Livermore 60%, Kroll 40% (trend priority with risk check)
3. Agreement rules:
   - Both BUY → STRONG_BUY (confidence = min of both)
   - Both SELL → STRONG_SELL
   - Disagree → HOLD (conflicting signals)
   - One BUY + one HOLD → BUY with reduced confidence
4. Position sizing: Use more conservative (smaller) of the two
5. Risk metrics: Use tighter stop-loss of the two
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from investlib_quant.livermore_strategy import LivermoreStrategy
from investlib_quant.kroll_strategy import KrollStrategy


class FusionStrategy:
    """Multi-strategy fusion combining Livermore + Kroll."""

    def __init__(
        self,
        livermore_weight: float = 0.6,
        kroll_weight: float = 0.4,
        enable_livermore: bool = True,
        enable_kroll: bool = True
    ):
        """Initialize fusion strategy.

        Args:
            livermore_weight: Weight for Livermore strategy (default 0.6)
            kroll_weight: Weight for Kroll strategy (default 0.4)
            enable_livermore: Enable Livermore strategy (default True)
            enable_kroll: Enable Kroll strategy (default True)
        """
        self.livermore_weight = livermore_weight
        self.kroll_weight = kroll_weight
        self.enable_livermore = enable_livermore
        self.enable_kroll = enable_kroll

        # Initialize strategies
        self.livermore = LivermoreStrategy() if enable_livermore else None
        self.kroll = KrollStrategy() if enable_kroll else None

        self.logger = logging.getLogger(__name__)

    def fuse_signals(
        self,
        livermore_signal: Optional[Dict[str, Any]],
        kroll_signal: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fuse signals from multiple strategies using weighted voting.

        Args:
            livermore_signal: Signal from Livermore strategy (or None if disabled)
            kroll_signal: Signal from Kroll strategy (or None if disabled)

        Returns:
            Fused signal dictionary
        """
        # Handle single-strategy cases
        if livermore_signal is None and kroll_signal is None:
            raise ValueError("At least one strategy must be enabled")
        if livermore_signal is None:
            return self._wrap_single_signal(kroll_signal, 'Kroll')
        if kroll_signal is None:
            return self._wrap_single_signal(livermore_signal, 'Livermore')

        # Extract actions
        liv_action = livermore_signal['action']
        kroll_action = kroll_signal['action']

        # Extract confidences (map to numeric scores)
        confidence_map = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        liv_conf_num = confidence_map.get(livermore_signal['confidence'], 2)
        kroll_conf_num = confidence_map.get(kroll_signal['confidence'], 2)

        # Fusion logic
        fusion_factors = []

        # Case 1: Both agree on BUY
        if liv_action == 'BUY' and kroll_action == 'BUY':
            final_action = 'STRONG_BUY' if liv_conf_num >= 2 and kroll_conf_num >= 2 else 'BUY'
            # Confidence = minimum of both (conservative)
            final_conf_num = min(liv_conf_num, kroll_conf_num)
            fusion_factors.append("✓ AGREEMENT: Both strategies signal BUY")
            fusion_factors.append(f"Livermore: {livermore_signal['confidence']}, Kroll: {kroll_signal['confidence']}")

        # Case 2: Both agree on SELL
        elif liv_action == 'SELL' and kroll_action == 'SELL':
            final_action = 'STRONG_SELL' if liv_conf_num >= 2 and kroll_conf_num >= 2 else 'SELL'
            final_conf_num = min(liv_conf_num, kroll_conf_num)
            fusion_factors.append("✓ AGREEMENT: Both strategies signal SELL")

        # Case 3: Both HOLD
        elif liv_action == 'HOLD' and kroll_action == 'HOLD':
            final_action = 'HOLD'
            final_conf_num = 1  # LOW
            fusion_factors.append("Both strategies recommend HOLD")

        # Case 4: One BUY, one HOLD → Reduced confidence BUY
        elif (liv_action == 'BUY' and kroll_action == 'HOLD') or \
             (liv_action == 'HOLD' and kroll_action == 'BUY'):
            final_action = 'BUY'
            final_conf_num = 1  # Reduce to LOW confidence
            fusion_factors.append("⚠ PARTIAL AGREEMENT: One BUY, one HOLD → Conservative BUY")
            fusion_factors.append(f"Livermore={liv_action}, Kroll={kroll_action}")

        # Case 5: One SELL, one HOLD → Reduced confidence SELL
        elif (liv_action == 'SELL' and kroll_action == 'HOLD') or \
             (liv_action == 'HOLD' and kroll_action == 'SELL'):
            final_action = 'SELL'
            final_conf_num = 1
            fusion_factors.append("⚠ PARTIAL AGREEMENT: One SELL, one HOLD → Conservative SELL")

        # Case 6: Conflicting signals (BUY vs SELL) → HOLD
        else:
            final_action = 'HOLD'
            final_conf_num = 1
            fusion_factors.append("✗ CONFLICT: Strategies disagree → HOLD for safety")
            fusion_factors.append(f"Livermore={liv_action}, Kroll={kroll_action}")

        # Map confidence number back to label
        reverse_map = {1: 'LOW', 2: 'MEDIUM', 3: 'HIGH'}
        final_confidence = reverse_map[final_conf_num]

        # Choose more conservative position size (smaller of the two)
        liv_position = livermore_signal.get('position_size_pct', 15)
        kroll_position = kroll_signal.get('position_size_pct', 12)
        final_position = min(liv_position, kroll_position)
        fusion_factors.append(f"Position size: {final_position}% (min of Livermore={liv_position}%, Kroll={kroll_position}%)")

        # Choose tighter stop-loss (closer to entry)
        liv_stop = livermore_signal.get('stop_loss', 0)
        kroll_stop = kroll_signal.get('stop_loss', 0)
        entry_price = livermore_signal.get('entry_price', kroll_signal.get('entry_price', 0))

        # Tighter stop = higher value for BUY, lower for SELL
        if final_action in ['BUY', 'STRONG_BUY']:
            final_stop_loss = max(liv_stop, kroll_stop)  # Higher = tighter
            fusion_factors.append(f"Stop-loss: {final_stop_loss:.2f} (tighter of {liv_stop:.2f}, {kroll_stop:.2f})")
        else:
            final_stop_loss = (liv_stop + kroll_stop) / 2 if liv_stop and kroll_stop else (liv_stop or kroll_stop)

        # Use Kroll's take-profit (more conservative)
        final_take_profit = kroll_signal.get('take_profit', livermore_signal.get('take_profit', entry_price))

        # Calculate weighted risk level
        liv_risk = self._risk_to_score(livermore_signal.get('risk_level', 'MEDIUM'))
        kroll_risk = self._risk_to_score(kroll_signal.get('risk_level', 'MEDIUM'))
        weighted_risk = liv_risk * self.livermore_weight + kroll_risk * self.kroll_weight
        final_risk = self._score_to_risk(weighted_risk)

        return {
            'action': final_action,
            'confidence': final_confidence,
            'fusion_factors': fusion_factors,
            'entry_price': entry_price,
            'stop_loss': final_stop_loss,
            'take_profit': final_take_profit,
            'position_size_pct': final_position,
            'risk_level': final_risk,
            # Individual signals for transparency
            'livermore_signal': {
                'action': liv_action,
                'confidence': livermore_signal['confidence'],
                'weight': self.livermore_weight
            },
            'kroll_signal': {
                'action': kroll_action,
                'confidence': kroll_signal['confidence'],
                'weight': self.kroll_weight
            }
        }

    def analyze_data(
        self,
        market_data,
        symbol: str,
        capital: float = 100000.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze provided market data with multi-strategy fusion (for backtesting).

        This method is used by backtesting to avoid redundant API calls.

        Args:
            market_data: DataFrame with OHLCV data
            symbol: Stock symbol (for logging/output)
            capital: Total capital available (default: 100000)
            metadata: Optional metadata dict (for data provenance tracking)

        Returns:
            Fused signal dictionary with metadata

        Raises:
            ValueError: If all enabled strategies fail
        """
        self.logger.info(f"[FusionStrategy] Analyzing {symbol} with multi-strategy fusion (from data)")

        # Run enabled strategies using analyze_data()
        livermore_signal = None
        kroll_signal = None

        if self.enable_livermore and self.livermore:
            try:
                self.logger.info("[FusionStrategy] Running Livermore strategy...")
                livermore_signal = self.livermore.analyze_data(
                    market_data=market_data,
                    symbol=symbol,
                    capital=capital,
                    metadata=metadata
                )
            except Exception as e:
                self.logger.error(f"[FusionStrategy] Livermore failed: {e}")

        if self.enable_kroll and self.kroll:
            try:
                self.logger.info("[FusionStrategy] Running Kroll strategy...")
                kroll_signal = self.kroll.analyze_data(
                    market_data=market_data,
                    symbol=symbol,
                    capital=capital,
                    metadata=metadata
                )
            except Exception as e:
                self.logger.error(f"[FusionStrategy] Kroll failed: {e}")

        # Fuse signals
        fused = self.fuse_signals(livermore_signal, kroll_signal)

        # Add metadata
        if metadata is None:
            metadata = {
                'api_source': 'Backtest (pre-fetched)',
                'retrieval_timestamp': datetime.now(),
                'data_freshness': 'historical'
            }

        fused.update({
            'symbol': symbol,
            'strategy': 'Fusion',
            'data_source': metadata.get('api_source', 'Unknown'),
            'data_timestamp': metadata['retrieval_timestamp'].isoformat() if isinstance(metadata.get('retrieval_timestamp'), datetime) else str(metadata.get('retrieval_timestamp', 'Unknown')),
            'data_freshness': metadata.get('data_freshness', 'unknown'),
            'data_points': len(market_data),
            'analysis_timestamp': datetime.now().isoformat()
        })

        return fused

    def analyze(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        capital: float = 100000.0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Analyze with multi-strategy fusion.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            capital: Total capital
            use_cache: Use cached data

        Returns:
            Fused signal dictionary with metadata
        """
        self.logger.info(f"[FusionStrategy] Analyzing {symbol} with multi-strategy fusion")

        # Run enabled strategies
        livermore_signal = None
        kroll_signal = None

        if self.enable_livermore and self.livermore:
            try:
                self.logger.info("[FusionStrategy] Running Livermore strategy...")
                livermore_signal = self.livermore.analyze(
                    symbol, start_date, end_date, capital, use_cache
                )
            except Exception as e:
                self.logger.error(f"[FusionStrategy] Livermore failed: {e}")

        if self.enable_kroll and self.kroll:
            try:
                self.logger.info("[FusionStrategy] Running Kroll strategy...")
                kroll_signal = self.kroll.analyze(
                    symbol, start_date, end_date, capital, use_cache
                )
            except Exception as e:
                self.logger.error(f"[FusionStrategy] Kroll failed: {e}")

        # Fuse signals
        fused = self.fuse_signals(livermore_signal, kroll_signal)

        # Add metadata from one of the strategies
        metadata_source = livermore_signal or kroll_signal
        if metadata_source:
            fused.update({
                'symbol': symbol,
                'strategy': 'Fusion',
                'data_source': metadata_source.get('data_source'),
                'data_timestamp': metadata_source.get('data_timestamp'),
                'data_freshness': metadata_source.get('data_freshness'),
                'analysis_timestamp': datetime.now().isoformat()
            })

        return fused

    def _wrap_single_signal(self, signal: Dict[str, Any], strategy_name: str) -> Dict[str, Any]:
        """Wrap single strategy signal when fusion not needed."""
        return {
            **signal,
            'fusion_factors': [f"Using {strategy_name} only (other strategy disabled)"]
        }

    def _risk_to_score(self, risk_level: str) -> float:
        """Convert risk level to numeric score."""
        risk_map = {'LOW': 1.0, 'MEDIUM': 2.0, 'HIGH': 3.0}
        return risk_map.get(risk_level, 2.0)

    def _score_to_risk(self, score: float) -> str:
        """Convert numeric score to risk level."""
        if score < 1.5:
            return 'LOW'
        elif score < 2.5:
            return 'MEDIUM'
        else:
            return 'HIGH'
