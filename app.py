import streamlit as st
import pandas as pd
from stock_selection_v1 import run_stock_selection

st.set_page_config(page_title="Stock Screener", layout="wide")

st.title("📈 Stock Screener Dashboard")

# ---------------- CACHE ---------------- #
@st.cache_data
def cached_run(tickers):
    return run_stock_selection(tickers)

# ---------------- SIDEBAR ---------------- #
st.sidebar.header("🔧 Controls")

# 🔹 CSV Upload
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV (with 'ticker' column)",
    type=["csv"]
)

# 🔹 Manual Input
tickers_input = st.sidebar.text_area(
    "Or enter tickers manually",
    "RELIANCE.NS,TCS.NS,INFY.NS"
)

# 🔹 Filters
min_rsi = st.sidebar.slider("Minimum RSI", 30, 80, 55)
min_rr = st.sidebar.slider("Minimum RR", 0.5, 5.0, 1.5)

bullish_only = st.sidebar.checkbox("Bullish Trend Only", True)
macd_positive = st.sidebar.checkbox("MACD Positive", True)

top_n = st.sidebar.slider("Top Trades", 5, 50, 10)

run_button = st.sidebar.button("🚀 Run Screener")

# ---------------- INPUT HANDLING ---------------- #

def get_tickers():
    # Priority: CSV > Manual input
    if uploaded_file is not None:
        df_upload = pd.read_csv(uploaded_file)

        # Normalize column names
        df_upload.columns = [c.lower() for c in df_upload.columns]

        # Accept both 'symbol' and 'ticker'
        col_found = None
        for col in ['symbol', 'ticker']:
            if col in df_upload.columns:
                col_found = col
                break

        if col_found is None:
            st.error("CSV must contain 'Symbol' or 'ticker' column")
            return []

        tickers = (
            df_upload[col_found]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
            .tolist()
        )

    else:
        tickers = [
            t.strip().upper()
            for t in tickers_input.split(",")
            if t.strip()
        ]

    # 🔥 Append .NS safely
    tickers = [
        t if t.endswith(".NS") else f"{t}.NS"
        for t in tickers
    ]

    # Remove duplicates
    tickers = list(dict.fromkeys(tickers))

    return tickers

# ---------------- MAIN ---------------- #
if run_button:

    tickers = get_tickers()

    if not tickers:
        st.warning("No tickers provided")
        st.stop()

    st.write(f"📌 Running for {len(tickers)} tickers")

    with st.spinner("Analyzing stocks..."):
        try:
            df = cached_run(tickers)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    if df.empty:
        st.warning("No data returned")
        st.stop()

    st.success("Analysis Complete")

    # ---------------- KPI METRICS ---------------- #
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Stocks", len(df))
    col2.metric("Avg RSI", round(df['RSI'].mean(), 2))
    col3.metric("Bullish Count", int((df['Above_SMA9'] == 1).sum()))
    col4.metric("High RR (>2)", int((df['RR'] > 2).sum()))

    # ---------------- FILTER LOGIC ---------------- #
    df_filtered = df.copy()

    if bullish_only:
        df_filtered = df_filtered[df_filtered['Above_SMA9'] == 1]

    if macd_positive:
        df_filtered = df_filtered[df_filtered['MACD'] == 1]

    df_filtered = df_filtered[df_filtered['RSI'] >= min_rsi]
    df_filtered = df_filtered[df_filtered['RR'] >= min_rr]
    df_filtered = df_filtered[df_filtered['Target %'] > 0]

    # ---------------- TOP TRADES ---------------- #
    if not df_filtered.empty:
        df_filtered = df_filtered.copy()

        df_filtered['RankScore'] = (
            df_filtered['Score'] * 0.6 +
            df_filtered['RR'] * 0.4
        )

        df_top = df_filtered.sort_values(
            by="RankScore", ascending=False
        ).head(top_n)
    else:
        df_top = pd.DataFrame()

    # ---------------- DISPLAY ---------------- #
    tab1, tab2, tab3 = st.tabs(["📊 All Stocks", "✅ Filtered", "🔥 Top Trades"])

    with tab1:
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.dataframe(df_filtered, use_container_width=True)

    with tab3:
        st.dataframe(df_top, use_container_width=True)

    # ---------------- CHARTS ---------------- #
    st.subheader("📊 RSI Distribution")
    st.bar_chart(df['RSI'])

    if not df_top.empty:
        st.subheader("🔥 Top Trades Upside %")
        st.bar_chart(df_top.set_index('ticker')['Target %'])

    # ---------------- DOWNLOAD ---------------- #
    st.download_button(
        "⬇️ Download Top Trades",
        df_top.to_csv(index=False),
        "top_trades.csv",
        "text/csv"
    )
