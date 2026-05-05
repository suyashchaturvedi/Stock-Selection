import numpy as np
import pandas as pd
import yfinance as yf
import time

# ================= SAFE FETCH =================

def fetch_data(tick):
    try:
        df = yf.download(
            tick,
            period="3mo",
            interval="1d",
            progress=False,
            threads=False
        )

        if df is not None and not df.empty:
            return df

        # fallback method
        df = yf.Ticker(tick).history(period="3mo")

        if df is not None and not df.empty:
            return df

    except:
        return None

    return None

# ================= INDICATORS =================

def sma(df, n):
    return df['Close'].rolling(n).mean()

def MACD(df):
    fast = df['Close'].ewm(span=12).mean()
    slow = df['Close'].ewm(span=26).mean()
    macd = fast - slow
    signal = macd.ewm(span=9).mean()
    return macd, signal

# ================= MAIN =================

def stock_status(tickers, start=None, end=None):

    results = []

    for i, tick in enumerate(tickers):

        df = fetch_data(tick)

        if df is None or len(df) < 20:
            continue

        try:
            close = float(df['Close'].iloc[-1])

            sma9 = sma(df, 9)
            sma20 = sma(df, 20)

            macd, signal = MACD(df)

            results.append({
                "ticker": tick,
                "cmp": round(close, 2),
                "AboveSMA9": 1 if close > sma9.iloc[-1] else -1,
                "MACD": 1 if macd.iloc[-1] > signal.iloc[-1] else -1,
                "ma_20_50_cross": 1 if sma20.iloc[-1] > sma20.iloc[-5] else -1
            })

            # avoid rate limiting
            time.sleep(0.05)

        except:
            continue

    return pd.DataFrame(results)
