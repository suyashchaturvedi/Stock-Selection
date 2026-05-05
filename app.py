import streamlit as st
import pandas as pd
from stock_selection_v1 import stock_status

st.set_page_config(layout="wide")
st.title("📊 Nifty 500 Screener (Stable Version)")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    if "Symbol" not in df.columns:
        st.error("CSV must contain 'Symbol'")
        st.stop()

    tickers = df["Symbol"].dropna().astype(str).str.strip() + ".NS"

    st.write(f"Total stocks: {len(tickers)}")

    if st.button("🚀 Run Screener"):

        with st.spinner("Fetching data..."):

            result_df = stock_status(tickers)

        if result_df.empty:
            st.error("❌ No data fetched. This is due to Yahoo blocking requests.")
            st.stop()

        st.success(f"✅ Stocks processed: {len(result_df)}")

        # scoring
        result_df["Score"] = result_df[["AboveSMA9","MACD","ma_20_50_cross"]].sum(axis=1)

        result_df = result_df.sort_values("Score", ascending=False)

        st.subheader("🏆 Top 10 Picks")
        st.dataframe(result_df.head(10), use_container_width=True)

        st.subheader("📋 Full Results")
        st.dataframe(result_df, use_container_width=True)
