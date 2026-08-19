import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import importlib
import requests

import fetcher, regime, bayesian_engine, signals, risk_engine, backtest, scanner, optimizer, costs

# Bust Streamlit memory cache on re-runs
importlib.reload(signals)
importlib.reload(backtest)
importlib.reload(scanner)
importlib.reload(optimizer)
importlib.reload(costs)

from fetcher import MarketDataEngine
from regime import RegimeDetector
from bayesian_engine import FastBayesianEngine
from signals import SignalGenerator
from risk_engine import RiskEngine
from backtest import Backtester
from scanner import BasketScanner, NIFTY_TOP_BASKET
from optimizer import HeavyweightOptimizer

# --- TELEGRAM NOTIFIER CLASS (Inlined to bypass import errors) ---
class TelegramNotifier:
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or ""
        self.chat_id = chat_id or ""

    def send_alert(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

# Page Configuration
st.set_page_config(
    page_title="FORGE Quant Studio",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ FORGE Quantitative Strategy Studio")
st.caption("Bar-by-Bar Bayesian Signal Processing, Institutional Cost Engine & Day-Anchored Walk-Forward Optimizer")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Quant Studio Controls")

symbol = st.sidebar.text_input("Ticker Symbol", value="RELIANCE.NS")
period = st.sidebar.selectbox("Period", ["1mo", "6mo", "1y", "max"], index=2)
interval = st.sidebar.selectbox("Interval", ["1d", "1h", "15m"], index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Capital & Risk Controls")
initial_capital = st.sidebar.number_input("Initial Capital (₹)", value=100000.0, step=10000.0)
max_risk_pct = st.sidebar.slider("Max Risk per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
slippage_pct = st.sidebar.number_input("Slippage (%)", value=0.1, step=0.05)
atr_mult = st.sidebar.number_input("ATR Multiplier", value=2.0, step=0.5)
rr_ratio = st.sidebar.number_input("Risk-Reward Ratio (RR)", value=2.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Telegram Alerts")
tg_token = st.sidebar.text_input("Bot Token", type="password", key="tg_token")
tg_chat_id = st.sidebar.text_input("Chat ID", key="tg_chat_id")

if st.sidebar.button("Test Telegram Alert"):
    if not tg_token or not tg_chat_id:
        st.sidebar.error("Please enter both Bot Token and Chat ID.")
    else:
        notifier = TelegramNotifier(token=tg_token, chat_id=tg_chat_id)
        success = notifier.send_alert("🚀 *FORGE Quant Studio*: Test alert successfully received!")
        if success:
            st.sidebar.success("Alert sent to Telegram!")
        else:
            st.sidebar.error("Failed to send. Check your credentials.")

# --- DATA FETCHING ---
@st.cache_data(ttl=300)
def load_data(sym: str, per: str, inter: str):
    fetcher_engine = MarketDataEngine()
    return fetcher_engine.fetch_and_store(sym, period=per, interval=inter)

df = load_data(symbol, period, interval)

# --- LATEST BAR INTELLIGENCE & VWAP ---
bayes = FastBayesianEngine()
sig_gen = SignalGenerator()
risk_eng = RiskEngine(total_capital=initial_capital, max_risk_pct=max_risk_pct)

if not df.empty:
    df['VWAP'] = sig_gen.calculate_vwap(df)

latest_sub_df = df.copy()
regime_info = RegimeDetector.classify(latest_sub_df) if not df.empty else {}
bayes_info = bayes.compute_posterior(latest_sub_df, window=20) if not df.empty else {}
sig_info = sig_gen.generate_signal(latest_sub_df, regime_info, bayes_info) if not df.empty else {"signal": "HOLD"}
current_signal = sig_info["signal"]

risk_info = risk_eng.calculate_position(latest_sub_df, signal=current_signal, atr_mult=atr_mult, rr_ratio=rr_ratio) if not df.empty else {}

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Single Ticker", 
    "Institutional Backtest", 
    "Basket Scanner", 
    "Walk-Forward", 
    "Monte Carlo Risk"
])

# ==========================================
# TAB 1: LIVE INTELLIGENCE
# ==========================================
with tab1:
    if df.empty or len(df) < 20:
        st.error("Insufficient market data returned. Please verify ticker symbol and period.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        latest_close = float(df.iloc[-1]["close"])
        latest_vwap = float(df.iloc[-1]["VWAP"]) if "VWAP" in df.columns else 0.0
        
        vwap_diff_pct = ((latest_close - latest_vwap) / latest_vwap) * 100 if latest_vwap > 0 else 0.0
        vwap_color = "🟢" if latest_close > latest_vwap else "🔴"
        
        m1.metric("Latest Close", f"₹{latest_close:,.2f}")
        m2.metric("Session VWAP", f"₹{latest_vwap:,.2f}", delta=f"{vwap_diff_pct:+.2f}% vs VWAP")
        
        p_bull = bayes_info.get("p_bullish", bayes_info.get("posterior_bullish", bayes_info.get("p_bull", 0.5)))
        m3.metric("Posterior Bull Prob", f"{p_bull * 100:.1f}%")
        
        sig_color = "🟢" if current_signal == "BUY" else ("🔴" if current_signal == "SELL" else "⚪")
        m4.metric("Strategy Signal", f"{sig_color} {current_signal}")

        st.markdown("---")
        col_left, col_right = st.columns([1, 2])

        with col_left:
            st.subheader("📋 Order Execution Plan")
            st.markdown(f"""
            * **Recommended Action:** `{current_signal}`
            * **Shares to Trade:** `{risk_info.get('recommended_shares', 0)}`
            * **Total Capital Allocated:** `₹{risk_info.get('recommended_shares', 0) * latest_close:,.2f}`
            * **Stop Loss Price:** `₹{risk_info.get('stop_loss_price', 0.0)}`
            * **Take Profit Price:** `₹{risk_info.get('take_profit_price', 0.0)}`
            * **Institutional VWAP Filter:** `{vwap_color} Price {'Above' if latest_close > latest_vwap else 'Below'} VWAP`
            * **Session Time Filter:** `Active (09:30-11:45 & 13:45-15:00)`
            """)
            st.caption(f"**Signal Reason:** {sig_info.get('reason', 'N/A')}")

        with col_right:
            st.subheader("📉 Price Action, VWAP & Indicators")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])

            fig.add_trace(go.Candlestick(
                x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price"
            ), row=1, col=1)

            if "VWAP" in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['timestamp'], y=df['VWAP'], mode='lines', name='VWAP', line=dict(color='#FF007F', width=1.5)
                ), row=1, col=1)

            if "SMA_20" in df.columns:
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='orange', width=1)), row=1, col=1)
            if "SMA_50" in df.columns:
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='blue', width=1)), row=1, col=1)

            if "RSI_14" in df.columns:
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI_14'], mode='lines', name='RSI 14', line=dict(color='purple')), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            fig.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TAB 2: INSTITUTIONAL BACKTEST (NET COSTS)
# ==========================================
with tab2:
    if df.empty or len(df) < 20:
        st.error("Insufficient market data for backtesting.")
    else:
        st.subheader(f"🧪 Net-of-Cost Backtest: {symbol}")
        st.caption("Includes STT, Brokerage, Exchange Turnover Fees, Stamp Duty, GST, and Slippage penalties.")
        
        backtester = Backtester(initial_capital=initial_capital, max_risk_pct=max_risk_pct, slippage_pct=slippage_pct)
        results = backtester.run(df, atr_mult=atr_mult, rr_ratio=rr_ratio)

        if "error" in results:
            st.error(results["error"])
        else:
            trades_df = pd.DataFrame(results.get("trades", []))
            total_costs_paid = trades_df["total_costs"].sum() if not trades_df.empty else 0.0

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Final Net Capital", f"₹{results['final_capital']:,.2f}", delta=f"{results['total_return_pct']:.2f}%")
            k2.metric("Net Win Rate", f"{results['win_rate']:.1f}%")
            k3.metric("Total Trades", results['total_trades'])
            k4.metric("Max Drawdown", f"{results['max_drawdown_pct']:.2f}%")
            k5.metric("Total Fees & Taxes Paid", f"₹{total_costs_paid:,.2f}")

            st.markdown("---")

            if not trades_df.empty:
                st.subheader("📈 Net Equity Curve (Post-Taxes & Slippage)")
                eq_fig = go.Figure()
                eq_fig.add_trace(go.Scatter(
                    x=trades_df['exit_time'],
                    y=trades_df['pnl'].cumsum() + initial_capital,
                    mode='lines+markers',
                    name='Net Equity (₹)',
                    line=dict(color='#00CC96', width=2)
                ))
                eq_fig.update_layout(xaxis_title="Exit Date", yaxis_title="Capital (₹)", height=350, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(eq_fig, use_container_width=True)

                st.subheader("📑 Audit Log: Gross PnL vs Statutory Costs & Slippage")
                
                def highlight_net_pnl(val):
                    color = 'rgba(0, 200, 0, 0.2)' if val > 0 else 'rgba(200, 0, 0, 0.2)'
                    return f'background-color: {color}'

                styled_df = trades_df[['entry_time', 'exit_time', 'side', 'shares', 'entry_price', 'exit_price', 'gross_pnl', 'total_costs', 'pnl', 'reason']].style.map(highlight_net_pnl, subset=['pnl'])
                st.dataframe(styled_df, use_container_width=True)
            else:
                st.info("No trades generated over this historical window with selected filters.")

# ==========================================
# TAB 3: MULTI-TICKER BASKET SCANNER
# ==========================================
with tab3:
    st.subheader("🔍 Multi-Ticker Basket Scan (Net of Costs)")
    st.caption("Runs strategy across liquid NSE symbols incorporating statutory charges and time-of-day filters.")

    basket_selection = st.multiselect("Select Tickers to Scan", options=NIFTY_TOP_BASKET, default=NIFTY_TOP_BASKET[:10])

    if st.button("🚀 Run Basket Scan", use_container_width=True):
        if not basket_selection:
            st.warning("Please select at least one ticker symbol to scan.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            basket_scanner = BasketScanner(initial_capital=initial_capital, max_risk_pct=max_risk_pct)
            
            def update_progress(pct, text):
                progress_bar.progress(pct)
                status_text.text(text)

            scan_results = basket_scanner.scan(
                symbols=basket_selection, period=period, interval=interval, atr_mult=atr_mult, rr_ratio=rr_ratio, progress_callback=update_progress
            )

            status_text.success("✅ Basket Scan Complete!")

            if not scan_results.empty:
                st.markdown("---")
                best_stock = scan_results.iloc[0]
                avg_win_rate = scan_results["Win Rate (%)"].mean()
                avg_return = scan_results["Total Return (%)"].mean()

                b1, b2, b3 = st.columns(3)
                b1.metric("Top Performer", f"{best_stock['Symbol']}", delta=f"{best_stock['Total Return (%)']:.2f}% Return")
                b2.metric("Basket Avg Return", f"{avg_return:.2f}%")
                b3.metric("Basket Avg Win Rate", f"{avg_win_rate:.1f}%")

                st.subheader("📊 Basket Net Performance Leaderboard")

                def color_returns(val):
                    color = 'rgba(0, 200, 0, 0.2)' if val > 0 else 'rgba(200, 0, 0, 0.2)'
                    return f'background-color: {color}'

                styled_scan = scan_results.style.map(color_returns, subset=['Total Return (%)'])
                st.dataframe(styled_scan, use_container_width=True)
            else:
                st.error("No valid backtest results generated.")

# ==========================================
# TAB 4: ROLLING WALK-FORWARD OPTIMIZER
# ==========================================
with tab4:
    st.subheader(f"🔄 Day-Anchored Rolling Walk-Forward Engine: {symbol}")
    st.caption("Splits history into rolling trading days, optimizes parameters on Train windows, and measures true Out-Of-Sample (OOS) execution quality.")

    wcol1, wcol2 = st.columns(2)
    with wcol1:
        train_days = st.number_input("In-Sample Train Window (Trading Days)", min_value=10, max_value=60, value=20, step=5)
    with wcol2:
        test_days = st.number_input("Out-of-Sample Test Window (Trading Days)", min_value=5, max_value=20, value=5, step=1)

    st.markdown("---")

    if st.button("🔥 Execute Day-Anchored Walk-Forward Optimization", use_container_width=True):
        if df.empty or len(df) < 100:
            st.error("Walk-Forward requires at least 60d of intraday data. Please select '60d' period in sidebar.")
        else:
            with st.spinner("Running Rolling In-Sample & Out-of-Sample Grid Simulations..."):
                optimizer_engine = HeavyweightOptimizer(initial_capital=initial_capital, max_risk_pct=max_risk_pct)
                
                wf_res = optimizer_engine.run_walk_forward(
                    df=df, train_days=int(train_days), test_days=int(test_days),
                    atr_list=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0], rr_list=[1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
                )

            if "error" in wf_res:
                st.error(wf_res["error"])
            else:
                summary_df = wf_res["window_summary"]
                oos_trades_df = wf_res["oos_trades"]

                st.success(f"✅ Walk-Forward Complete! Evaluated across {len(summary_df)} rolling windows.")

                if not oos_trades_df.empty:
                    oos_pnl = oos_trades_df["pnl"].sum()
                    oos_return_pct = (oos_pnl / initial_capital) * 100
                    winning_oos = oos_trades_df[oos_trades_df["pnl"] > 0]
                    oos_win_rate = (len(winning_oos) / len(oos_trades_df)) * 100
                    total_oos_costs = oos_trades_df["total_costs"].sum()

                    o1, o2, o3, o4 = st.columns(4)
                    o1.metric("Total OOS Return", f"₹{oos_pnl:,.2f}", delta=f"{oos_return_pct:.2f}%")
                    o2.metric("OOS Win Rate", f"{oos_win_rate:.1f}%")
                    o3.metric("Total OOS Trades", len(oos_trades_df))
                    o4.metric("OOS Statutory Fees Paid", f"₹{total_oos_costs:,.2f}")

                    st.markdown("---")
                    st.subheader("📈 Out-of-Sample (OOS) Equity Curve")
                    oos_fig = go.Figure()
                    oos_fig.add_trace(go.Scatter(
                        x=oos_trades_df['exit_time'], y=oos_trades_df['pnl'].cumsum() + initial_capital,
                        mode='lines+markers', name='OOS Capital (₹)', line=dict(color='#00CC96', width=2)
                    ))
                    oos_fig.update_layout(xaxis_title="OOS Execution Date", yaxis_title="Capital (₹)", height=350, margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(oos_fig, use_container_width=True)

                st.subheader("📑 Rolling Window Parameter Breakdown")
                st.dataframe(summary_df, use_container_width=True)

# ==========================================
# TAB 5: MONTE CARLO RISK SIMULATION
# ==========================================
with tab5:
    st.header("🎲 Monte Carlo Sequence Risk & Stress-Testing")

    if "trade_log" in st.session_state and not st.session_state["trade_log"].empty:
        trades_df = st.session_state["trade_log"]
        st.success(f"Loaded {len(trades_df)} historical trades from backtest engine.")
    else:
        st.info("No active backtest found in session memory. Run Tab 2 first, or test below using simulated returns.")
        np.random.seed(42)
        trades_df = pd.DataFrame({"pnl_pct": np.random.normal(0.003, 0.015, size=80)})

    col1, col2 = st.columns(2)
    with col1:
        num_sims = st.slider("Number of Simulations", min_value=100, max_value=5000, value=1000, step=100)
    with col2:
        ruin_limit = st.slider("Max Drawdown Ruin Threshold (%)", min_value=5, max_value=50, value=20, step=5) / 100.0

    if st.button("🔥 Run Monte Carlo Simulation", use_container_width=True):
        from monte_carlo import MonteCarloEngine
        
        mc = MonteCarloEngine(trades_df=trades_df, initial_capital=100000.0, num_simulations=num_sims)
        mc.run_simulation()
        metrics = mc.calculate_risk_metrics(ruin_threshold_pct=ruin_limit)

        if metrics:
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Median Return", f"{metrics['median_return_pct']:.2f}%")
            m2.metric("99% Value at Risk (VaR)", f"{metrics['var_99_pct']:.2f}%")
            m3.metric("95th Percentile Max DD", f"{metrics['worst_95th_dd_pct']:.2f}%")
            m4.metric(f"Prob. of >{ruin_limit*100:.0f}% Drawdown", f"{metrics['prob_ruin_pct']:.1f}%")

            percentile_df = mc.get_percentile_equity_curves()

            fig = go.Figure()
            fig.add_trace(go.Scatter(y=percentile_df["Best 90th Percentile"], mode="lines", name="90th Percentile (Optimistic)", line=dict(color="#00FF7F", dash="dash")))
            fig.add_trace(go.Scatter(y=percentile_df["Median Path (50th)"], mode="lines", name="50th Percentile (Median)", line=dict(color="#1E90FF", width=2)))
            fig.add_trace(go.Scatter(y=percentile_df["Worst 10th Percentile"], mode="lines", name="10th Percentile (Pessimistic)", line=dict(color="#FF4500", dash="dash")))
            
            fig.update_layout(
                title="Monte Carlo Equity Trajectory Fan Chart",
                xaxis_title="Trade Count Sequence",
                yaxis_title="Capital (INR)",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)