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

# ---- Portfolio section ----
st.header("Portfolio Overview")
# Example DataFrame (replace with your own data)
data = {
    "Stock": ["AAPL", "TSLA"],
    "Quantity": [50, 10],
    "Avg Cost": [170.0, 650.0],
    "Current Price": [180.0, 700.0],
    "P/L": [500, 500],
}
df = pd.DataFrame(data)
st.table(df)

# ---- Analytics ----
st.header("Portfolio Analytics")
total_invested = sum(df["Quantity"] * df["Avg Cost"])
current_value = sum(df["Quantity"] * df["Current Price"])
total_pl = current_value - total_invested

st.metric("Total Invested", f"${total_invested:,.2f}")
st.metric("Current Value", f"${current_value:,.2f}")
st.metric("Total P/L", f"${total_pl:,.2f}")

# ---- Notes / Info ----
st.header("Notes / Info")
st.text_area("Notes", height=100, placeholder="Write any notes here...")
