import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- Page config ---
st.set_page_config(page_title="Trades Dashboard", layout="wide")

# --- CSS for clean dashboard UI ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8f9fa;
        font-family: "Inter", sans-serif;
    }
    .card {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .metric {
        font-size: 22px;
        font-weight: 600;
    }
    .sub {
        color: #6c757d;
        font-size: 13px;
    }
    .delete-btn {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Initialize session state ---
if "trades" not in st.session_state:
    st.session_state.trades = pd.DataFrame(
        columns=["Date", "Symbol", "Side", "Quantity", "Price", "Fees", "TotalCost", "Note"]
    )

# --- Helpers ---
def add_trade(date, symbol, side, qty, price, fees, note):
    qty = float(qty)
    price = float(price)
    fees = float(fees)
    total = qty * price + fees if side == "Buy" else -qty * price + fees
    row = {
        "Date": pd.to_datetime(date).strftime("%Y-%m-%d"),
        "Symbol": symbol.upper(),
        "Side": side,
        "Quantity": qty if side == "Buy" else -qty,
        "Price": price,
        "Fees": fees,
        "TotalCost": total,
        "Note": note,
    }
    st.session_state.trades = pd.concat(
        [st.session_state.trades, pd.DataFrame([row])], ignore_index=True
    )

def delete_trade(index):
    st.session_state.trades.drop(index, inplace=True)
    st.session_state.trades.reset_index(drop=True, inplace=True)

def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Symbol", "Quantity", "AvgCost", "Invested"])
    df2 = df.copy()
    # buys only for cost basis
    buys = df2[df2["Quantity"] > 0]
    agg = buys.groupby("Symbol").apply(
        lambda g: pd.Series({
            "BuyQty": g["Quantity"].sum(),
            "BuyInvested": (g["Quantity"] * g["Price"]).sum() + g["Fees"].sum(),
        })
    ).reset_index()
    qty = df2.groupby("Symbol")["Quantity"].sum().reset_index().rename(columns={"Quantity": "Quantity"})
    summary = pd.merge(qty, agg, on="Symbol", how="left").fillna(0)
    summary["AvgCost"] = summary.apply(
        lambda r: (r.BuyInvested / r.BuyQty) if r.BuyQty > 0 else 0, axis=1
    )
    summary["Invested"] = summary["BuyInvested"]
    final = summary[["Symbol", "Quantity", "AvgCost", "Invested"]]
    final["AvgCost"] = final["AvgCost"].round(4)
    final["Invested"] = final["Invested"].round(2)
    return final.sort_values(by="Symbol").reset_index(drop=True)

# --- Sidebar navigation ---
st.sidebar.title("📊 Dashboard")
page = st.sidebar.radio("Navigate", ["Dashboard", "Trades", "Summary", "Export"])

# --- Dashboard Page ---
if page == "Dashboard":
    st.title("📈 Trades Dashboard")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card'><div class='metric'>"
                    f"{len(st.session_state.trades)}"
                    "</div><div class='sub'>Total Trades</div></div>", unsafe_allow_html=True)
    with col2:
        total_qty = st.session_state.trades["Quantity"].sum() if not st.session_state.trades.empty else 0
        st.markdown("<div class='card'><div class='metric'>"
                    f"{total_qty:.2f}"
                    "</div><div class='sub'>Net Quantity</div></div>", unsafe_allow_html=True)
    with col3:
        invested = compute_summary(st.session_state.trades)["Invested"].sum() if not st.session_state.trades.empty else 0
        st.markdown("<div class='card'><div class='metric'>$"
                    f"{invested:.2f}"
                    "</div><div class='sub'>Total Invested</div></div>", unsafe_allow_html=True)

# --- Trades Page ---
elif page == "Trades":
    st.title("📝 Manage Trades")

    with st.form("trade_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            date = st.date_input("Date", value=datetime.today())
        with c2:
            symbol = st.text_input("Symbol", value="AAPL")
        with c3:
            side = st.selectbox("Side", ["Buy", "Sell"])

        c4, c5, c6 = st.columns(3)
        with c4:
            qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=1.0, format="%.4f")
        with c5:
            price = st.number_input("Price", min_value=0.0, value=100.0, format="%.4f")
        with c6:
            fees = st.number_input("Fees", min_value=0.0, value=0.0, format="%.2f")

        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Add Trade ➕")
        if submitted and symbol:
            add_trade(date, symbol, side, qty, price, fees, note)
            st.success(f"Added {side} {qty} {symbol.upper()} @ {price}")

    st.markdown("---")
    if st.session_state.trades.empty:
        st.info("No trades yet.")
    else:
        st.subheader("Your Trades")
        for i, row in st.session_state.trades.iterrows():
            cols = st.columns([6,1])
            with cols[0]:
                st.write(
                    f"**{row['Date']}** | {row['Side']} {row['Quantity']} {row['Symbol']} @ {row['Price']} | Fees: {row['Fees']} | Note: {row['Note']}"
                )
            with cols[1]:
                if st.button("🗑️", key=f"del_{i}"):
                    delete_trade(i)
                    st.experimental_rerun()

# --- Summary Page ---
elif page == "Summary":
    st.title("📊 Summary")
    summary = compute_summary(st.session_state.trades)
    if summary.empty:
        st.info("No summary yet — add some trades.")
    else:
        st.dataframe(summary)

# --- Export Page ---
elif page == "Export":
    st.title("📤 Export Trades")
    if st.session_state.trades.empty:
        st.info("No trades to export.")
    else:
        buffer = io.StringIO()
        st.session_state.trades.to_csv(buffer, index=False)
        st.download_button("Download CSV", data=buffer.getvalue(), file_name="trades.csv", mime="text/csv")
