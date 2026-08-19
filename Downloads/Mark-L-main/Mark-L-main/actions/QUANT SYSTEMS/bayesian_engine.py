"""
FORGE Fast Bayesian Probability Engine
"""
import pandas as pd
import numpy as np

class FastBayesianEngine:
    def compute_posterior(self, df: pd.DataFrame, window: int = 20) -> dict:
        if df.empty or len(df) < window:
            return {"posterior_bullish": 0.5, "p_bullish": 0.5}

        sub_df = df.tail(window).copy()
        returns = sub_df['close'].pct_change().dropna()

        # Evidence: Ratio of positive return bars
        positive_bars = (returns > 0).sum()
        total_bars = len(returns)

        # Prior distribution setup
        prior_bullish = 0.5
        likelihood = positive_bars / total_bars if total_bars > 0 else 0.5

        # Bayes Update rule
        posterior_bullish = (likelihood * prior_bullish) / ((likelihood * prior_bullish) + ((1 - likelihood) * (1 - prior_bullish)))

        return {
            "posterior_bullish": float(np.clip(posterior_bullish, 0.05, 0.95)),
            "p_bullish": float(np.clip(posterior_bullish, 0.05, 0.95))
        }