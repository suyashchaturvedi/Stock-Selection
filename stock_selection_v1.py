import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

def current_candle(df):
  HighCurr = round(df.High.iloc[-1], 2)
  LowCurr = round(df.Low.iloc[-1], 2)
  CloseCurr = round(df.Close.iloc[-1], 2)
  OpenCurr = round(df.Open.iloc[-1], 2)

  return OpenCurr, HighCurr, LowCurr, CloseCurr

def prev_month_candle(df):
  df2 = df.reset_index()
  curr_date = df2.Date.iloc[-1]
  curr_month = curr_date.month
  if curr_month == 1:
    prev_month = 12
  else:
    prev_month = curr_month - 1

  masked_month = df2['Date'].map(lambda x: x.month) == prev_month
  prev_month_df = df2[masked_month]

  high = round(max(prev_month_df.High.values).item(), 2)
  low = round(min(prev_month_df.Low.values).item(), 2)
  close = round(prev_month_df.Close.iloc[-1].item(), 2)

  # print("Prev_High", high)
  # print("Prev_Low", low)
  # print("Prev_Close", close)

  return high, low, close

def fibo_levels(df):
  HIGHprev, LOWprev, CLOSEprev = prev_month_candle(df)
  PP = round((HIGHprev + LOWprev + CLOSEprev) / 3, 2)
  R1 = round(PP + 0.382 * (HIGHprev - LOWprev), 2)
  S1 = round(PP - 0.382 * (HIGHprev - LOWprev), 2)
  R2 = round(PP + 0.618 * (HIGHprev - LOWprev), 2)
  S2 = round(PP - 0.618 * (HIGHprev - LOWprev), 2)
  R3 = round(PP + (HIGHprev - LOWprev), 2)
  S3 = round(PP - (HIGHprev - LOWprev), 2)

  # print("Pivot_Point", PP)
  # print("R3", R3)
  # print("R2", R2)
  # print("R1", R1)
  # print("S1", S1)
  # print("S2", S2)
  # print("S3", S3)

  return S1, S2, S3, PP, R1, R2, R3

def sma(df, period):
  sma = df.Close.rolling(period).mean().values

  return sma

def ema(df, period, column='Close', alpha=False):

    con = pd.concat([df[column][:period].rolling(window=period).mean(), df[column][period:]])

    if (alpha == True):
        # (1 - alpha) * previous_val + alpha * current_val where alpha = 1 / period
        a = con.ewm(alpha=1 / period, adjust=False).mean()
    else:
        # ((current_val - previous_val) * coeff) + previous_val where coeff = 2 / (period + 1)
        a = con.ewm(span=period, adjust=False).mean()

    return a.values

def atr_(df, period=20):
  df1 = pd.DataFrame()
  atr = 'ATR_' + str(period)

  if not 'TR' in df1.columns:
      df1['h-l'] = df.High - df.Low
      df1['h-yc'] = abs(df.High - df['Close'].shift(1))
      df1['l-yc'] = abs(df.Low - df['Close'].shift(1))

      df1['TR'] = df1[['h-l', 'h-yc', 'l-yc']].max(axis=1)

      df1.drop(['h-l', 'h-yc', 'l-yc'], inplace=True, axis=1)

  df1[atr]=ema(df1, period, column='TR', alpha=True)

  return df1

def ATR(DF,n=20):
    "function to calculate True Range and Average True Range"
    df = DF.copy()
    #print(df)
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df2 = df.drop(['H-L','H-PC','L-PC'],axis=1)
    s_array = df2['ATR'].to_numpy()
    return s_array

def MACD(df, fast_length=12, slow_length=26, signal_length=9):
  fast_ema = df.Close.ewm(span=fast_length, adjust=False).mean()
  slow_ema = df.Close.ewm(span=slow_length, adjust=False).mean()
  macd = fast_ema - slow_ema
  signal = macd.ewm(span=signal_length, adjust=False).mean()

  return macd.values, signal.values

def prev_day_candle(df):
  open_prev = round(df.Open.iloc[-2], 2)
  high_prev = round(df.High.iloc[-2], 2)
  low_prev = round(df.Low.iloc[-2], 2)
  close_prev = round(df.Close.iloc[-2], 2)

  return open_prev, high_prev, low_prev, close_prev

def check_bullish_ingulfing(df):
  op, hp, lp, cp = prev_day_candle(df)
  oc, hc, lc, cc = current_candle(df)
  #(op.values, hp, lp, cp)
  #print(oc, hc, lc, cc)
  if op.values > cp.values and oc.values < cc.values:
    if oc.values <= cp.values and cc.values > op.values:
      return True
    else:
      return False
  else:
    return False
  
def check_bearish_ingulfing(df):
  op, hp, lp, cp = prev_day_candle(df)
  oc, hc, lc, cc = current_candle(df)

  if op.values < cp.values and oc.values > cc.values:
    if oc.values >= cp.values and cc.values < op.values:
      return True
    else:
      return False
  else:
    return False
  
def SuperTrend(df, period, multiplier, ohlc=['Open', 'High', 'Low', 'Close']):

  df1=atr_(df, period)
  atr = 'ATR_' + str(period)
  st = 'ST_' + str(period) + '_' + str(multiplier)
  stx = 'STX_' + str(period) + '_' + str(multiplier)

  # Compute basic upper and lower bands
  df1['basic_ub'] = ((df.High + df.Low) / 2).squeeze() + multiplier * df1[atr].fillna(0)
  df1['basic_lb'] = ((df.High + df.Low) / 2).squeeze() - multiplier * df1[atr].fillna(0)

  # Compute final upper and lower bands
  df1['final_ub'] = 0.00
  df1['final_lb'] = 0.00
  for i in range(period, len(df)):
    df1.loc[df1.index[i], 'final_ub'] = df1['basic_ub'].iat[i] if df1['basic_ub'].iat[i] < df1['final_ub'].iat[i - 1] or df[ohlc[3]].iloc[i - 1, 0] > df1['final_ub'].iat[i - 1] else df1['final_ub'].iat[i - 1]
    df1.loc[df1.index[i], 'final_lb'] = df1['basic_lb'].iat[i] if df1['basic_lb'].iat[i] > df1['final_lb'].iat[i - 1] or df[ohlc[3]].iloc[i - 1, 0] < df1['final_lb'].iat[i - 1] else df1['final_lb'].iat[i - 1]
  # Set the Supertrend value
  df1[st] = 0.00
  for i in range(period, len(df)):
      df1.loc[df1.index[i], st] = df1['final_ub'].iat[i] if df1[st].iat[i - 1] == df1['final_ub'].iat[i - 1] and df[ohlc[3]].iloc[i, 0] <= df1['final_ub'].iat[i] else \
                           df1['final_lb'].iat[i] if df1[st].iat[i - 1] == df1['final_ub'].iat[i - 1] and df[ohlc[3]].iloc[i, 0] >  df1['final_ub'].iat[i] else \
                           df1['final_lb'].iat[i] if df1[st].iat[i - 1] == df1['final_lb'].iat[i - 1] and df[ohlc[3]].iloc[i, 0] >= df1['final_lb'].iat[i] else \
                           df1['final_ub'].iat[i] if df1[st].iat[i - 1] == df1['final_lb'].iat[i - 1] and df[ohlc[3]].iloc[i, 0] <  df1['final_lb'].iat[i] else 0.00
  # Mark the trend direction up/down
  df1[stx] = np.where((df1[st] > 0.00), np.where((df[ohlc[3]].squeeze() < df1[st]), 'down',  'up'), "")

  # Remove basic and final bands from the columns
  df1.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)
  return df1

def check_morning_star(df):
  op, hp, lp, cp = prev_day_candle(df)
  oc, hc, lc, cc = current_candle(df)
  opp, hpp, lpp, cpp = df.iloc[-3].Open, df.iloc[-3].High, df.iloc[-3].Low, df.iloc[-3].Close
  volume = df.iloc[-5:].Volume.values

  if opp.values > cpp.values and oc.values < cc.values:
    dogi = abs(op-cp)
    recent_volume = volume[-1]
    body_of_current_candle = abs(oc-cc)
    body_of_pp_candle = abs(opp-cpp)

    opp_pct = (opp - cpp) / opp
    if opp_pct.values >= 0.02:

      if min(op.values,cp.values) < max(opp.values, cc.values):

        if body_of_current_candle.values >= 0.7 * body_of_pp_candle.values:

          if dogi.values <= 0.1*body_of_current_candle.values:

            return True

        else:
          return False

      else:
        return False

    else:
      return False

  else:
    return False

def check_evening_star(df):
  op, hp, lp, cp = prev_day_candle(df)
  oc, hc, lc, cc = current_candle(df)
  opp, hpp, lpp, cpp = df.iloc[-3].Open, df.iloc[-3].High, df.iloc[-3].Low, df.iloc[-3].Close
  volume = df.iloc[-5:].Volume.values

  if opp.values < cpp.values and oc.values > cc.values:
    dogi = abs(op-cp)
    recent_volume = volume[-1]
    body_of_current_candle = abs(oc-cc)
    body_of_pp_candle = abs(opp-cpp)

    cpp_pct = (cpp - opp) / opp
    if cpp_pct.values >= 0.02:

      if min(op.values, cp.values) < max(cpp.values, oc.values):

        if body_of_current_candle.values >= 0.8 * body_of_pp_candle.values:

          if recent_volume == max(volume) and dogi.values <= 0.1*body_of_current_candle.values:
            return True

          else:
            return False

        else:
          return False

      else:
        return False

    else:
      return False

  else:
    return False
  
def RSI(df, rsi_period):
  delta = df.Close.diff()
  gain = delta.mask(delta < 0, 0)
  loss = delta.mask(delta > 0, 0)
  avg_gain = gain.ewm(com=rsi_period-1, min_periods=rsi_period).mean()
  avg_loss = loss.ewm(com=rsi_period-1, min_periods=rsi_period).mean()
  rs = abs(avg_gain / avg_loss)
  rsi = 100 - (100/(1+rs))

  return rsi.values


#Main function to run all the analysis and the functions for ranking of stocks based on technical analysis
def stock_status(tickers, st, end):
  status = {}
  c = 0
  for tick in tickers:
    """     try: """
    df3 = yf.download(tick, start=st, end=end,auto_adjust=True)
    """     except:
          continue """

    """     try: """
    oc, hc, lc, cc = current_candle(df3)
    hp, lp, cp = prev_month_candle(df3)
    s1,s2,s3,pp,r1,r2,r3 = fibo_levels(df3)
    """     except:
          continue """

    status[c] = {'ticker':tick}
    status[c]['cmp'] = round(cc, 2)
    sma_9 = sma(df3, 9)
    sma_20 = sma(df3,20)
    atr=ATR(df3)
    macd, signal = MACD(df3, fast_length=12, slow_length=26, signal_length=9)

    if cc.values > sma_9[-1]:
      status[c]['AboveSMA9'] = 1
    else:
      status[c]['AboveSMA9'] = -1

    if check_bullish_ingulfing(df3):
      status[c]['BullishIngulfing'] = 1
    else:
      status[c]['BullishIngulfing'] = 0

    if check_bearish_ingulfing(df3):
      status[c]['BearshIngulfing'] = -1
    else:
      status[c]['BearshIngulfing'] = 0

    if SuperTrend(df3,10,3)['STX_10_3'].iloc[-1] == 'up':
      status[c]['SuperTrend'] = 1
    else:
      status[c]['SuperTrend'] = -1

    if (sma(df3,20)[-1] - sma(df3,50)[-1]) > 0:
      status[c]['ma_20_50_cross'] = 1
    else:
      status[c]['ma_20_50_cross'] = -1

    if (macd[-1] - signal[-1]) > 0:
      status[c]['MACD'] = 1
    else:
      status[c]['MACD'] = -1

    if RSI(df3,11)[-1] >= 60:
      status[c]['RSI_Above_60'] = 1
    elif RSI(df3,11)[-1] >= 42 and RSI(df3,11)[-1] < 60:
      status[c]['RSI_Above_60'] = 0
      status[c]['RSI_Below_42'] = 0
    else:
      status[c]['RSI_Below_42'] = -1

    if check_morning_star(df3):
      status[c]['Morning_Star'] = 1
    else:
      status[c]['Morning_Star'] = 0

    if check_evening_star(df3):
      status[c]['Evening_Star'] = -1
    else:
      status[c]['Evening_Star'] = 0

    if cc.values > pp:
      if cc.values < r1:
        status[c]['status'] = 'pivot point={}, break_out, R1={}'.format(pp,r1)
        status[c]['Target']=r1
        status[c]['SSL']=pp
      elif cc.values < r2:
        status[c]['status'] = 'R1={}, break_out, R2={}'.format(r1,r2)
        status[c]['Target']=r2
        status[c]['SSL']=r1
      elif cc.values < r3:
        status[c]['status'] = 'R2={}, break_out, R3={}'.format(r2,r3)
        status[c]['Target']=r3
        status[c]['SSL']=r2
      else:
        status[c]['status'] = 'Break_up all the resistances'
        status[c]['Target']='7%'
        status[c]['SSL']=r3

    elif cc.values < pp:
      if cc.values > s1:
        status[c]['status'] = 'pivot point={}, break_down, s1={}'.format(pp, s1)
      elif cc.values > s2:
        status[c]['status'] = 'S1={}, break_down, s2={}'.format(s1,s2)
      elif cc.values > s3:
        status[c]['status'] = 'S2={}, break_down, s3={}'.format(s2,s3)
      else:
        status[c]['status'] = 'Break_down all the resistances'

    status[c]['MA'] = sma_20[-1]
    status[c]['ATR'] = atr[-1]
    c += 1

  return status