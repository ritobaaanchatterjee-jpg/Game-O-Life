"""
FORGE Walk-Forward Optimizer Engine
"""
import pandas as pd
from backtest import Backtester

class HeavyweightOptimizer:
    def __init__(self, initial_capital: float = 100000.0, max_risk_pct: float = 1.0):
        self.initial_capital = initial_capital
        self.max_risk_pct = max_risk_pct

    def run_walk_forward(self, df: pd.DataFrame, train_days: int = 20, test_days: int = 5, atr_list: list = None, rr_list: list = None) -> dict:
        if df.empty or len(df) < (train_days + test_days):
            return {"error": "Dataset too short for specified walk-forward window sizes."}

        atr_list = atr_list or [1.5, 2.0, 2.5]
        rr_list = rr_list or [1.5, 2.0, 2.5]

        # Group data into trading chunks
        df = df.copy()
        df['dt'] = pd.to_datetime(df['timestamp'])
        df['date_group'] = df['dt'].dt.date
        unique_dates = df['date_group'].unique()

        window_summary = []
        all_oos_trades = []

        i = 0
        window_id = 1
        while i + train_days + test_days <= len(unique_dates):
            train_dates = unique_dates[i : i + train_days]
            test_dates = unique_dates[i + train_days : i + train_days + test_days]

            train_df = df[df['date_group'].isin(train_dates)].reset_index(drop=True)
            test_df = df[df['date_group'].isin(test_dates)].reset_index(drop=True)

            # In-Sample (IS) Grid Search
            best_score = -999999
            best_params = (atr_list[0], rr_list[0])

            for a in atr_list:
                for r in rr_list:
                    bt = Backtester(initial_capital=self.initial_capital, max_risk_pct=self.max_risk_pct)
                    res = bt.run(train_df, atr_mult=a, rr_ratio=r)
                    score = res.get('total_return_pct', -999)
                    if score > best_score:
                        best_score = score
                        best_params = (a, r)

            # Out-Of-Sample (OOS) Test
            opt_a, opt_r = best_params
            oos_bt = Backtester(initial_capital=self.initial_capital, max_risk_pct=self.max_risk_pct)
            oos_res = oos_bt.run(test_df, atr_mult=opt_a, rr_ratio=opt_r)

            window_summary.append({
                "Window": f"W{window_id}",
                "Train Start": str(train_dates[0]),
                "Test End": str(test_dates[-1]),
                "Best ATR Mult": opt_a,
                "Best RR Ratio": opt_r,
                "IS Return (%)": round(best_score, 2),
                "OOS Return (%)": round(oos_res.get('total_return_pct', 0.0), 2)
            })

            all_oos_trades.extend(oos_res.get('trades', []))
            i += test_days
            window_id += 1

        return {
            "window_summary": pd.DataFrame(window_summary),
            "oos_trades": pd.DataFrame(all_oos_trades)
        }