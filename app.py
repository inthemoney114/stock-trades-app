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

# Calculate average cost per ticker for remaining shares
avg_cost_per_stock = {}
for stock in trades_df["Stock"].unique():
    remaining_buys = trades_df[(trades_df["Stock"]==stock) & (trades_df["Action"]=="Buy") & (trades_df["Remaining"]>0)]
    if not remaining_buys.empty:
        avg_cost = ( (remaining_buys["Remaining"] * (remaining_buys["Price"] + remaining_buys["Brokerage"]/remaining_buys["Quantity"])).sum() / remaining_buys["Remaining"].sum() )
    else:
        avg_cost = 0
    avg_cost_per_stock[stock] = round(avg_cost,2)

# Display table
trades_df["Average Cost per Stock"] = trades_df["Stock"].map(avg_cost_per_stock)
st.table(trades_df)

# Portfolio Metrics
st.header("Portfolio Analytics")
total_invested = sum(
    trades_df[trades_df["Action"]=="Buy"]["Remaining"] * trades_df[trades_df["Action"]=="Buy"]["Price"]
)
st.metric("Total Invested", f"${total_invested:,.2f}")
