import requests
from time import time

def get_text_similarity(text0, text1):
    # url = "http://172.16.15.191:2222/api/vlm/v1/get_text_similarity/"
    # url = "http://localhost:8081/api/vlm/v1/get_text_similarity/"
    url = "http://172.16.15.69:8081/api/vlm/v1/get_text_similarity/"
    data = {
        'text0': text0,
        'text1': text1
    }

    t0 = time()
    print(f"Requesting similarity for:\n- text0: {text0}\n- text1: {text1}")

    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"요청 실패: {e}")
        return None

    t1 = time()
    print(f"요청 소요 시간: {round(t1 - t0, 3)}초")

    result = response.json()
    if result.get("code") == 200:
        sim = result.get("simimarity", None)
        print(f"유사도: {sim}")
        return sim
    else:
        print("서버 응답 오류:", result)
        return None

if __name__ == '__main__':
    # 비교할 텍스트 정의
    text0 = "오영시에서 왔다갔다"
    text1 = "오산 지역에서 움직였다"

    get_text_similarity(text0, text1)
