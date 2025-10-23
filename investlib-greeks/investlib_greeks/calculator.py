"""
MyInvest V0.3 - Options Greeks Calculator (T032)
Black-Scholes Greeks calculation using py_vollib_vectorized.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Literal, Tuple
from datetime import datetime


logger = logging.getLogger(__name__)


class OptionsGreeksCalculator:
    """Calculate option Greeks using Black-Scholes model.

    Greeks: Delta, Gamma, Vega, Theta, Rho
    """

    def calculate_greeks(
        self,
        S: float,  # Spot price
        K: float,  # Strike price
        T: float,  # Time to expiry (years)
        r: float,  # Risk-free rate
        sigma: float,  # Volatility (annualized)
        option_type: Literal['call', 'put']
    ) -> Dict[str, float]:
        """Calculate all Greeks for a single option.

        Args:
            S: Current spot price
            K: Strike price
            T: Time to expiry in years (e.g., 30 days = 30/365)
            r: Risk-free interest rate (e.g., 0.03 = 3%)
            sigma: Implied volatility (e.g., 0.20 = 20%)
            option_type: 'call' or 'put'

        Returns:
            Dict with delta, gamma, vega, theta, rho

        Example:
            >>> calc = OptionsGreeksCalculator()
            >>> greeks = calc.calculate_greeks(
            ...     S=50, K=50, T=0.25, r=0.03, sigma=0.20, option_type='call'
            ... )
            >>> # greeks = {'delta': 0.58, 'gamma': 0.04, ...}
        """
        try:
            from py_vollib.black_scholes import black_scholes as bs
            from py_vollib.black_scholes.greeks import analytical as greeks

            # Calculate Greeks
            delta = greeks.delta(option_type[0], S, K, T, r, sigma)
            gamma = greeks.gamma(option_type[0], S, K, T, r, sigma)
            vega = greeks.vega(option_type[0], S, K, T, r, sigma)
            theta = greeks.theta(option_type[0], S, K, T, r, sigma)
            rho = greeks.rho(option_type[0], S, K, T, r, sigma)

            result = {
                'delta': delta,
                'gamma': gamma,
                'vega': vega / 100,  # Convert to % change per 1% vol
                'theta': theta / 365,  # Convert to daily theta
                'rho': rho / 100  # Convert to % change per 1% rate
            }

            logger.debug(
                f"[Greeks] {option_type} S={S} K={K} T={T:.3f}y σ={sigma*100:.1f}%: "
                f"Δ={result['delta']:.3f} Γ={result['gamma']:.4f} "
                f"ν={result['vega']:.4f} Θ={result['theta']:.2f} ρ={result['rho']:.4f}"
            )

            return result

        except ImportError:
            logger.warning("[Greeks] py_vollib not available, using simplified Greeks")
            # Fallback: simplified delta only
            return self._simplified_greeks(S, K, T, option_type)

    def _simplified_greeks(
        self,
        S: float,
        K: float,
        T: float,
        option_type: str
    ) -> Dict[str, float]:
        """Simplified Greeks when py_vollib unavailable."""
        # Simple delta approximation
        if option_type == 'call':
            delta = 0.5 if S >= K else 0.2
        else:  # put
            delta = -0.5 if S <= K else -0.2

        return {
            'delta': delta,
            'gamma': 0.0,
            'vega': 0.0,
            'theta': 0.0,
            'rho': 0.0
        }

    def calculate_greeks_dataframe(
        self,
        options_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate Greeks for a DataFrame of options.

        Args:
            options_df: DataFrame with columns [spot, strike, expiry_date, iv, type]

        Returns:
            DataFrame with added Greeks columns

        Example:
            >>> df = pd.DataFrame({
            ...     'spot': [50, 50],
            ...     'strike': [48, 52],
            ...     'expiry_date': ['2025-03-21', '2025-03-21'],
            ...     'iv': [0.20, 0.25],
            ...     'type': ['call', 'put']
            ... })
            >>> result = calc.calculate_greeks_dataframe(df)
            >>> # result has delta, gamma, vega, theta, rho columns
        """
        results = []

        for _, row in options_df.iterrows():
            # Calculate time to expiry
            expiry = pd.to_datetime(row['expiry_date'])
            days_to_expiry = (expiry - datetime.now()).days
            T = max(days_to_expiry / 365.0, 0.001)  # Minimum 0.001 year

            greeks = self.calculate_greeks(
                S=row['spot'],
                K=row['strike'],
                T=T,
                r=0.03,  # Default risk-free rate
                sigma=row.get('iv', 0.20),  # Use IV or default 20%
                option_type=row['type']
            )

            results.append(greeks)

        # Add Greeks as columns
        greeks_df = pd.DataFrame(results)
        return pd.concat([options_df, greeks_df], axis=1)


class VolatilityManager:
    """Manage implied volatility with historical volatility fallback."""

    def __init__(self, default_iv: float = 0.20):
        """Initialize volatility manager.

        Args:
            default_iv: Default IV when data unavailable (e.g., 0.20 = 20%)
        """
        self.default_iv = default_iv

    def get_volatility(
        self,
        symbol: str,
        historical_prices: pd.Series = None
    ) -> float:
        """Get volatility for option pricing.

        Priority:
        1. Implied volatility (IV) from market (not implemented yet)
        2. Historical volatility (HV) from price series
        3. Default volatility

        Args:
            symbol: Option symbol
            historical_prices: Historical price series (for HV calculation)

        Returns:
            Volatility (annualized)
        """
        # Try historical volatility
        if historical_prices is not None and len(historical_prices) > 20:
            hv = self.calculate_historical_volatility(historical_prices)
            logger.info(f"[Vol] {symbol}: Using HV={hv*100:.1f}%")
            return hv

        # Fallback to default
        logger.warning(
            f"[Vol] {symbol}: No IV/HV available, using default {self.default_iv*100:.1f}%"
        )
        return self.default_iv

    def calculate_historical_volatility(
        self,
        prices: pd.Series,
        window: int = 30
    ) -> float:
        """Calculate historical volatility from price series.

        Args:
            prices: Price series
            window: Rolling window in days (default: 30)

        Returns:
            Annualized volatility
        """
        # Calculate log returns
        returns = np.log(prices / prices.shift(1))

        # Calculate volatility (std of returns)
        vol = returns.std()

        # Annualize (assuming 252 trading days)
        annualized_vol = vol * np.sqrt(252)

        return annualized_vol
