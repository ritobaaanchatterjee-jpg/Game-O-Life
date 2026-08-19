"""
FORGE Monte Carlo Sequence Risk & Stress-Test Engine
"""
import pandas as pd
import numpy as np

class MonteCarloEngine:
    def __init__(self, trades_df: pd.DataFrame, initial_capital: float = 100000.0, num_simulations: int = 1000):
        self.trades_df = trades_df
        self.initial_capital = initial_capital
        self.num_simulations = num_simulations
        self.simulated_paths = []

    def run_simulation(self):
        if self.trades_df.empty:
            return

        returns = self.trades_df['pnl_pct'].values if 'pnl_pct' in self.trades_df.columns else np.random.normal(0.002, 0.01, 50)
        n_trades = len(returns)

        paths = []
        for _ in range(self.num_simulations):
            resampled_returns = np.random.choice(returns, size=n_trades, replace=True)
            equity_curve = self.initial_capital * np.cumprod(1 + resampled_returns)
            paths.append(equity_curve)

        self.simulated_paths = np.array(paths)

    def calculate_risk_metrics(self, ruin_threshold_pct: float = 0.20) -> dict:
        if len(self.simulated_paths) == 0:
            return {}

        final_returns_pct = ((self.simulated_paths[:, -1] - self.initial_capital) / self.initial_capital) * 100
        
        # Drawdowns per path
        max_dds = []
        ruin_count = 0
        for path in self.simulated_paths:
            peak = np.maximum.accumulate(path)
            dd = (path - peak) / peak
            max_dd = abs(np.min(dd))
            max_dds.append(max_dd)
            if max_dd >= ruin_threshold_pct:
                ruin_count += 1

        return {
            "median_return_pct": float(np.median(final_returns_pct)),
            "var_99_pct": float(-np.percentile(final_returns_pct, 1)),
            "worst_95th_dd_pct": float(np.percentile(max_dds, 95) * 100),
            "prob_ruin_pct": float((ruin_count / self.num_simulations) * 100)
        }

    def get_percentile_equity_curves(self) -> pd.DataFrame:
        if len(self.simulated_paths) == 0:
            return pd.DataFrame()

        p90 = np.percentile(self.simulated_paths, 90, axis=0)
        p50 = np.percentile(self.simulated_paths, 50, axis=0)
        p10 = np.percentile(self.simulated_paths, 10, axis=0)

        return pd.DataFrame({
            "Best 90th Percentile": p90,
            "Median Path (50th)": p50,
            "Worst 10th Percentile": p10
        })