import numpy as np
import pandas as pd
import yfinance as yf

# ===================== BASIC CANDLE FUNCTIONS =====================

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

# ===================== TECHNICAL INDICATORS =====================

def sma(df, period):
    return df['Close'].rolling(period).mean().values

def ema(df, period):
    return df['Close'].ewm(span=period, adjust=False).mean().values

def ATR(df, n=20):
    df = df.copy()
    df['H-L'] = abs(df['High'] - df['Low'])
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(n).mean()
    return df['ATR'].values

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

# ===================== PATTERN CHECKS =====================

def bullish_engulfing(df):
    op, _, _, cp = prev_day_candle(df)
    oc, _, _, cc = current_candle(df)
    return (op > cp) and (oc < cc) and (oc <= cp) and (cc > op)

def bearish_engulfing(df):
    op, _, _, cp = prev_day_candle(df)
    oc, _, _, cc = current_candle(df)
    return (op < cp) and (oc > cc) and (oc >= cp) and (cc < op)

# ===================== SUPER TREND =====================

def supertrend(df, period=10, multiplier=3):
    hl2 = (df['High'] + df['Low']) / 2
    atr = pd.Series(ATR(df, period))
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    st = pd.Series(index=df.index, dtype=float)
    trend = pd.Series(index=df.index, dtype=str)

    for i in range(period, len(df)):
        if df['Close'].iloc[i] > upperband.iloc[i-1]:
            trend.iloc[i] = 'up'
        elif df['Close'].iloc[i] < lowerband.iloc[i-1]:
            trend.iloc[i] = 'down'
        else:
            trend.iloc[i] = trend.iloc[i-1]

        st.iloc[i] = lowerband.iloc[i] if trend.iloc[i] == 'up' else upperband.iloc[i]

    return trend

# ===================== MAIN FUNCTION =====================

def stock_status(tickers, start, end):

    status = {}
    c = 0

    for tick in tickers:
        try:
            df = yf.download(tick, start=start, end=end, progress=False)

            # 🚨 critical filter
            if df is None or df.empty or len(df) < 50:
                continue

            oc, hc, lc, cc = current_candle(df)

            sma9 = sma(df, 9)
            sma20 = sma(df, 20)
            sma50 = sma(df, 50)

            macd, signal = MACD(df)
            rsi = RSI(df)

            trend = supertrend(df)

            status[c] = {
                'ticker': tick,
                'cmp': round(float(cc), 2)
            }

            status[c]['AboveSMA9'] = 1 if cc > sma9[-1] else -1
            status[c]['SuperTrend'] = 1 if trend.iloc[-1] == 'up' else -1
            status[c]['MACD'] = 1 if (macd[-1] > signal[-1]) else -1
            status[c]['ma_20_50_cross'] = 1 if sma20[-1] > sma50[-1] else -1

            if rsi[-1] >= 60:
                status[c]['RSI'] = 1
            elif rsi[-1] <= 42:
                status[c]['RSI'] = -1
            else:
                status[c]['RSI'] = 0

            status[c]['Bullish'] = 1 if bullish_engulfing(df) else 0
            status[c]['Bearish'] = -1 if bearish_engulfing(df) else 0

            c += 1

        except Exception:
            continue

    return status
