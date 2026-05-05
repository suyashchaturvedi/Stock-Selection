import streamlit as st
import pandas as pd
import datetime
import yfinance as yf
from stock_selection_v1 import stock_status

st.set_page_config(layout="wide")
st.title("📊 Nifty 500 Trading Dashboard")

uploaded_file = st.file_uploader("Upload Nifty 500 CSV", type=["csv"])

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    if 'Symbol' not in df.columns:
        st.error("CSV must contain 'Symbol' column")
        st.stop()

    df['Ticker'] = df['Symbol'].astype(str).str.strip() + ".NS"
    tickers = df['Ticker'].dropna().tolist()

    st.success(f"Loaded {len(tickers)} stocks")

    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date.today()

    if st.button("🚀 Run Dashboard"):

        with st.spinner("Running screener..."):

            result = stock_status(tickers, start_date, end_date)

        # 🔥 DEBUG: show how many worked
        st.write(f"Stocks processed successfully: {len(result)}")

        if not result:
            st.error("No results generated. Likely Yahoo API/network issue.")
            st.stop()

        df_res = pd.DataFrame.from_dict(result, orient='index')

        # Clean CMP
        df_res['cmp'] = pd.to_numeric(df_res['cmp'], errors='coerce').round(2)

        # Score
        score_cols = ['AboveSMA9', 'MACD', 'ma_20_50_cross']
        df_res['Score'] = df_res[score_cols].sum(axis=1)

        df_res = df_res.sort_values(by='Score', ascending=False)

        st.success("Dashboard Ready")

        st.subheader("🏆 Top 10 Stocks")
        st.dataframe(df_res.head(10), use_container_width=True)

        # Chart
        st.subheader("📈 Stock Chart")
        selected = st.selectbox("Select stock", df_res['ticker'])

        if selected:
            chart = yf.download(selected, period="6mo")
            if not chart.empty:
                st.line_chart(chart['Close'])

        # Download
        csv = df_res.to_csv(index=False).encode('utf-8')

        st.download_button(
            "Download Results",
            csv,
            "results.csv",
            "text/csv"
        )

        with st.expander("View Full Data"):
            st.dataframe(df_res, use_container_width=True)
