import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Stock Portfolio Tracker", layout="wide")

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
        st.success(f"{action} trade added: {qty} shares of {stock} at ${price}")
        # Here you would add the trade to your session_state or database

# ---- Portfolio section ----
st.header("Portfolio Overview")
# Empty placeholder DataFrame for now
df = pd.DataFrame(columns=["Stock","Quantity","Avg Cost","Current Price","P/L"])
st.table(df)

# ---- Analytics ----
st.header("Portfolio Analytics")
st.metric("Total Invested", "$0.00")
st.metric("Current Value", "$0.00")
st.metric("Total P/L", "$0.00")

# ---- Notes / Info ----
st.header("Notes / Info")
st.text_area("Notes", height=100, placeholder="Write any notes here...")
