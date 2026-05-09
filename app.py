import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

from stock_selection_v1 import run_stock_selection

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="Stock Screener", layout="wide")

st.title("📈 Stock Screener Dashboard")

# ---------------- CACHE ---------------- #
@st.cache_data
def cached_run(tickers):
    return run_stock_selection(tickers)

# ---------------- SIDEBAR ---------------- #
st.sidebar.header("🔧 Controls")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV (Symbol / ticker column)",
    type=["csv"]
)

tickers_input = st.sidebar.text_area(
    "Or enter tickers manually",
    "RELIANCE.NS,TCS.NS,INFY.NS"
)

min_rsi = st.sidebar.slider("Minimum RSI", 30, 80, 55)
min_rr = st.sidebar.slider("Minimum RR", 0.5, 5.0, 1.5)

bullish_only = st.sidebar.checkbox("Bullish Trend Only", True)
macd_positive = st.sidebar.checkbox("MACD Positive", True)

top_n = st.sidebar.slider("Top Trades", 5, 50, 10)

run_button = st.sidebar.button("🚀 Run Screener")

# ---------------- TICKER HANDLING ---------------- #
def get_tickers():
    if uploaded_file is not None:
        df_upload = pd.read_csv(uploaded_file)
        df_upload.columns = [c.lower() for c in df_upload.columns]

        col_found = None
        for col in ['symbol', 'ticker']:
            if col in df_upload.columns:
                col_found = col
                break

        if col_found is None:
            st.error("CSV must contain 'Symbol' or 'ticker'")
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

    # Append .NS safely
    tickers = [
        t if t.endswith(".NS") else f"{t}.NS"
        for t in tickers
    ]

    # Remove duplicates
    tickers = list(dict.fromkeys(tickers))

    return tickers

# ---------------- CHART FUNCTION ---------------- #
def plot_stock_chart(ticker):
    df = yf.download(ticker, period="6mo", auto_adjust=True, progress=False)

    if df.empty:
        return None

    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Close"))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20"))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="SMA 50"))

    fig.update_layout(
        title=f"{ticker} Price Chart",
        height=500
    )

    return fig

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

    # ---------------- KPI ---------------- #
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Stocks", len(df))
    col2.metric("Avg RSI", round(df['RSI'].mean(), 2))
    col3.metric("Bullish Count", int((df['Above_SMA9'] == 1).sum()))
    col4.metric("High RR (>2)", int((df['RR'] > 2).sum()))

    # ---------------- FILTER ---------------- #
    df_filtered = df.copy()

    if bullish_only:
        df_filtered = df_filtered[df_filtered['Above_SMA9'] == 1]

    if macd_positive:
        df_filtered = df_filtered[df_filtered['MACD'] == 1]

    df_filtered = df_filtered[df_filtered['RSI'] >= min_rsi]
    df_filtered = df_filtered[df_filtered['Target %'] > 0]

    # Safe RR filter (optional)
    df_filtered = df_filtered[df_filtered['RR'].notna()]
    df_filtered = df_filtered[df_filtered['RR'] >= min_rr]

    # ---------------- RANK SCORE ---------------- #
    df_filtered['RankScore'] = (
        df_filtered['Score'] * 0.6 +
        df_filtered['RR'].fillna(0) * 0.4
    )

    df_top = df_filtered.sort_values(
        by="RankScore", ascending=False
    ).head(top_n)

    # ---------------- TABS ---------------- #
    tab1, tab2, tab3 = st.tabs(["📊 All Stocks", "✅ Filtered", "🔥 Top Trades"])

    with tab1:
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.dataframe(df_filtered, use_container_width=True)

    with tab3:
        st.dataframe(df_top, use_container_width=True)

    # ---------------- CHART ---------------- #
    st.subheader("📈 Stock Chart")

    if not df_top.empty:
        selected_ticker = st.selectbox(
            "Select stock",
            df_top['ticker']
        )

        chart = plot_stock_chart(selected_ticker)

        if chart:
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("No chart data")

    # ---------------- DOWNLOAD ---------------- #
    st.download_button(
        "⬇️ Download Top Trades",
        df_top.to_csv(index=False),
        "top_trades.csv"
    )
