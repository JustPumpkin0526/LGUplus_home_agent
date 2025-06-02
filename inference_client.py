import requests
from PIL import Image
import io

def infer_from_server_with_image_object(server_url, image: Image.Image, query, model_name="your_model_name", temperature=0.0, top_p=0.0):
    url = f"{server_url}/infer"
    
    image_bytes_io = io.BytesIO()
    image.save(image_bytes_io, format="JPEG")
    image_bytes_io.seek(0)

    files = {
        "image": ("image.jpg", image_bytes_io, "image/jpeg")
    }

    data = {
        "query": query,
        "model_name": model_name,
        "temperature": str(temperature),
        "top_p": str(top_p)
    }

    response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 서버 응답 오류: {response.status_code}")
        return response.text

# 예시 사용
if __name__ == "__main__":
    # VLM 동작하는 서버 주소(변경X)
    server_url = "http://172.16.8.52:8000"  # 예: "http://192.168.0.101:8000"
    
    ##########################################################################
    # 로컬 이미지 경로
    image_path = "test.png"
    # 프롬프트
    user_query = "이 이미지를 설명해줘"
    # 사용할 모델 이름
    '''
    Llama3.2-VIX-M-3B-KO: 한글 3B 모델
    Llama3.2-VIX-V-1B-EN: 영어 1B 모델
    '''
    model_name = "Llama3.2-VIX-V-1B-EN"
    ##########################################################################
    
    image = Image.open(image_path).convert("RGB")  # 혹은 OpenCV로 읽은 이미지를 PIL로 변환해도 OK
    result = infer_from_server_with_image_object(server_url, image, user_query, model_name)
    print("결과:", result)
