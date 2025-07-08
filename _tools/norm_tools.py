import numpy as np
import random
from datetime import datetime, timedelta

# time function
def str_tm_to_datetime(tm, format):
        # 문자열을 datetime 객체로 변환
        if format == "%Y%m%d%H%M" and tm[-4:] == "2400":
            tm = tm[:-4] + "0000"
            time_obj = datetime.strptime(tm, format) + timedelta(days=1)
        else:
            time_obj = datetime.strptime(tm, format)
        
        return time_obj

def get_duration_tm(tm, duration=3, step=15):
    # 문자열을 datetime 객체로 변환
    if tm[-4:] == "2400":
        tm = tm[:-4] + "0000"
        time_obj = datetime.strptime(tm, "%Y%m%d%H%M") + timedelta(days=1)
    else:
        time_obj = datetime.strptime(tm, "%Y%m%d%H%M")

    # 3시간 전과 후의 시간 범위 설정
    start_time = time_obj - timedelta(hours=duration)
    # end_time = time_obj + timedelta(hours=duration)
    end_time = time_obj

    # 15분 간격으로 시간 생성 및 출력
    current_time = start_time
    times = []

    while current_time <= end_time:
        times.append(current_time.strftime("%Y%m%d%H%M"))
        current_time += timedelta(minutes=step)

    return times

def get_duration_between_tm(bgng_tm, end_tm, step=15, format="%Y%m%d%H%M"):
    start_time = str_tm_to_datetime(bgng_tm, format)
    end_time = str_tm_to_datetime(end_tm, format)

    current_time = start_time
    times = []

    while current_time <= end_time:
        times.append(current_time.strftime(format))
        current_time += timedelta(minutes=step)

    return times

def round_to_nearest_15_min(time_str, format="%Y%m%d%H%M"):
    # 문자열을 datetime 객체로 변환
    dt = datetime.strptime(time_str, format)

    # 15분 단위로 시간을 반올림
    minute_adjusted = (dt.minute + 7) // 15 * 15
    if minute_adjusted == 60:
        # 분이 60분으로 올림되면 한 시간을 추가하고 분을 0으로 설정
        dt = dt + timedelta(hours=1)
        minute_adjusted = 0

    # 보정된 시간 설정
    rounded_time = dt.replace(minute=minute_adjusted, second=0, microsecond=0)

    # 반올림된 시간이 입력 시간보다 클 경우, 이전 15분으로 이동
    if rounded_time > dt:
        rounded_time -= timedelta(minutes=15)

    # 결과를 원하는 형식으로 반환
    return rounded_time.strftime(format)

def get_current_time_str(format="%Y%m%d%H%M"):
    return datetime.now().strftime(format)

def get_next_time_str(tm, step=15, format="%Y%m%d%H%M"):
    tm = str_tm_to_datetime(tm)
    tm += timedelta(minutes=step)
    return tm.strftime(format)

# etc...
def generate_random_numbers(num):
    # 10번, 각각 50개의 랜덤 숫자 생성
    random_sets = [[random.randint(0, num) for _ in range(100)] for _ in range(10)]
    return random_sets
    
def find_element(data, key, value):
    return next((element for element in data if element.get(key) == value), None)

def find_elements(data, key, value):
    return [element for element in data if element.get(key) == value]

def index_loop(index, maxium):
    if (index <0):
        return maxium -1
    elif index > (maxium -1):
        return 0
    else:
        return index