"""
FORGE Dynamic Risk Engine
"""
import pandas as pd

class RiskEngine:
    def __init__(self, total_capital: float = 100000.0, max_risk_pct: float = 1.0):
        self.total_capital = total_capital
        self.max_risk_pct = max_risk_pct / 100.0

    def calculate_position(self, df: pd.DataFrame, signal: str, atr_mult: float = 2.0, rr_ratio: float = 2.0) -> dict:
        if df.empty or signal not in ["BUY", "SELL"]:
            return {"recommended_shares": 0, "stop_loss_price": 0.0, "take_profit_price": 0.0}

        latest = df.iloc[-1]
        close = float(latest['close'])
        atr = float(latest.get('ATR_14', close * 0.01))

        risk_amount = self.total_capital * self.max_risk_pct
        stop_dist = atr * atr_mult

        if stop_dist <= 0:
            return {"recommended_shares": 0, "stop_loss_price": 0.0, "take_profit_price": 0.0}

        shares = int(risk_amount // stop_dist)
        # Capital ceiling check
        shares = min(shares, int(self.total_capital // close))

        if signal == "BUY":
            sl = round(close - stop_dist, 2)
            tp = round(close + (stop_dist * rr_ratio), 2)
        else:
            sl = round(close + stop_dist, 2)
            tp = round(close - (stop_dist * rr_ratio), 2)

        return {
            "recommended_shares": max(0, shares),
            "stop_loss_price": sl,
            "take_profit_price": tp
        }