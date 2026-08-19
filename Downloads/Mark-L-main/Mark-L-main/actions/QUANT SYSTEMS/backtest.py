"""
FORGE Institutional Backtester Engine
"""
import pandas as pd
from costs import calculate_trade_costs
from signals import SignalGenerator
from bayesian_engine import FastBayesianEngine
from regime import RegimeDetector

class Backtester:
    def __init__(self, initial_capital: float = 100000.0, max_risk_pct: float = 1.0, slippage_pct: float = 0.1):
        self.initial_capital = initial_capital
        self.max_risk_pct = max_risk_pct / 100.0
        self.slippage_pct = slippage_pct

    def run(self, df: pd.DataFrame, atr_mult: float = 2.0, rr_ratio: float = 2.0) -> dict:
        if df.empty or len(df) < 30:
            return {"error": "Insufficient dataset for backtest"}

        df = df.copy()
        sig_gen = SignalGenerator()
        bayes = FastBayesianEngine()

        df['VWAP'] = sig_gen.calculate_vwap(df)
        
        capital = self.initial_capital
        trades = []
        position = None  # None or dict

        for i in range(30, len(df)):
            sub_df = df.iloc[:i+1]
            curr_bar = sub_df.iloc[-1]
            close = float(curr_bar['close'])
            high = float(curr_bar['high'])
            low = float(curr_bar['low'])
            timestamp = curr_bar['timestamp']

            # Check open position exit triggers
            if position:
                side = position['side']
                sl = position['sl']
                tp = position['tp']
                shares = position['shares']
                entry_price = position['entry_price']

                exit_price = None
                reason = None

                if side == 'BUY':
                    if low <= sl:
                        exit_price = sl
                        reason = "Stop Loss"
                    elif high >= tp:
                        exit_price = tp
                        reason = "Take Profit"
                elif side == 'SELL':
                    if high >= sl:
                        exit_price = sl
                        reason = "Stop Loss"
                    elif low <= tp:
                        exit_price = tp
                        reason = "Take Profit"

                if exit_price:
                    gross_pnl = (exit_price - entry_price) * shares if side == 'BUY' else (entry_price - exit_price) * shares
                    cost_info = calculate_trade_costs(side, shares, entry_price, exit_price, self.slippage_pct)
                    net_pnl = gross_pnl - cost_info['total_costs']
                    capital += net_pnl

                    trades.append({
                        "entry_time": position['entry_time'],
                        "exit_time": timestamp,
                        "side": side,
                        "shares": shares,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "gross_pnl": gross_pnl,
                        "total_costs": cost_info['total_costs'],
                        "pnl": net_pnl,
                        "pnl_pct": net_pnl / self.initial_capital,
                        "reason": reason
                    })
                    position = None
                    continue

            # Evaluate Entry if flat
            if not position:
                regime_info = RegimeDetector.classify(sub_df)
                bayes_info = bayes.compute_posterior(sub_df, window=20)
                sig = sig_gen.generate_signal(sub_df, regime_info, bayes_info)['signal']

                if sig in ['BUY', 'SELL']:
                    atr = float(curr_bar.get('ATR_14', close * 0.01))
                    stop_dist = atr * atr_mult
                    if stop_dist > 0:
                        risk_amt = self.initial_capital * self.max_risk_pct
                        shares = int(risk_amt // stop_dist)
                        shares = min(shares, int(capital // close))

                        if shares > 0:
                            sl = round(close - stop_dist, 2) if sig == 'BUY' else round(close + stop_dist, 2)
                            tp = round(close + (stop_dist * rr_ratio), 2) if sig == 'BUY' else round(close - (stop_dist * rr_ratio), 2)

                            position = {
                                "side": sig,
                                "shares": shares,
                                "entry_price": close,
                                "entry_time": timestamp,
                                "sl": sl,
                                "tp": tp
                            }

        trades_df = pd.DataFrame(trades)
        if trades_df.empty:
            return {
                "final_capital": capital,
                "total_return_pct": 0.0,
                "win_rate": 0.0,
                "total_trades": 0,
                "max_drawdown_pct": 0.0,
                "trades": []
            }

        wins = trades_df[trades_df['pnl'] > 0]
        win_rate = (len(wins) / len(trades_df)) * 100

        # Equity drawdown
        equity = trades_df['pnl'].cumsum() + self.initial_capital
        peak = equity.cummax()
        dd = (equity - peak) / peak
        max_dd = abs(float(dd.min())) * 100 if not dd.empty else 0.0

        return {
            "final_capital": float(capital),
            "total_return_pct": float(((capital - self.initial_capital) / self.initial_capital) * 100),
            "win_rate": float(win_rate),
            "total_trades": len(trades_df),
            "max_drawdown_pct": float(max_dd),
            "trades": trades
        }