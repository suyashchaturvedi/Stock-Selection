import numpy as np
import pandas as pd
import yfinance as yf

# ================= BASIC FUNCTIONS =================

def current_candle(df):
    return (
        float(df['Open'].iloc[-1]),
        float(df['High'].iloc[-1]),
        float(df['Low'].iloc[-1]),
        float(df['Close'].iloc[-1])
    )

def prev_day_candle(df):
    return (
        float(df['Open'].iloc[-2]),
        float(df['High'].iloc[-2]),
        float(df['Low'].iloc[-2]),
        float(df['Close'].iloc[-2])
    )

# ================= INDICATORS =================

def sma(df, period):
    return df['Close'].rolling(period).mean().values

def MACD(df):
    fast = df['Close'].ewm(span=12, adjust=False).mean()
    slow = df['Close'].ewm(span=26, adjust=False).mean()
    macd = fast - slow
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd.values, signal.values

def RSI(df, period=11):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period-1).mean()
    avg_loss = loss.ewm(com=period-1).mean()
    rs = avg_gain / avg_loss
    return (100 - (100 / (1 + rs))).values

# ================= PATTERNS =================

def bullish_engulfing(df):
    op, _, _, cp = prev_day_candle(df)
    oc, _, _, cc = current_candle(df)
    return (op > cp) and (oc < cc) and (oc <= cp) and (cc > op)

def bearish_engulfing(df):
    op, _, _, cp = prev_day_candle(df)
    oc, _, _, cc = current_candle(df)
    return (op < cp) and (oc > cc) and (oc >= cp) and (cc < op)

# ================= MAIN FUNCTION =================

def stock_status(tickers, start, end):

    status = {}
    c = 0

    for tick in tickers:
        try:
            # 🔥 FIXED DOWNLOAD (reliable)
            df = yf.download(
                tick,
                period="6mo",
                interval="1d",
                progress=False,
                auto_adjust=True,
                threads=False
            )

            # 🔥 FIXED FILTER
            if df is None or df.empty:
                continue

            oc, hc, lc, cc = current_candle(df)

            sma9 = sma(df, 9)
            sma20 = sma(df, 20)
            sma50 = sma(df, 50)

            macd, signal = MACD(df)
            rsi = RSI(df)

            status[c] = {
                'ticker': tick,
                'cmp': round(float(cc), 2),
                'AboveSMA9': 1 if cc > sma9[-1] else -1,
                'MACD': 1 if macd[-1] > signal[-1] else -1,
                'ma_20_50_cross': 1 if sma20[-1] > sma50[-1] else -1,
                'RSI': 1 if rsi[-1] >= 60 else (-1 if rsi[-1] <= 42 else 0),
                'Bullish': 1 if bullish_engulfing(df) else 0,
                'Bearish': -1 if bearish_engulfing(df) else 0
            }

            c += 1

        except Exception:
            continue

    return status
