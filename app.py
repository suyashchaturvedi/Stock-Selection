import streamlit as st
import pandas as pd
import datetime
import yfinance as yf
from stock_selection_v1 import stock_status

st.set_page_config(layout="wide")
st.title("📊 Nifty 500 Trading Dashboard")

# Upload CSV
uploaded_file = st.file_uploader("Upload Nifty 500 CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if 'Symbol' not in df.columns:
        st.error("CSV must contain 'Symbol' column")
        st.stop()

    # Convert to Yahoo format
    df['Ticker'] = df['Symbol'].astype(str).str.strip() + ".NS"
    tickers = df['Ticker'].tolist()

    st.success(f"Loaded {len(tickers)} stocks ✅")

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        min_score = st.slider("Minimum Score", -4, 4, 1)

    with col2:
        if 'Industry' in df.columns:
            industry = st.selectbox("Industry Filter", ["All"] + sorted(df['Industry'].dropna().unique()))
        else:
            industry = "All"

    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date.today()

    if st.button("🚀 Run Dashboard"):

        results_list = []
        progress = st.progress(0)

        for i, tick in enumerate(tickers):
            try:
                res = stock_status([tick], start_date, end_date)

                if res:
                    for _, val in res.items():
                        results_list.append(val)

            except:
                continue

            progress.progress((i + 1) / len(tickers))

        if len(results_list) == 0:
            st.error("No results generated.")
            st.stop()

        df_res = pd.DataFrame(results_list)

        # Merge industry info
        df_res = df_res.merge(df[['Ticker', 'Industry']], left_on='ticker', right_on='Ticker', how='left')

        # Score
        score_cols = ['AboveSMA9', 'SuperTrend', 'MACD', 'ma_20_50_cross']
        score_cols = [col for col in score_cols if col in df_res.columns]

        if score_cols:
            df_res['Score'] = df_res[score_cols].sum(axis=1)

        # Apply filters
        df_res = df_res[df_res['Score'] >= min_score]

        if industry != "All":
            df_res = df_res[df_res['Industry'] == industry]

        df_res = df_res.sort_values(by='Score', ascending=False)

        st.success("Dashboard Ready ✅")

        # 🔥 Top Picks
        st.subheader("🏆 Top Picks")
        top_picks = df_res.head(10)
        st.dataframe(top_picks, use_container_width=True)

        # 📊 Select stock for chart
        st.subheader("📈 Stock Chart")

        selected_stock = st.selectbox("Select stock", df_res['ticker'].unique())

        if selected_stock:
            data = yf.download(selected_stock, start=start_date, end=end_date)

            st.line_chart(data['Close'])

        # 📥 Download button
        st.subheader("📥 Download Results")

        csv = df_res.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Download Full Results",
            data=csv,
            file_name="stock_screener_results.csv",
            mime="text/csv"
        )

        # 📋 Full table
        with st.expander("View Full Data"):
            st.dataframe(df_res, use_container_width=True)
