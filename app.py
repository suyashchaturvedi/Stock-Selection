import streamlit as st
import pandas as pd
import datetime
from stock_selection_v1 import stock_status

st.title("📈 Nifty 500 Screener")

uploaded_file = st.file_uploader("Upload Nifty 500 CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Convert to Yahoo Finance format
    tickers = df['Symbol'].dropna().apply(lambda x: f"{x}.NS").tolist()

    st.write(f"Loaded {len(tickers)} stocks ✅")

    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date.today()

    if st.button("🚀 Run Screener"):
        result = stock_status(tickers, start_date, end_date)

        df_res = pd.DataFrame(result).T

        score_cols = ['AboveSMA9','SuperTrend','MACD','ma_20_50_cross']
        df_res['Score'] = df_res[score_cols].sum(axis=1)

        df_res = df_res.sort_values(by='Score', ascending=False)

        st.subheader("🏆 Top 20 Stocks")
        st.dataframe(df_res.head(20))

        with st.expander("View all"):
            st.dataframe(df_res)
