"""
FORGE Signal Processing Engine
"""
import pandas as pd

class SignalGenerator:
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        if df.empty:
            return pd.Series(dtype=float)

        df = df.copy()
        df['dt'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['dt'].dt.date
        
        # Cumulative VWAP anchored daily
        tp = (df['high'] + df['low'] + df['close']) / 3.0
        pv = tp * df['volume']
        
        vwap = pv.groupby(df['date']).cumsum() / df['volume'].groupby(df['date']).cumsum()
        return vwap.fillna(df['close'])

    def generate_signal(self, df: pd.DataFrame, regime_info: dict, bayes_info: dict) -> dict:
        if df.empty:
            return {"signal": "HOLD", "reason": "No data"}

        latest = df.iloc[-1]
        p_bull = bayes_info.get("p_bullish", 0.5)
        regime = regime_info.get("regime", "RANGEBOUND")
        
        close = latest['close']
        vwap = latest.get('VWAP', close)

        # Institutional Execution Criteria
        if p_bull >= 0.60 and close > vwap and regime != "BEARISH_TREND":
            return {"signal": "BUY", "reason": f"Posterior Bullish ({p_bull*100:.1f}%) + Above VWAP"}
        elif p_bull <= 0.40 and close < vwap and regime != "BULLISH_TREND":
            return {"signal": "SELL", "reason": f"Posterior Bearish ({p_bull*100:.1f}%) + Below VWAP"}
        
        return {"signal": "HOLD", "reason": "Neutral probability / No trend confirmation"}