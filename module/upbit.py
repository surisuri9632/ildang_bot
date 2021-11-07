import math
import time
import logging
import requests
import jwt
import uuid
import hashlib

from urllib.parse import urlencode
from decimal import Decimal

# Keys
access_key = 'HnXpKzTa0Tc6VECpUxFxfSZ70yHWWQwY8eW2MoJE'
secret_key = 'WCZ19YZktxLPga1msebnROZS781frzKl0QxnXiMr'
server_url = 'https://api.upbit.com'


"""
- Name: set_loglevel
- Desc: 로그레벨을 설정합니다.
- Input
    1) level: 로그레벨
        1. D(d): DEBUG
        2. E(e): ERROR
        3. 그외(기본): INFO
"""

def set_loglevel(level):
    try:
        # 로그레벨: DEBUG
        if level.upper() == "D":
            logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.DEBUG
            )
        # 로그레벨 : ERROR
        elif level.upper() == "E":
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.ERROR
            )
        # 로그레벨: INFO
        else:
            logging.basicConfig(
                format='[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]:%(message)s',
                datefmt='%Y/%m/%d %I:%M:%S %p',
                level=logging.INFO
            )

    except Exception:
        raise

"""
- Name: send_request
- Desc: Request 처리
- 요청 수를 초과하면 에러가 발생합니다.
- Input
    1) reqType: 요청 타입
    2) reqURl: 요청 URL
    3) reqParam: 요청 파라미터
    4) reqHeader: 요청 헤더
- Output
    1) response: 응답 데이터
"""
def send_request(reqType, reqUrl, reqParam, reqHeader):
    try:
        # 요청 가능 회수를 확보하기 위해 기다리는 시간(단위: 초)
        err_sleep_time = 1

        # 요청에 대한 응답을 받을 때까지 반복적으로 수행합니다.
        while True:
            # 요청 처리
            response = requests.request(reqType, reqUrl, params=reqParam, headers=reqHeader)

            # 요청 가능회수를 추출합니다.
            if 'Remaining-Req' in response.headers:
                header_info = response.headers['Remaining-Req']
                start_idx = header_info.find("sec=")
                end_idx = len(header_info)
                remain_sec = header_info[int(start_idx):int(end_idx)].replace('sec=', '')
            else:
                logging.error("헤더 정보 이상")
                logging.error(response.headers)
                break

            # 요청 가능회수가 4개 미만이면 요청 가능회수 확보를 위해 일정시간 대기합니다.
            if int(remain_sec) < 4:
                logging.debug("요청 가능회수 한도 도달! 남은횟수:" + str(remain_sec))
                time.sleep(err_sleep_time)
            
            # 정상 응답일 때 동작합니다
            if response.status_code == 200 or response.status_code == 201:
                break
            elif response.status_code == 429:
                logging.error("요청 가능회수 초과!:" + str(response.status_code))
                time.sleep(err_sleep_time)
                break
            # 그 외 오류
            else:
                logging.error("기타 에러:" + str(response.status_code))
                logging.error(response.status_code)
                break

            # 요청 가능회수 초과 에러 발생시에는 다시 요청
            logging.info("[restRequest] 요청 재처리중...")

        return response

    except Exception:
        raise

"""
- Name: get_items
- Desc: 전체 종목 리스트를 조회합니다.

- Input
    1) market: 대상 마켓(콤마 구분자: KRW, BTC, USDT)
    2) except_item: 제외 종목(콤마 구분자: BTC,ETH)
- Output
    1) 전체 리스트: 리스트
"""

def get_items(market, except_item):
    try:
        # 조회 결과 리턴용 배열
        rtn_list = []

        # 마켓 데이터
        markets = market.split(',')

        # 제외 데이터
        except_items = except_item.split(',')

        url = "https://api.upbit.com/v1/market/all"
        querystring = {"isDetails": "false"}
        response = send_request("GET", url, querystring, "")
        data = response.json()

        # 조회 마켓만 추출
        for data_for in data:
            for market_for in markets:
                if data_for['market'].split('-')[0] == market_for:
                    rtn_list.append(data_for)
        
        # 제외 종목 제거
        for rtnlist_for in rtn_list[:]:
            for exceptItemFor in except_items:
                for marketFor in markets:
                    if rtnlist_for['market'] == marketFor + '-' + exceptItemFor:
                        rtn_list.remove(rtnlist_for)

        return rtn_list


    except Exception:
        raise




"""
- Name: buycoin_mp
- Desc: 시장가로 매수합니다.
- Input
    1) target_item: 대상종목
    2) buy_amount: 매수금액
- Output
    1) rtn_data: 매수결과
"""

def buycoin_mp(target_item, buy_amount):
    try:
        query = {'market': target_item, 'side': 'bid', 'price': buy_amount, 'ord_type': 'price',}
        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {'access_key': access_key,'nonce': str(uuid.uuid4()),'query_hash': query_hash,'query_hash_alg': 'SHA512',}
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = send_request("POST", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()

        logging.info("")
        logging.info("----------------------------------------------")
        logging.info("시장가 매수 완료!")
        logging.info(rtn_data)
        logging.info("----------------------------------------------")

        return rtn_data
    except Exception:
        raise



"""
- Name: get_balance
- Desc: 잔고 조회하기
- Input
    1) target_item: 대상종목
- Output
    1) rtn_balance: 주문 가능 잔고
"""

def get_balance(target_item):
    try:

        # 주문 가능 잔고 리턴용
        rtn_balance = 0

        # 최대 재시도 횟수
        max_cnt = 0

        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
        }

        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        # 잔고가 조회 될 때까지 반복합니다
        while True:

            #조회 횟수 증가
            max_cnt = max_cnt + 1
            res = send_request("GET", server_url + "/v1/accounts", "", headers)
            my_asset = res.json()

            # 해당 종목에 대한 잔고를 조회합니다
            # 잔고는 마켓에 상관없이 전체 잔고가 조회됩니다

            for myasset_for in my_asset:
                if myasset_for['currency'] == target_item.split('-')[1]:
                    rtn_balance = myasset_for['balance']
                
            # 잔고가 0 이상일 때까지 반복합니다.
            # 잔고가 0 이상일때까지 반복
            if Decimal(str(rtn_balance)) > Decimal(str(0)):
                break

            # 최대 100회 반복합니다.
            if max_cnt > 100:
                break
            
            logging.info("[주문가능 잔고 리턴용] 요청 재처리중...")
        return rtn_balance
    except Exception:
        raise

"""
- Name: sellcoin_mp
- Desc: 시장가로 매도하기 입니다.
- Input
    1) target_item: 대상종목
- Output
    1) rtn_data: 매도 결과
"""

# 시장가 매도
def sellcoin_mp(target_item):
    try:
        # 잔고 조회
        cur_balance = get_balance(target_item)

        query = {
            'market': target_item,
            'side': 'ask',
            'volume': cur_balance,
            'ord_type': 'market',
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("POST", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        logging.info("")
        logging.info("----------------------------------------------")
        logging.info("시장가 매도 완료!")
        logging.info(rtn_data)
        logging.info("----------------------------------------------")
 
        return rtn_data

    except Exception:
        raise

"""
- Name: sellcoin_tg
- Desc: 지정가로 매도하기 입니다.
- Input
    1) target_item: 대상종목
    2) sell_price: 매도 희망 금액
- Output
    1) rtn_data: 매도 결과
"""
def sellcoin_tg(target_item, sell_price):
    try:
 
        # 잔고 조회
        cur_balance = get_balance(target_item)
 
        query = {
            'market': target_item,
            'side': 'ask',
            'volume': cur_balance,
            'price': sell_price,
            'ord_type': 'limit',
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("POST", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        logging.info("")
        logging.info("----------------------------------------------")
        logging.info("지정가 매도 설정 완료!")
        logging.info(rtn_data)
        logging.info("----------------------------------------------")
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

"""
- Name: get_hoga
- Desc: 호가 금액 계산하기 입니다.
- Input
    1) cur_price: 현재 가격 입니다.
- Output
    1) hoga_val: 호가 단위 입니다.
"""
def get_hoga(cur_price):
    try:
 
        # 호가 단위
        if Decimal(str(cur_price)) < 10:
            hoga_val = 0.01
        elif Decimal(str(cur_price)) < 100:
            hoga_val = 0.1
        elif Decimal(str(cur_price)) < 1000:
            hoga_val = 1
        elif Decimal(str(cur_price)) < 10000:
            hoga_val = 5
        elif Decimal(str(cur_price)) < 100000:
            hoga_val = 10
        elif Decimal(str(cur_price)) < 500000:
            hoga_val = 50
        elif Decimal(str(cur_price)) < 1000000:
            hoga_val = 100
        elif Decimal(str(cur_price)) < 2000000:
            hoga_val = 500
        else:
            hoga_val = 1000
 
        return hoga_val
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

"""
- Name: get_targetprice
- Desc: 호가 단위 금액 계산 하기 입니다.
- Input
    1) cal_type : H:호가로, R:비율로
    2) st_price : 기준가격
#   3) chg_val : 변화단위
- Output
    1) rtn_price : 계산된 금액
"""
def get_targetprice(cal_type, st_price, chg_val):
    try:
        # 계산된 가격
        rtn_price = st_price
 
        # 호가단위로 계산
        if cal_type.upper() == "H":
 
            for i in range(0, abs(int(chg_val))):
 
                hoga_val = get_hoga(rtn_price)
 
                if Decimal(str(chg_val)) > 0:
                    rtn_price = Decimal(str(rtn_price)) + Decimal(str(hoga_val))
                elif Decimal(str(chg_val)) < 0:
                    rtn_price = Decimal(str(rtn_price)) - Decimal(str(hoga_val))
                else:
                    break
 
        # 비율로 계산
        elif cal_type.upper() == "R":
 
            while True:
 
                # 호가단위 추출
                hoga_val = get_hoga(st_price)
 
                if Decimal(str(chg_val)) > 0:
                    rtn_price = Decimal(str(rtn_price)) + Decimal(str(hoga_val))
                elif Decimal(str(chg_val)) < 0:
                    rtn_price = Decimal(str(rtn_price)) - Decimal(str(hoga_val))
                else:
                    break
 
                if Decimal(str(chg_val)) > 0:
                    if Decimal(str(rtn_price)) >= Decimal(str(st_price)) * (
                            Decimal(str(1)) + (Decimal(str(chg_val))) / Decimal(str(100))):
                        break
                elif Decimal(str(chg_val)) < 0:
                    if Decimal(str(rtn_price)) <= Decimal(str(st_price)) * (
                            Decimal(str(1)) + (Decimal(str(chg_val))) / Decimal(str(100))):
                        break
 
        return rtn_price
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

"""
- Name: get_accounts
- Desc: 잔고 정보 조회 하기 입니다.
- Input
    1) except_yn : KRW 및 소액 제외
    2) market_code : 마켓코드 추가(매도시 필요)
- Output
    1) 잔고 정보
"""
def get_accounts(except_yn, market_code):
    try:
 
        rtn_data = []
 
        # 소액 제외 기준
        min_price = 5000
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("GET", server_url + "/v1/accounts", "", headers)
        account_data = res.json()
 
        for account_data_for in account_data:
 
            # KRW 및 소액 제외
            if except_yn == "Y" or except_yn == "y":
                if account_data_for['currency'] != "KRW" and Decimal(str(account_data_for['avg_buy_price'])) * (Decimal(str(account_data_for['balance'])) + Decimal(str(account_data_for['locked']))) >= Decimal(str(min_price)):
                    rtn_data.append(
                        {'market': market_code + '-' + account_data_for['currency'], 'balance': account_data_for['balance'],
                         'locked': account_data_for['locked'],
                         'avg_buy_price': account_data_for['avg_buy_price'],
                         'avg_buy_price_modified': account_data_for['avg_buy_price_modified']})
            else:
                rtn_data.append(
                    {'market': market_code + '-' + account_data_for['currency'], 'balance': account_data_for['balance'],
                     'locked': account_data_for['locked'],
                     'avg_buy_price': account_data_for['avg_buy_price'],
                     'avg_buy_price_modified': account_data_for['avg_buy_price_modified']})
 
        return rtn_data
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

"""
- Name: get_krwbal
- Desc: 원화 잔고 조회 입니다.
- Input
    1) KRW 잔고 Dictionary
      1. krw_balance : KRW 잔고
      2. fee : 수수료
      3. available_krw : 매수가능 KRW잔고(수수료를 고려한 금액)
"""
def get_krwbal():
    try:
 
        # 잔고 리턴용
        rtn_balance = {}
 
        # 수수료 0.05%(업비트 기준)
        fee_rate = 0.05
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("GET", server_url + "/v1/accounts", "", headers)
 
        data = res.json()
 
        for dataFor in data:
            if (dataFor['currency']) == "KRW":
                krw_balance = math.floor(Decimal(str(dataFor['balance'])))
 
        # 잔고가 있는 경우만
        if Decimal(str(krw_balance)) > Decimal(str(0)):
            # 수수료
            fee = math.ceil(Decimal(str(krw_balance)) * (Decimal(str(fee_rate)) / Decimal(str(100))))
 
            # 매수가능금액
            available_krw = math.floor(Decimal(str(krw_balance)) - Decimal(str(fee)))
 
        else:
            # 수수료
            fee = 0
 
            # 매수가능금액
            available_krw = 0
 
        # 결과 조립
        rtn_balance['krw_balance'] = krw_balance
        rtn_balance['fee'] = fee
        rtn_balance['available_krw'] = available_krw
 
        return rtn_balance
 
    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception:
        raise

"""
- Name: get_order
- Desc: 미체결 주문 조회
- Input
    1) target_item : 대상종목
      1. krw_balance : KRW 잔고
      2. fee : 수수료
      3. available_krw : 매수가능 KRW잔고(수수료를 고려한 금액)
- Output
    1) 미체결 주문 내역
"""
def get_order(target_item):
    try:
        query = {
            'market': target_item,
            'state': 'wait',
        }
 
        query_string = urlencode(query).encode()
 
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
 
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
 
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
 
        res = send_request("GET", server_url + "/v1/orders", query, headers)
        rtn_data = res.json()
 
        return rtn_data
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise