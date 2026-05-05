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
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()

    # Validate CSV
    if 'Symbol' not in df.columns:
        st.error("CSV must contain 'Symbol' column")
        st.stop()

    # Prepare tickers
    df['Ticker'] = df['Symbol'].astype(str).str.strip() + ".NS"
    tickers = df['Ticker'].dropna().tolist()

    st.success(f"Loaded {len(tickers)} stocks ✅")
    st.write("Sample tickers:", tickers[:5])

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        min_score = st.slider("Minimum Score", -4, 4, 1)

    with col2:
        if 'Industry' in df.columns:
            industry = st.selectbox(
                "Industry Filter",
                ["All"] + sorted(df['Industry'].dropna().unique())
            )
        else:
            industry = "All"

    # Dates
    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date.today()

    if st.button("🚀 Run Dashboard"):

        results_list = []
        progress = st.progress(0)

        for i, tick in enumerate(tickers):
            try:
                res = stock_status([tick], start_date, end_date)

                if isinstance(res, dict) and len(res) > 0:
                    for _, val in res.items():
                        if isinstance(val, dict):
                            results_list.append(val)

            except Exception as e:
                st.write(f"Error in {tick}: {e}")
                continue

            progress.progress((i + 1) / len(tickers))

        # 🚨 No results case
        if not results_list:
            st.error("No results generated. Check logs above.")
            st.stop()

        df_res = pd.DataFrame(results_list)

        # Ensure required columns
        if 'ticker' not in df_res.columns:
            st.error("Missing 'ticker' column from output")
            st.stop()

        if 'cmp' not in df_res.columns:
            st.error("Missing 'cmp' column from output")
            st.stop()

        # Clean CMP
        df_res['cmp'] = pd.to_numeric(df_res['cmp'], errors='coerce')
        df_res['cmp'] = df_res['cmp'].fillna(0).round(2)

        # Merge Industry
        if 'Industry' in df.columns:
            df_res = df_res.merge(
                df[['Ticker', 'Industry']],
                left_on='ticker',
                right_on='Ticker',
                how='left'
            )
            df_res.drop(columns=['Ticker'], inplace=True)

        # Score calculation
        score_cols = ['AboveSMA9', 'SuperTrend', 'MACD', 'ma_20_50_cross']
        available_cols = [col for col in score_cols if col in df_res.columns]

        if available_cols:
            df_res['Score'] = df_res[available_cols].sum(axis=1)
        else:
            df_res['Score'] = 0

        # Apply filters
        df_res = df_res[df_res['Score'] >= min_score]

        if industry != "All":
            df_res = df_res[df_res['Industry'] == industry]

        # Sort
        df_res = df_res.sort_values(by='Score', ascending=False)

        # Clean column order
        cols = ['ticker', 'cmp', 'Score'] + [
            c for c in df_res.columns if c not in ['ticker', 'cmp', 'Score']
        ]
        df_res = df_res[cols]

        st.success("Dashboard Ready ✅")

        # 🏆 Top Picks
        st.subheader("🏆 Top 10 Stocks")
        st.dataframe(df_res.head(10), use_container_width=True)

        # 📈 Chart
        st.subheader("📈 Stock Chart")

        selected_stock = st.selectbox(
            "Select stock",
            df_res['ticker'].dropna().unique()
        )

        if selected_stock:
            try:
                chart_data = yf.download(selected_stock, start=start_date, end=end_date)
                if not chart_data.empty:
                    st.line_chart(chart_data['Close'])
                else:
                    st.warning("No chart data available")
            except Exception as e:
                st.warning(f"Chart failed: {e}")

        # 📥 Download
        st.subheader("📥 Download Results")

        csv = df_res.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="Download Full Results",
            data=csv,
            file_name="stock_screener_results.csv",
            mime="text/csv"
        )

        # 📋 Full Data
        with st.expander("View Full Data"):
            st.dataframe(df_res, use_container_width=True)
