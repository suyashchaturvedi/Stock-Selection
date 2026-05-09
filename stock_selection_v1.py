import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import time

REQUIRED_COLS = ['Open', 'High', 'Low', 'Close']


# ---------------- DOWNLOAD ---------------- #

def download_batch(tickers, start, end, retries=2):
    for attempt in range(retries):
        try:
            return yf.download(
                tickers,
                start=start,
                end=end,
                group_by='ticker',
                auto_adjust=True,
                threads=True,
                progress=False
            )
        except Exception as e:
            print(f"Batch download failed ({attempt+1}): {e}")
            time.sleep(1)
    return None


def download_single(ticker, start, end):
    try:
        return yf.download(
            ticker,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False
        )
    except:
        return None


# ---------------- NORMALIZE ---------------- #

def normalize_yf_data(data, tickers):
    if data is None or data.empty:
        return {}

    if isinstance(data.columns, pd.MultiIndex):
        if 'Close' in data.columns.get_level_values(0):
            data = data.swaplevel(axis=1)

        out = {}
        for t in tickers:
            if t in data.columns.get_level_values(0):
                df = data[t].copy()
                df.columns = [c.capitalize() for c in df.columns]
                out[t] = df
        return out

    return {tickers[0]: data}


# ---------------- INDICATORS ---------------- #

def compute_indicators(df):
    close = df['Close']

    sma9 = close.rolling(9).mean()
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(com=10).mean()
    avg_loss = loss.ewm(com=10).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return sma9, sma20, sma50, macd, signal, rsi


# ---------------- PATTERNS ---------------- #

def bullish_engulfing(df):
    if len(df) < 2:
        return 0
    prev, curr = df.iloc[-2], df.iloc[-1]
    return int(
        (prev['Open'] > prev['Close']) and
        (curr['Open'] < curr['Close']) and
        (curr['Open'] <= prev['Close']) and
        (curr['Close'] > prev['Open'])
    )


def bearish_engulfing(df):
    if len(df) < 2:
        return 0
    prev, curr = df.iloc[-2], df.iloc[-1]
    return int(
        (prev['Open'] < prev['Close']) and
        (curr['Open'] > curr['Close']) and
        (curr['Open'] >= prev['Close']) and
        (curr['Close'] < prev['Open'])
    )


# ---------------- PIVOTS ---------------- #

def compute_pivots(df):
    df2 = df.reset_index()

    curr_month = df2['Date'].iloc[-1].month
    prev_month = 12 if curr_month == 1 else curr_month - 1

    prev_df = df2[df2['Date'].dt.month == prev_month]

    if prev_df.empty:
        return None

    high = prev_df['High'].max()
    low = prev_df['Low'].min()
    close = prev_df['Close'].iloc[-1]

    pp = (high + low + close) / 3

    r1 = pp + 0.382 * (high - low)
    r2 = pp + 0.618 * (high - low)
    r3 = pp + (high - low)

    s1 = pp - 0.382 * (high - low)
    s2 = pp - 0.618 * (high - low)
    s3 = pp - (high - low)

    return pp, r1, r2, r3, s1, s2, s3


# ---------------- MAIN ENGINE ---------------- #

def stock_status(tickers, start, end):

    results = []
    failed = []

    data_raw = download_batch(tickers, start, end)
    data = normalize_yf_data(data_raw, tickers)

    for tick in tickers:
        try:
            df = data.get(tick)

            if df is None or df.empty:
                df = download_single(tick, start, end)

            if df is None or df.empty:
                failed.append(tick)
                continue

            df.columns = [c.capitalize() for c in df.columns]

            if not all(col in df.columns for col in REQUIRED_COLS):
                failed.append(tick)
                continue

            df = df.dropna()

            if len(df) < 50:
                failed.append(tick)
                continue

            sma9, sma20, sma50, macd, signal, rsi = compute_indicators(df)

            close_price = float(df['Close'].iloc[-1])

            sma9_last = sma9.iloc[-1]
            sma20_last = sma20.iloc[-1]
            sma50_last = sma50.iloc[-1]
            macd_last = macd.iloc[-1]
            signal_last = signal.iloc[-1]
            rsi_last = rsi.iloc[-1]

            if pd.isna([sma9_last, sma20_last, sma50_last, macd_last, signal_last, rsi_last]).any():
                failed.append(tick)
                continue

            pivots = compute_pivots(df)
            if pivots is None:
                failed.append(tick)
                continue

            pp, r1, r2, r3, s1, s2, s3 = pivots
            cc = close_price

            # -------- TARGET + SL -------- #
            if cc > pp:
                if cc < r1:
                    target, ssl = r1, pp
                elif cc < r2:
                    target, ssl = r2, r1
                elif cc < r3:
                    target, ssl = r3, r2
                else:
                    target, ssl = cc * 1.07, r3
            else:
                if cc > s1:
                    target, ssl = s1, pp
                elif cc > s2:
                    target, ssl = s2, s1
                elif cc > s3:
                    target, ssl = s3, s2
                else:
                    target, ssl = cc * 0.93, s3

            row = {
                "ticker": tick,
                "cmp": round(cc, 2),

                "Above_SMA9": 1 if cc > sma9_last else -1,
                "MA_Cross": 1 if sma20_last > sma50_last else -1,
                "MACD": 1 if macd_last > signal_last else -1,
                "RSI": round(rsi_last, 2),

                "Bullish": bullish_engulfing(df),
                "Bearish": -bearish_engulfing(df),

                "Target": round(target, 2),
                "SSL": round(ssl, 2),
            }

            # Score
            row["Score"] = (
                row["Above_SMA9"] +
                row["MA_Cross"] +
                row["MACD"] +
                (1 if row["RSI"] > 60 else -1 if row["RSI"] < 40 else 0) +
                row["Bullish"] +
                row["Bearish"]
            )

            results.append(row)

        except Exception as e:
            print(f"Error processing {tick}: {e}")
            failed.append(tick)

    df_final = pd.DataFrame(results)

    if not df_final.empty:
        df_final = df_final.copy()

        df_final.loc[:, 'Target %'] = ((df_final['Target'] / df_final['cmp']) * 100 - 100).round()
        df_final.loc[:, 'Final SL'] = ((df_final['SSL'] + df_final['cmp']) / 2).round()
        df_final.loc[:, 'SL %'] = (100 - (df_final['Final SL'] / df_final['cmp']) * 100).round()

        df_final.loc[:, 'RR'] = (
            (df_final['Target'] - df_final['cmp']) /
            (df_final['cmp'] - df_final['Final SL'])
        ).round(2)

        df_final = df_final.sort_values(by="Score", ascending=False).reset_index(drop=True)

    print(f"\nProcessed: {len(results)} | Failed: {len(failed)}")

    return df_final


# ---------------- WRAPPER ---------------- #

def run_stock_selection(tickers):
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365)
    return stock_status(tickers, start, end)
