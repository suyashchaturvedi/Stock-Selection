
import streamlit as st
import pandas as pd

st.title("Daily Stock Picks")
df=pd.read_csv(r"latest_picks.csv")
st.subheader("Today's Stock Picks")
st.table(df)
st.caption("Updated automatically at 9:15 AM every day")
