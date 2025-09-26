import streamlit as st
import pandas as pd

st.set_page_config(page_title="Stock Portfolio Tracker", layout="wide")

# Initialize trades
if "trades" not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Stock", "Action", "Quantity", "Price", "Brokerage", "Remaining"
    ])

st.title("📈 Stock Portfolio Tracker")
st.markdown("Add, track, and manage your trades with FIFO average cost calculation.")

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
        st.session_state.trades = pd.concat([st.session_state.trades, new_trade], ignore_index=True)
        st.success(f"{action} trade added: {qty} shares of {stock} at ${price} with ${brokerage} brokerage")

# ---- Process FIFO sells ----
trades_df = st.session_state.trades.copy()
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

# ---- Calculate Progressive Average Cost ----
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

# ---- Display table with delete buttons ----
st.header("Portfolio Trades")

if not trades_df.empty:
    # Header row
    headers = ["Stock","Action","Quantity","Price","Brokerage","Remaining","Avg Cost","Delete"]
    col_widths = [1.5,1,1,1,1,1,1,0.5]
    cols = st.columns(col_widths)
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    
    # Trade rows
    for idx, row in trades_df.iterrows():
        cols = st.columns(col_widths)
        cols[0].write(row['Stock'])
        cols[1].write(row['Action'])
        cols[2].write(row['Quantity'])
        cols[3].write(f"${row['Price']:.2f}")
        cols[4].write(f"${row['Brokerage']:.2f}")
        cols[5].write(row['Remaining'])
        cols[6].write(f"${row['Progressive Avg Cost']:.2f}")
        if cols[7].button("Delete", key=f"del_{idx}"):
            st.session_state.trades.drop(index=idx, inplace=True)
            st.session_state.trades.reset_index(drop=True, inplace=True)
            st.experimental_rerun()
else:
    st.write("No trades yet.")

# ---- Portfolio Metrics ----
st.header("Portfolio Metrics")
remaining_buys = trades_df[(trades_df["Action"]=="Buy") & (trades_df["Remaining"]>0)]
if not remaining_buys.empty:
    total_qty = remaining_buys["Remaining"].sum()
    total_invested = (remaining_buys["Remaining"] * (remaining_buys["Price"] + remaining_buys["Brokerage"]/remaining_buys["Quantity"])).sum()
else:
    total_qty = total_invested = 0

st.metric("Total Shares Remaining", f"{total_qty}")
st.metric("Total Invested ($)", f"${total_invested:,.2f}")
