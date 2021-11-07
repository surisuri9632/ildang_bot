from numpy.lib.type_check import real
import pyupbit
import time
import pandas as pd

access_key = 'HnXpKzTa0Tc6VECpUxFxfSZ70yHWWQwY8eW2MoJE'
secret_key = 'WCZ19YZktxLPga1msebnROZS781frzKl0QxnXiMr'
upbit = pyupbit.Upbit(access_key, secret_key)


balances = upbit.get_balances()




'''
티커에 해당하는 코인의 수익율을 구해서 리턴하는 함수 입니다.
'''
def GetRevenueRate(balances, ticker):
    revenue_rate = 0.0
    for value in balances:
        realTicker = value['unit_currency'] + "-" + value['currency']
        if ticker == realTicker:
            time.sleep(0.05)
            currentPrice = pyupbit.get_current_price(realTicker)
            revenue_rate = (currentPrice - float(value['avg_buy_price'])) * 100.0 / float(value['avg_buy_price'])
    return revenue_rate

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

'''
거래대금이 많은 순으로 코인 리스트를 가져옵니다.
interval: 기준날짜,  -1: 현재, -2: 이전구간
top: 호출 개수
'''
def GetTopCoinList(interval, top):
    print("----- 거래대금 많은 순으로 코인 리스트를 가져옵니다. -----")
    dic_coin_money = dict()
    tickers = pyupbit.get_tickers("KRW")
    for ticker in tickers:
        try:
            df = pyupbit.get_ohlcv(ticker, interval)
            
            #거래 대금입니다. 100% 일치하지 않음.
            # 오놀의 거래대금과 전날의 거래대금을 더합니다.
            volume_money = (df['close'][-1] * df['volume'][-1]) + (df['close'][-2] * df['volume'][-2])
            dic_coin_money[ticker] = volume_money
            #print(ticker, volume_money)

            time.sleep(0.02)
        except Exception as e:
            print("코인리스트 가져오기 실패.:", e)
            return;

    dic_sorted_coin_money = sorted(dic_coin_money.items(), key=lambda x: x[1], reverse=True)

    coin_list = list()
    cnt = 0
    for coin_data in dic_sorted_coin_money:
        cnt += 1
        if cnt <= top:
            coin_list.append(coin_data[0])
        else:
            break
    print("----- 코인리스트 가져오기 완료되었습니다. -----")
    return coin_list
    
'''
해당 리스트 안에 해당 코인이 있는지 체크하는 함수
'''
def CheckCoinInList(coinList, ticker):
    inCoinOk = False
    for coinTicker in coinList:
        if coinTicker == ticker:
            inCoinOk = True
            break
    
    return inCoinOk


'''
코인을 이미 가지고 있는지 없는지를 체크하는 함수입니다.
가지고 있으면 True
없으면 False 를 반환합니다.
'''
def IsHasCoin(balnaces, ticker):
    hasCoin = False
    for value in balances:
        realTicker = value['unit_currency'] + "-" + value['currency']
        if ticker == realTicker:
            hasCoin = True
    return hasCoin



#dangerCoinList = []
#topCoinList = GetTopCoinList("day", 20)
tickers = pyupbit.get_tickers("KRW")
for ticker in tickers:
    try:
        # 거래량 많은 탑코인 리스트안의 코인이 아니면 스킵
        # 탑코인에 해당하는 코인은 이후 로직을 수행합니다
        '''
        if CheckCoinInList(topCoinList, ticker) == False:
            continue
        if CheckCoinInList(dangerCoinList, ticker) == True:
            continue
        '''

        df_60 = pyupbit.get_ohlcv(ticker, interval="minute60")
        rsi60_min_before = GetRSI(df_60, 14, -2)
        rsi60_min_current = GetRSI(df_60, 14, -1)

        revenue_rate = GetRevenueRate(balances, ticker)

        print(ticker, ", RSI: ", rsi60_min_before, " -> ", rsi60_min_current)

    except Exception as e:
        print("에러가 발생하였습니다.")

