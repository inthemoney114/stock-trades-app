import streamlit as st
import pandas as pd

st.set_page_config(page_title="Stock Portfolio Tracker", layout="wide")

# ---- Initialize session state ----
if "trades" not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Stock", "Action", "Quantity", "Price", "Brokerage", "Remaining"
    ])

# ---- Title ----
st.title("📈 Stock Portfolio Tracker")
st.markdown("Manage your trades and see your portfolio at a glance.")

# ---- Add a Trade ----
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
        st.session_state.trades = pd.concat(
            [st.session_state.trades, new_trade], ignore_index=True
        )
        st.success(f"{action} trade added: {qty} shares of {stock} at ${price} with ${brokerage} brokerage")

# ---- Portfolio Calculation ----
st.header("Portfolio Overview")

portfolio_data = []

for stock, trades in st.session_state.trades.groupby("Stock"):
    buys = trades[trades["Action"] == "Buy"].copy()
    sells = trades[trades["Action"] == "Sell"].copy()

    # Process sells using FIFO
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

    remaining_qty = buys["Remaining"].sum()
    if remaining_qty > 0:
        # Average cost per share includes proportional brokerage
        avg_cost = ( (buys["Remaining"] * (buys["Price"] + buys["Brokerage"]/buys["Quantity"])).sum() / remaining_qty )
    else:
        avg_cost = 0

    portfolio_data.append({
        "Stock": stock,
        "Quantity": remaining_qty,
        "Average Cost": round(avg_cost, 2),
        "Current Price": 0.0,  # Replace with live price if desired
        "Unrealized P/L": 0.0  # Can calculate if current price is set
    })

portfolio_df = pd.DataFrame(portfolio_data)
st.table(portfolio_df)

# ---- Portfolio Metrics ----
st.header("Portfolio Analytics")

if not portfolio_df.empty and "Average Cost" in portfolio_df.columns and "Quantity" in portfolio_df.columns:
    total_invested = (portfolio_df["Quantity"] * portfolio_df["Average Cost"]).sum()
    total_value = (portfolio_df["Quantity"] * portfolio_df["Current Price"]).sum()
    total_pl = total_value - total_invested
else:
    total_invested = total_value = total_pl = 0

st.metric("Total Invested", f"${total_invested:,.2f}")
st.metric("Current Value", f"${total_value:,.2f}")
st.metric("Total P/L", f"${total_pl:,.2f}")

# ---- Notes / Info ----
st.header("Notes / Info")
st.text_area("Notes", height=100, placeholder="Write any notes here...")
