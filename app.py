import streamlit as st
import pandas as pd
from datetime import datetime
import io

st.set_page_config(page_title="SciFi Trades", layout="wide", initial_sidebar_state="expanded")

# --- inject small CSS for a modern sci-fi look ---
st.markdown(
    """
    <style>
    :root{
      --bg:#0b1020; /* deep space */
      --panel:#0f1724; /* darker card */
      --accent:#7cf6ff; /* cyan */
      --accent-2:#b67bff; /* purple */
      --muted:#94a3b8;
    }
    .stApp {
      background: linear-gradient(180deg, var(--bg), #071022 140%);
      color: white;
      font-family: 'Segoe UI', Roboto, Arial, sans-serif;
    }
    .stSidebar { background: rgba(9,12,20,0.65); }
    .card { background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); padding:16px; border-radius:12px; }
    .accent { color: var(--accent); }
    .accent-2 { color: var(--accent-2); }
    .small-muted { color: var(--muted); font-size:12px }
    /* better looking tables */
    .dataframe thead tr:only-child th {
      text-align: left;
    }
    @media (max-width: 600px){
      .big-hero { font-size:20px !important }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- helpers ---

def init_session():
    if "trades" not in st.session_state:
        st.session_state.trades = pd.DataFrame(
            columns=["Date", "Symbol", "Side", "Quantity", "Price", "Fees", "TotalCost", "Note"]
        )


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
    st.session_state.trades = pd.concat([st.session_state.trades, pd.DataFrame([row])], ignore_index=True)


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Symbol", "Quantity", "AvgCost", "Invested"])
    df2 = df.copy()
    # for average cost use only buys to compute cost basis; subtract sells from qty
    buys = df2[df2["Quantity"] > 0]
    agg = buys.groupby("Symbol").apply(
        lambda g: pd.Series({
            "BuyQty": g["Quantity"].sum(),
            "BuyInvested": (g["Quantity"] * g["Price"]).sum() + g["Fees"].sum(),
        })
    ).reset_index()
    # overall quantity (buys minus sells)
    qty = df2.groupby("Symbol")["Quantity"].sum().reset_index().rename(columns={"Quantity": "Quantity"})
    summary = pd.merge(qty, agg, on="Symbol", how="left").fillna(0)
    summary["AvgCost"] = summary.apply(lambda r: (r.BuyInvested / r.BuyQty) if r.BuyQty > 0 else 0, axis=1)
    summary["Invested"] = summary["BuyInvested"]
    final = summary[["Symbol", "Quantity", "AvgCost", "Invested"]]
    final["AvgCost"] = final["AvgCost"].round(4)
    final["Invested"] = final["Invested"].round(2)
    final = final.sort_values(by="Symbol").reset_index(drop=True)
    return final


# --- UI ---
init_session()

col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("# <span class='accent big-hero'>SciFi Trades</span>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Simple responsive Streamlit app to log trades and calculate average cost per symbol. Compact, fast, and mobile-friendly.</div>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("trade_form"):
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            date = st.date_input("Date", value=datetime.today())
            symbol = st.text_input("Symbol", value="AAPL")
            side = st.selectbox("Side", ["Buy", "Sell"])
        with dcol2:
            qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=1.0, format="%.4f")
            price = st.number_input("Price", min_value=0.0, value=100.0, format="%.4f")
            fees = st.number_input("Fees", min_value=0.0, value=0.0, format="%.2f")

        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Add trade")
        if submitted:
            if not symbol:
                st.warning("Please enter a ticker symbol.")
            else:
                add_trade(date, symbol, side, qty, price, fees, note)
                st.success(f"Added {side} {qty} {symbol.upper()} @ {price}")

    st.markdown("---")
    st.markdown("### Import / Export")
    uploaded = st.file_uploader("Upload CSV to load existing trades", type=["csv"]) 
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            # basic validation
            required = {"Date","Symbol","Side","Quantity","Price","Fees","TotalCost","Note"}
            if set(df.columns) >= required:
                st.session_state.trades = df
                st.success("Loaded trades from CSV")
            else:
                st.error("CSV is missing required columns. Expected columns: Date, Symbol, Side, Quantity, Price, Fees, TotalCost, Note")
        except Exception as e:
            st.error(f"Failed to load CSV: {e}")

    buffer = io.StringIO()
    if not st.session_state.trades.empty:
        st.session_state.trades.to_csv(buffer, index=False)
        st.download_button("Download trades CSV", data=buffer.getvalue(), file_name="trades.csv", mime="text/csv")

with col2:
    st.markdown("### Trades")
    if st.session_state.trades.empty:
        st.info("No trades yet — add one on the left.")
    else:
        df = st.session_state.trades.copy()
        df["Date"] = pd.to_datetime(df["Date"]) 
        df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)
        st.dataframe(df.style.set_precision(4))

    st.markdown("---")
    st.markdown("### Summary")
    summary = compute_summary(st.session_state.trades)
    if summary.empty:
        st.info("No summary to show — add buy trades to see average cost per symbol.")
    else:
        st.table(summary)

# small footer
st.markdown("---")
st.markdown("<div class='small-muted'>Pro tip: To keep your data available across devices, save the exported CSV to Google Drive or a private GitHub repo and re-upload when you open the app on another device.</div>", unsafe_allow_html=True)

# --- end of app ---
