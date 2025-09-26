import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Stock Portfolio Tracker", layout="wide")

# ---- Initialize session state ----
if "trades" not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=["Stock","Quantity","Price","Action"])

# ---- Title ----
st.title("📈 Stock Portfolio Tracker")
st.markdown("Manage your trades and see your portfolio at a glance.")

# ---- Input section ----
st.header("Add a Trade")
with st.form("trade_form"):
    stock = st.text_input("Stock Symbol")
    qty = st.number_input("Quantity", min_value=1, step=1)
    price = st.number_input("Price per Share", min_value=0.0, step=0.01)
    action = st.selectbox("Action", ["Buy", "Sell"])
    submitted = st.form_submit_button("Submit Trade")
    if submitted:
        # Add trade to session state
        st.session_state.trades = pd.concat([
            st.session_state.trades,
            pd.DataFrame({"Stock":[stock], "Quantity":[qty], "Price":[price], "Action":[action]})
        ], ignore_index=True)
        st.success(f"{action} trade added: {qty} shares of {stock} at ${price}")

# ---- Portfolio section ----
st.header("Portfolio Overview")
st.table(st.session_state.trades)

# ---- Analytics ----
st.header("Portfolio Analytics")
if not st.session_state.trades.empty:
    buys = st.session_state.trades[st.session_state.trades["Action"]=="Buy"]
    sells = st.session_state.trades[st.session_state.trades["Action"]=="Sell"]
    
    total_invested = (buys["Quantity"] * buys["Price"]).sum()
    total_sold = (sells["Quantity"] * sells["Price"]).sum()
    current_value = total_invested - total_sold  # simple placeholder
    total_pl = current_value - total_invested
    
    st.metric("Total Invested", f"${total_invested:,.2f}")
    st.metric("Current Value", f"${current_value:,.2f}")
    st.metric("Total P/L", f"${total_pl:,.2f}")
else:
    st.metric("Total Invested", "$0.00")
    st.metric("Current Value", "$0.00")
    st.metric("Total P/L", "$0.00")

# ---- Notes / Info ----
st.header("Notes / Info")
st.text_area("Notes", height=100, placeholder="Write any notes here...")
