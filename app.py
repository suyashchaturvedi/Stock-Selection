import streamlit as st
import pandas as pd
import datetime
from stock_selection_v1 import stock_status

st.set_page_config(layout="wide")
st.title("📈 Nifty 500 Stock Screener")

# Upload CSV
uploaded_file = st.file_uploader("Upload Nifty 500 CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error("Error reading CSV file")
        st.stop()

    # Validate column
    if 'Symbol' not in df.columns:
        st.error("CSV must contain 'Symbol' column")
        st.stop()

    # Convert to Yahoo Finance format
    tickers = (
        df['Symbol']
        .dropna()
        .astype(str)
        .str.strip()
        .apply(lambda x: f"{x}.NS")
        .tolist()
    )

    st.success(f"Loaded {len(tickers)} stocks ✅")
    st.write("Sample tickers:", tickers[:5])

    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date.today()

    if st.button("🚀 Run Screener"):

        results_list = []
        progress = st.progress(0)

        for i, tick in enumerate(tickers):
            try:
                res = stock_status([tick], start_date, end_date)

                if res:
                    for _, val in res.items():
                        results_list.append(val)

            except Exception:
                continue

            progress.progress((i + 1) / len(tickers))

        if len(results_list) == 0:
            st.error("No results generated. Check ticker format or data availability.")
            st.stop()

        df_res = pd.DataFrame(results_list)

        # Add Score safely
        score_cols = ['AboveSMA9', 'SuperTrend', 'MACD', 'ma_20_50_cross']
        score_cols = [col for col in score_cols if col in df_res.columns]

        if score_cols:
            df_res['Score'] = df_res[score_cols].sum(axis=1)
            df_res = df_res.sort_values(by='Score', ascending=False)
        else:
            st.warning("Score columns not found")

        st.success("Analysis Complete ✅")

        st.subheader("🏆 Top 20 Stocks")
        st.dataframe(df_res.head(20), use_container_width=True)

        with st.expander("View Full Results"):
            st.dataframe(df_res, use_container_width=True)
