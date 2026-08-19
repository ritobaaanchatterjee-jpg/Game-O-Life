"""
FORGE Market Data Engine
"""
import pandas as pd
import numpy as np
import yfinance as yf

class MarketDataEngine:
    def fetch_and_store(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                return pd.DataFrame()

            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.reset_index()
            rename_map = {'Date': 'timestamp', 'Datetime': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}
            df = df.rename(columns=rename_map)
            df.columns = [col.lower() for col in df.columns]

            if 'timestamp' not in df.columns or df.empty:
                return pd.DataFrame()

            df = df.sort_values('timestamp').reset_index(drop=True)

            # Compute Technical Indicators
            df['SMA_20'] = df['close'].rolling(20).mean()
            df['SMA_50'] = df['close'].rolling(50).mean()

            # RSI 14
            delta = df['close'].diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            df['RSI_14'] = 100 - (100 / (1 + rs))

            # ATR 14
            high_low = df['high'] - df['low']
            high_close = (df['high'] - df['close'].shift()).abs()
            low_close = (df['low'] - df['close'].shift()).abs()
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR_14'] = tr.rolling(14).mean()

            return df.dropna().reset_index(drop=True)
        except Exception:
            return pd.DataFrame()