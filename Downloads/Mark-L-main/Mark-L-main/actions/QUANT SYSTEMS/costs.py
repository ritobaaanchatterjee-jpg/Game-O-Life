"""
FORGE Cost Engine - Institutional Brokerage & Statutory Taxes (NSE Intraday)
"""

def calculate_trade_costs(side: str, shares: int, entry_price: float, exit_price: float, slippage_pct: float = 0.1) -> dict:
    turnover_entry = shares * entry_price
    turnover_exit = shares * exit_price
    total_turnover = turnover_entry + turnover_exit

    # Brokerage: Flat ₹20 or 0.03% whichever is lower (per leg)
    brok_entry = min(20.0, 0.0003 * turnover_entry)
    brok_exit = min(20.0, 0.0003 * turnover_exit)
    total_brokerage = brok_entry + brok_exit

    # STT (Securities Transaction Tax): 0.025% on Sell side only for Intraday
    stt = 0.00025 * turnover_exit if side in ['BUY', 'LONG'] else 0.00025 * turnover_entry

    # Exchange Turnover Charges: ~0.00325% on total turnover
    exchange_charges = 0.0000325 * total_turnover

    # SEBI Charges: ₹10 per crore (0.0001%)
    sebi_charges = 0.000001 * total_turnover

    # Stamp Duty: 0.003% on Buy side only
    stamp_duty = 0.00003 * (turnover_entry if side in ['BUY', 'LONG'] else turnover_exit)

    # GST: 18% on (Brokerage + Exchange Charges + SEBI Fees)
    gst = 0.18 * (total_brokerage + exchange_charges + sebi_charges)

    # Execution Slippage Penalty
    slippage = (slippage_pct / 100.0) * total_turnover

    total_statutory_costs = total_brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst + slippage

    return {
        "total_costs": total_statutory_costs,
        "brokerage": total_brokerage,
        "stt": stt,
        "slippage": slippage,
        "gst": gst
    }