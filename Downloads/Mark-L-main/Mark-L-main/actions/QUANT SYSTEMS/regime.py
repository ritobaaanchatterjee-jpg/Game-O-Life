"""
FORGE Market Regime Classifier
"""
import pandas as pd

class RegimeDetector:
    @staticmethod
    def classify(df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 20:
            return {"regime": "NEUTRAL", "trend_strength": 0.0}

        latest = df.iloc[-1]
        close = latest['close']
        sma20 = latest.get('SMA_20', close)
        sma50 = latest.get('SMA_50', close)

        if close > sma20 > sma50:
            regime = "BULLISH_TREND"
        elif close < sma20 < sma50:
            regime = "BEARISH_TREND"
        else:
            regime = "RANGEBOUND"

        return {
            "regime": regime,
            "sma_spread_pct": float(((sma20 - sma50) / sma50) * 100) if sma50 > 0 else 0.0
        }