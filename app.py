import streamlit as st
import pandas as pd
import datetime
from stock_selection_v1 import stock_status

st.set_page_config(layout="wide")
st.title("📈 Nifty 500 Screener")

# Upload CSV
uploaded_file = st.file_uploader("Upload Nifty 500 CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Convert symbols to Yahoo Finance format
    tickers = df['Symbol'].dropna().apply(lambda x: f"{x}.NS").tolist()

    st.success(f"Loaded {len(tickers)} stocks ✅")
    st.write("Sample tickers:", tickers[:5])

    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date.today()

    if st.button("🚀 Run Screener"):

        results = {}
        progress = st.progress(0)

        for i, tick in enumerate(tickers):
            try:
                res = stock_status([tick], start_date, end_date)

                if res:
                    results.update(res)

            except Exception as e:
                continue

            progress.progress((i + 1) / len(tickers))

        if len(results) == 0:
            st.error("No results generated. Check ticker format or data availability.")
        else:
            df_res = pd.DataFrame(results).T

            # Add score
            score_cols = ['AboveSMA9', 'SuperTrend', 'MACD', 'ma_20_50_cross']
            df_res['Score'] = df_res[score_cols].sum(axis=1)

            df_res = df_res.sort_values(by='Score', ascending=False)

            st.success("Analysis Complete ✅")

            st.subheader("🏆 Top 20 Stocks")
            st.dataframe(df_res.head(20), use_container_width=True)

            with st.expander("View all results"):
                st.dataframe(df_res, use_container_width=True)
