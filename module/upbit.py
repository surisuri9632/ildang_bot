import time
import logging
import requests


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