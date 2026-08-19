"""
FORGE Basket Scanner
"""
import pandas as pd
from fetcher import MarketDataEngine
from backtest import Backtester

NIFTY_TOP_BASKET = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
    "INFY.NS", "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LTIM.NS", "AXISBANK.NS"
]

class BasketScanner:
    def __init__(self, initial_capital: float = 100000.0, max_risk_pct: float = 1.0):
        self.initial_capital = initial_capital
        self.max_risk_pct = max_risk_pct

    def scan(self, symbols: list, period: str = "1y", interval: str = "1d", atr_mult: float = 2.0, rr_ratio: float = 2.0, progress_callback=None) -> pd.DataFrame:
        fetcher_engine = MarketDataEngine()
        results = []
        total = len(symbols)

        for idx, sym in enumerate(symbols):
            if progress_callback:
                progress_callback(int(((idx + 1) / total) * 100), f"Scanning {sym} ({idx+1}/{total})...")

            df = fetcher_engine.fetch_and_store(sym, period=period, interval=interval)
            if df.empty or len(df) < 30:
                continue

            bt = Backtester(initial_capital=self.initial_capital, max_risk_pct=self.max_risk_pct)
            res = bt.run(df, atr_mult=atr_mult, rr_ratio=rr_ratio)

            if "error" not in res:
                results.append({
                    "Symbol": sym,
                    "Total Return (%)": res['total_return_pct'],
                    "Win Rate (%)": res['win_rate'],
                    "Trades": res['total_trades'],
                    "Max DD (%)": res['max_drawdown_pct'],
                    "Final Capital (₹)": res['final_capital']
                })

        res_df = pd.DataFrame(results)
        return res_df.sort_values(by="Total Return (%)", ascending=False).reset_index(drop=True) if not res_df.empty else pd.DataFrame()