import streamlit as st
import pandas as pd

st.set_page_config(page_title="Stock Portfolio Tracker", layout="wide")

# Initialize trades
if "trades" not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Stock", "Action", "Quantity", "Price", "Brokerage", "Remaining"
    ])

# Title
st.title("📈 Stock Portfolio Tracker")
st.markdown("Manage your trades and see your portfolio at a glance.")

# Add a trade
st.header("Add a Trade")
with st.form("trade_form"):
    stock = st.text_input("Stock Symbol")
    action = st.selectbox("Action", ["Buy", "Sell"])
    qty = st.number_input("Quantity", min_value=1, step=1)
    price = st.number_input("Price per Share", min_value=0.0, step=0.01)
    brokerage = st.number_input("Brokerage ($)", min_value=0.0, step=0.01, value=0.0)
    submitted = st.form_submit_button("Submit Trade")
    
    if submitted:
        remaining = qty if action == "Buy" else 0
        new_trade = pd.DataFrame({
            "Stock": [stock],
            "Action": [action],
            "Quantity": [qty],
            "Price": [price],
            "Brokerage": [brokerage],
            "Remaining": [remaining]
        })
        st.session_state.trades = pd.concat([st.session_state.trades, new_trade], ignore_index=True)
        st.success(f"{action} trade added: {qty} shares of {stock} at ${price} with ${brokerage} brokerage")

# Portfolio Overview
st.header("Portfolio Overview")
trades_df = st.session_state.trades.copy()

# Process sells using FIFO per stock
for stock in trades_df["Stock"].unique():
    buys = trades_df[(trades_df["Stock"]==stock) & (trades_df["Action"]=="Buy")].copy()
    sells = trades_df[(trades_df["Stock"]==stock) & (trades_df["Action"]=="Sell")].copy()
    
    # Reduce remaining per buy lot
    for _, sell in sells.iterrows():
        qty_to_sell = sell["Quantity"]
        for bidx, buy in buys.iterrows():
            if buys.at[bidx, "Remaining"] >= qty_to_sell:
                buys.at[bidx, "Remaining"] -= qty_to_sell
                qty_to_sell = 0
                break
            else:
                qty_to_sell -= buys.at[bidx, "Remaining"]
                buys.at[bidx, "Remaining"] = 0
    trades_df.loc[buys.index, "Remaining"] = buys["Remaining"]

# Calculate progressive average cost per row for each stock
trades_df["Progressive Avg Cost"] = 0.0

for stock in trades_df["Stock"].unique():
    remaining_buys = trades_df[(trades_df["Stock"]==stock) & (trades_df["Action"]=="Buy")].copy()
    total_qty = 0
    total_cost = 0.0
    for idx, row in remaining_buys.iterrows():
        if row["Remaining"] > 0:
            lot_qty = row["Remaining"]
            lot_cost = lot_qty * (row["Price"] + row["Brokerage"]/row["Quantity"])
            total_qty += lot_qty
            total_cost += lot_cost
            trades_df.at[idx, "Progressive Avg Cost"] = total_cost / total_qty
        else:
            trades_df.at[idx, "Progressive Avg Cost"] = 0.0

st.table(trades_df)
