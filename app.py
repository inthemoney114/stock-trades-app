import streamlit as st
import pandas as pd
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Stock Tracker Dashboard", layout="wide")

# --- User Info ---
user_name = "Ali"
st.title(f"Welcome back, {user_name}!")
st.markdown("### Your Stock Portfolio Dashboard")

# --- Initialize Session State ---
if "trades" not in st.session_state:
    st.session_state.trades = []

# --- LIFO Avg Cost & P/L Logic ---
def update_trades_lifo(trades):
    data = []
    holdings = {}  # symbol -> list of [qty, price] for LIFO
    for t in trades:
        symbol = t['Symbol']
        qty = t['Quantity']
        price = t['Price']
        trade_type = t['Type']

        if symbol not in holdings:
            holdings[symbol] = []

        if trade_type == "Buy":
            holdings[symbol].append([qty, price])
            total_qty = sum(q for q, p in holdings[symbol])
            avg_cost = sum(q*p for q,p in holdings[symbol]) / total_qty
            data.append({**t, "Avg Cost": round(avg_cost, 2), "P/L": 0})
        else:  # Sell
            sell_qty = qty
            pl = 0
            while sell_qty > 0 and holdings[symbol]:
                lot_qty, lot_price = holdings[symbol].pop()
                taken = min(lot_qty, sell_qty)
                pl += taken * (price - lot_price)
                lot_qty -= taken
                sell_qty -= taken
                if lot_qty > 0:
                    holdings[symbol].append([lot_qty, lot_price])
            if holdings[symbol]:
                total_qty = sum(q for q,p in holdings[symbol])
                avg_cost = sum(q*p for q,p in holdings[symbol]) / total_qty
            else:
                avg_cost = 0
            data.append({**t, "Avg Cost": round(avg_cost, 2), "P/L": round(pl, 2)})
    
    df = pd.DataFrame(data)
    if not df.empty:
        df['Total'] = df['Quantity'] * df['Price']
        totals = df[['Quantity', 'Total', 'P/L']].sum()
        totals['Symbol'] = 'TOTAL'
        totals['Type'] = '-'
        totals['Price'] = '-'
        totals['Avg Cost'] = '-'
        df.loc['Total'] = totals
    return df, holdings

# --- Portfolio Overview ---
def portfolio_overview(holdings):
    overview_data = []
    for symbol, lots in holdings.items():
        total_qty = sum(q for q,p in lots)
        if total_qty == 0:
            continue
        avg_cost = sum(q*p for q,p in lots) / total_qty
        last_price = lots[-1][1] if lots else 0
        current_value = total_qty * last_price
        current_cost = total_qty * avg_cost
        overview_data.append({
            "Symbol": symbol,
            "Quantity": total_qty,
            "Avg Cost": round(avg_cost,2),
            "Current Cost": round(current_cost,2),
            "Current Value": round(current_value,2)
        })
    return pd.DataFrame(overview_data)

# --- Add New Trade Form ---
st.sidebar.header("Add / Delete Trades")
with st.sidebar.form("Add Trade"):
    st.subheader("Add a Trade")
    symbol = st.text_input("Symbol").upper()
    trade_type = st.selectbox("Type", ["Buy", "Sell"])
    quantity = st.number_input("Quantity", min_value=1, step=1)
    price = st.number_input("Price", min_value=0.01, step=0.01, format="%.2f")
    date = st.date_input("Date", datetime.today())
    submitted = st.form_submit_button("Add Trade")
    if submitted:
        st.session_state.trades.append({
            "Symbol": symbol,
            "Type": trade_type,
            "Quantity": quantity,
            "Price": price,
            "Date": date
        })
        st.success(f"Trade added: {symbol} {trade_type} {quantity} @ {price}")

# --- Delete Trade ---
if st.session_state.trades:
    with st.sidebar.form("Delete Trade"):
        st.subheader("Delete a Trade")
        delete_index = st.number_input("Trade index to delete", min_value=0, max_value=len(st.session_state.trades)-1, step=1)
        delete_submitted = st.form_submit_button("Delete Trade")
        if delete_submitted:
            removed = st.session_state.trades.pop(delete_index)
            st.warning(f"Deleted trade: {removed}")

# --- Update Trades & Portfolio AFTER any changes ---
trades_df, holdings = update_trades_lifo(st.session_state.trades)
overview_df = portfolio_overview(holdings)

# --- Portfolio Overview at Top ---
st.subheader("Portfolio Overview")
if not overview_df.empty:
    st.dataframe(overview_df, use_container_width=True)
else:
    st.info("No holdings yet.")

# --- Trades Table ---
st.subheader("Trades Table")
st.dataframe(trades_df, use_container_width=True, height=400)

# --- Download CSV ---
if not trades_df.empty:
    csv = trades_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "trades.csv", "text/csv")
