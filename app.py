import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Stock Tracker", layout="wide")

# Initialize session state
if "trades" not in st.session_state:
    st.session_state.trades = []

# Helper functions
def calculate_lifo_avg_cost(trades, symbol):
    """
    Calculate average cost for a given symbol using LIFO method.
    Returns current average cost.
    """
    relevant_trades = [t for t in trades if t['Symbol'] == symbol]
    position = 0
    total_cost = 0
    for trade in reversed(relevant_trades):
        if trade['Type'] == "Buy":
            qty_to_add = min(trade['Quantity'], position) if position > 0 else trade['Quantity']
            total_cost += qty_to_add * trade['Price']
            position += trade['Quantity']
        elif trade['Type'] == "Sell":
            position -= trade['Quantity']
    return round(total_cost / position, 2) if position != 0 else 0

def update_trades():
    df = pd.DataFrame(st.session_state.trades)
    if not df.empty:
        df['Total'] = df['Quantity'] * df['Price']
        df['Avg Cost'] = df.apply(lambda x: calculate_lifo_avg_cost(st.session_state.trades, x['Symbol']), axis=1)
        df['P/L'] = df.apply(lambda x: (x['Price'] - x['Avg Cost']) * x['Quantity'] if x['Type']=="Sell" else 0, axis=1)
        df.loc['Total'] = df[['Quantity', 'Total', 'P/L']].sum()
        df.at['Total', 'Symbol'] = "TOTAL"
        df.at['Total', 'Type'] = "-"
        df.at['Total', 'Price'] = "-"
        df.at['Total', 'Avg Cost'] = "-"
    else:
        df = pd.DataFrame()
    return df

# Add new trade
with st.form("Add Trade"):
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

# Delete trade
st.subheader("Delete a Trade")
if st.session_state.trades:
    delete_index = st.number_input("Trade index to delete", min_value=0, max_value=len(st.session_state.trades)-1, step=1)
    if st.button("Delete Trade"):
        removed = st.session_state.trades.pop(delete_index)
        st.warning(f"Deleted trade: {removed}")
else:
    st.info("No trades to delete.")

# Show trades
st.subheader("Trades Table")
trades_df = update_trades()
st.dataframe(trades_df, use_container_width=True, height=400)

# Download option
if not trades_df.empty:
    csv = trades_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "trades.csv", "text/csv")
