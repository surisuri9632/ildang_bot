import pyupbit
import time
import pandas as pd

access_key = 'HnXpKzTa0Tc6VECpUxFxfSZ70yHWWQwY8eW2MoJE'
secret_key = 'WCZ19YZktxLPga1msebnROZS781frzKl0QxnXiMr'
upbit = pyupbit.Upbit(access_key, secret_key)





'''
RSI 지표 수치를 구해준다.
ohlcv: 분봉/일봉 정보, period: 기간
inverval: 기준날짜,  -1: 현재, -2: 이전구간
'''
def GetRSI(ohlcv, period, inverval):
    ohlcv["close"] = ohlcv["close"]
    delta = ohlcv["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    _gain = up.ewm(com=(period - 1), min_periods = period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods = period).mean()

    RS = _gain / _loss
    return float(pd.Series(100 - (100 / (1 + RS)), name="RSI").iloc[inverval])



'''
이동평균선 수치를 구해줍니다.
ohlcv: 분봉/일봉정보
period: 기간
inverval: 기준날짜,  -1: 현재, -2: 이전구간
'''
def GetMA(ohlcv, period, interval):
    close = ohlcv["close"]
    ma = close.rolling(period).mean()
    return float(ma[interval])

# 비트코인 일봉 정보를 가져옵니다.
df = pyupbit.get_ohlcv("KRW-BTC", interval="minute240")


ma5_before = GetMA(df, 5, -2)
ma5_now = GetMA(df, 5, -1)

print(ma5_now, ma5_before)

