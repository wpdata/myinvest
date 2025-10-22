"""Integration tests for Livermore Advisor.

Tests the complete advisor workflow with signal processing.
"""

import pytest
import json
from datetime import datetime


try:
    from investlib_advisors.livermore_advisor import LivermoreAdvisor
    ADVISOR_EXISTS = True
except ImportError:
    ADVISOR_EXISTS = False


@pytest.mark.skipif(not ADVISOR_EXISTS, reason="LivermoreAdvisor not yet implemented")
class TestLivermoreAdvisor:
    """Test Livermore Advisor recommendation generation."""

    def test_generate_recommendation_from_signal(self):
        """Test advisor generates complete recommendation from signal."""
        advisor = LivermoreAdvisor()
        
        signal = {
            "symbol": "600519.SH",
            "action": "BUY",
            "entry_price": 1500.0,
            "stop_loss": 1450.0,
            "take_profit": 1650.0,
            "position_size_pct": 15.0,
            "max_loss": 5000.0,
            "confidence": "HIGH",
            "key_factors": ["Price breakout", "Volume spike"],
            "risk_reward_ratio": 3.0
        }
        
        recommendation = advisor.generate_recommendation(signal, capital=100000)
        
        assert recommendation is not None
        assert "reasoning" in recommendation
        assert "advisor_name" in recommendation
        assert recommendation["advisor_name"] == "Livermore"
        
    def test_recommendation_includes_mandatory_fields(self):
        """Test all recommendations have mandatory fields."""
        advisor = LivermoreAdvisor()
        signal = {
            "symbol": "600519.SH", "action": "BUY",
            "entry_price": 1500.0, "stop_loss": 1450.0,
            "take_profit": 1650.0, "position_size_pct": 15.0,
            "max_loss": 5000.0, "confidence": "HIGH",
            "key_factors": [], "risk_reward_ratio": 3.0
        }
        
        rec = advisor.generate_recommendation(signal, capital=100000)
        
        required = ["advisor_name", "advisor_version", "strategy_name", 
                    "reasoning", "confidence", "key_factors"]
        for field in required:
            assert field in rec
