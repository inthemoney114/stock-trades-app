import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Stock Trade Tracker", layout="wide")

st.title("🚀 Stock Trade Tracker (with Avg Cost)")

# Initialize session state
if "trades" not in st.session_state:
    st.session_state.trades = []
if "positions" not in st.session_state:
    st.session_state.positions = {}  # {symbol: {"qty": int, "avg_cost": float}}

# --- Trade Entry Form ---
with st.form("trade_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        symbol = st.text_input("Stock Symbol").upper()
    with col2:
        trade_type = st.selectbox("Type", ["BUY", "SELL"])
    with col3:
        qty = st.number_input("Quantity", min_value=1, step=1)

    col4, col5 = st.columns(2)
    with col4:
        price = st.number_input("Price", min_value=0.0, step=0.01)
    with col5:
        trade_date = st.date_input("Date", datetime.today())

    submitted = st.form_submit_button("➕ Add Trade")

    if submitted and symbol:
        # Fetch position for symbol
        pos = st.session_state.positions.get(symbol, {"qty": 0, "avg_cost": 0.0})
        old_qty, old_avg = pos["qty"], pos["avg_cost"]

        if trade_type == "BUY":
            new_qty = old_qty + qty
            new_avg = ((old_avg * old_qty) + (price * qty)) / new_qty if new_qty > 0 else 0
            st.session_state.positions[symbol] = {"qty": new_qty, "avg_cost": new_avg}

        elif trade_type == "SELL":
            if qty > old_qty:
                st.warning("⚠️ You cannot sell more shares than you hold.")
            else:
                new_qty = old_qty - qty
                new_avg = old_avg if new_qty > 0 else 0.0
                st.session_state.positions[symbol] = {"qty": new_qty, "avg_cost": new_avg}

        # Save trade history
        st.session_state.trades.append({
            "Date": trade_date,
            "Symbol": symbol,
            "Type": trade_type,
            "Quantity": qty,
            "Price": price,
            "Avg Cost After Trade": st.session_state.positions[symbol]["avg_cost"],
            "Position Qty": st.session_state.positions[symbol]["qty"]
        })

# --- Display Trades Table ---
if st.session_state.trades:
    df = pd.DataFrame(st.session_state.trades)
    st.subheader("📜 Trade History")
    st.dataframe(df, use_container_width=True)

    # Export to CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Trades CSV", csv, "trades.csv", "text/csv")

# --- Display Current Positions ---
if st.session_state.positions:
    st.subheader("📊 Current Positions")
    pos_df = pd.DataFrame([
        {"Symbol": s, "Quantity": p["qty"], "Avg Cost": p["avg_cost"]}
        for s, p in st.session_state.positions.items() if p["qty"] > 0
    ])
    st.dataframe(pos_df, use_container_width=True)
