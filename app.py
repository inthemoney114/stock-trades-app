import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Stock Tracker Dashboard", layout="wide")

# --- User Info ---
user_name = "Ali"
st.title(f"Welcome back, {user_name}!")
st.markdown("### Your Stock Portfolio Dashboard")

# --- Initialize Session State ---
if "trades" not in st.session_state:
    st.session_state.trades = []
if "live_prices" not in st.session_state:
    st.session_state.live_prices = {}  # store user-entered live prices

# --- LIFO Avg Cost & P/L Logic ---
def update_trades_lifo(trades):
    data = []
    holdings = {}
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

# --- Fetch Latest ASX Prices ---
@st.cache_data(show_spinner=False)
def fetch_asx_price(symbol):
    # ASX symbols on Yahoo end with .AX
    yf_symbol = symbol if symbol.endswith(".AX") else symbol + ".AX"
    try:
        ticker = yf.Ticker(yf_symbol)
        price = ticker.fast_info['last_price']
        return price
    except Exception:
        return None

# --- Portfolio Overview ---
def portfolio_overview(holdings):
    overview_data = []
    for symbol, lots in holdings.items():
        total_qty = sum(q for q,p in lots)
        if total_qty == 0:
            continue
        avg_cost = sum(q*p for q,p in lots) / total_qty

        # Try to fetch live price from Yahoo Finance
        live_price = fetch_asx_price(symbol)
        if not live_price:
            # fallback to user-entered or last trade price
            live_price = st.session_state.live_prices.get(symbol) or (lots[-1][1] if lots else 0)

        current_value = total_qty * live_price
        current_cost = total_qty * avg_cost
        overview_data.append({
            "Symbol": symbol,
            "Quantity": total_qty,
            "Avg Cost": round(avg_cost,2),
            "Current Cost": round(current_cost,2),
            "Current Value": round(current_value,2),
            "Live Price": round(live_price,2)
        })
    return pd.DataFrame(overview_data)

# --- Format Trades Table ---
def style_trades(df):
    df_main = df[df['Symbol'] != 'TOTAL'].copy()
    df_total = df[df['Symbol'] == 'TOTAL'].copy()

    def color_pl(val):
        if isinstance(val, (int, float)):
            if val < 0:
                return 'color: red'
            elif val > 0:
                return 'color: green'
        return ''

    styled = df_main.style.format({
        'Price': '${:,.2f}',
        'Avg Cost': '${:,.2f}',
        'Total': '${:,.2f}',
        'P/L': '${:,.2f}'
    }).applymap(color_pl, subset=['P/L'])

    return styled, df_total

# --- Trade Management Panel ---
st.markdown("## 📝 Trade Management")
col_add, col_delete = st.columns([2, 1])

# --- Add Trade Form ---
with col_add.form("Add Trade"):
    st.markdown("### ➕ Add a Trade")
    symbol = st.text_input("Symbol").upper()
    trade_type = st.selectbox("Type", ["Buy", "Sell"])
    quantity = st.number_input("Quantity", min_value=1, step=1)
    price = st.number_input("Price", min_value=0.01, step=0.01, format="%.2f")
    date = st.date_input("Date", datetime.today())
    submitted_add = st.form_submit_button("Add Trade")
    if submitted_add:
        st.session_state.trades.append({
            "Symbol": symbol,
            "Type": trade_type,
            "Quantity": quantity,
            "Price": price,
            "Date": date
        })
        st.success(f"Trade added: {symbol} {trade_type} {quantity} @ {price}")

# --- Delete Trade Form ---
with col_delete.form("Delete Trade"):
    st.markdown("### 🗑️ Delete a Trade")
    if st.session_state.trades:
        delete_index = st.number_input(
            "Trade index to delete", min_value=0, max_value=len(st.session_state.trades)-1, step=1
        )
        submitted_delete = st.form_submit_button("Delete Trade")
        if submitted_delete:
            removed = st.session_state.trades.pop(delete_index)
            st.warning(f"Deleted trade: {removed}")
    else:
        st.info("No trades to delete.")
        st.form_submit_button("Delete Trade")  # dummy submit

# --- Manual Live Price Input ---
st.subheader("Update Live Prices")
if st.session_state.trades:
    with st.form("Live Prices"):
        live_symbol = st.selectbox("Select Symbol", sorted(set(t["Symbol"] for t in st.session_state.trades)))
        live_price = st.number_input("Enter Current Price", min_value=0.01, step=0.01, format="%.2f")
        submitted_live = st.form_submit_button("Update Price")
        if submitted_live:
            st.session_state.live_prices[live_symbol] = live_price
            st.success(f"Updated {live_symbol} live price to {live_price}")
else:
    st.info("Add a trade first to update live prices.")

# --- UPDATE TRADES & PORTFOLIO AFTER ADD/DELETE ---
trades_df, holdings = update_trades_lifo(st.session_state.trades)
overview_df = portfolio_overview(holdings)

# --- Summary Cards ---
st.markdown("## 📦 Portfolio Summary")
if not overview_df.empty:
    total_value = overview_df["Current Value"].sum()
    total_cost = overview_df["Current Cost"].sum()
    total_pl = total_value - total_cost
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Cost", f"${total_cost:,.2f}")
    col2.metric("📈 Current Value", f"${total_value:,.2f}")
    if total_pl >= 0:
        col3.metric("✅ Unrealized P/L", f"${total_pl:,.2f}", f"🟢 +${total_pl:,.2f}")
    else:
        col3.metric("❌ Unrealized P/L", f"${total_pl:,.2f}", f"-${abs(total_pl):,.2f}", delta_color="normal")

# --- Portfolio Dashboard Cards per Symbol ---
st.markdown("## 📊 Portfolio Overview by Symbol")
if not overview_df.empty:
    for idx, row in overview_df.iterrows():
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label=f"{row['Symbol']} Quantity", value=f"{row['Quantity']:,}")
        col2.metric(label="Avg Cost", value=f"${row['Avg Cost']:,.2f}")
        col3.metric(label="Current Cost", value=f"${row['Current Cost']:,.2f}")
        col4.metric(label="Live Price", value=f"${row['Live Price']:,.2f}")
        current_value = row['Current Value']
        unrealized_pl = current_value - row['Current Cost']

        if unrealized_pl < 0:
            col4.metric("Current Value (Unrealized P/L)", f"${current_value:,.2f}", f"-${abs(unrealized_pl):,.2f}", delta_color="normal")
        elif unrealized_pl > 0:
            col4.metric("Current Value (Unrealized P/L)", f"${current_value:,.2f}", f"🟢 ${unrealized_pl:,.2f}", delta_color="normal")
        else:
            col5.metric("Current Value (Unrealized P/L)", f"${current_value:,.2f}", "$0.00", delta_color="off")

    # --- Modern Graphs ---
    st.markdown("#### Portfolio Value Breakdown")
    pie_fig = px.pie(overview_df, names="Symbol", values="Current Value", title="Holdings by Value", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(pie_fig, use_container_width=True)

    st.markdown("#### Portfolio Value Over Time (Simulated)")
    # Simulate portfolio value over time using trades
    if not trades_df.empty:
        trades_df_sorted = trades_df[trades_df['Symbol'] != 'TOTAL'].sort_values("Date")
        portfolio_value = []
        value = 0
        for i, row in trades_df_sorted.iterrows():
            if row['Type'] == 'Buy':
                value += row['Quantity'] * row['Price']
            elif row['Type'] == 'Sell':
                value -= row['Quantity'] * row['Price']
            portfolio_value.append({"Date": row['Date'], "Value": value})
        value_df = pd.DataFrame(portfolio_value)
        if not value_df.empty:
            line_fig = go.Figure()
            line_fig.add_trace(go.Scatter(x=value_df['Date'], y=value_df['Value'], mode='lines+markers', name='Portfolio Value'))
            line_fig.update_layout(title="Portfolio Value Over Time", xaxis_title="Date", yaxis_title="Value ($)", template="plotly_white")
            st.plotly_chart(line_fig, use_container_width=True)
else:
    st.info("No holdings yet.")

# --- Trades Table ---
st.subheader("Trades Table")
if not trades_df.empty:
    styled_df, total_row = style_trades(trades_df)
    st.dataframe(styled_df, use_container_width=True, height=400)
    if not total_row.empty:
        st.markdown("**TOTAL**")
        st.dataframe(total_row, use_container_width=True)
else:
    st.info("No trades yet.")

# --- Download CSV ---
if not trades_df.empty:
    csv = trades_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "trades.csv", "text/csv")
