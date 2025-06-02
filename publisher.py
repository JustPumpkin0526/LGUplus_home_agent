#conda actvate py38
from pydantic import BaseModel
import uvicorn
# import redis
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from multiprocessing import Process, Queue
from uuid import uuid4
import base64
import json
import time
import queue 
from PIL import Image
from io import BytesIO

# from time import time
import traceback
import yaml
import pickle
import sys
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import torch
# torch.backends.cudnn.benchmark = True

import numpy as np
import importlib
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer

from workers import *
from logger_config import logger
import GPUtil
GPUtil.showUtilization()

base_abspath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),".."))
sys.path.append(base_abspath)
# device = "cpu"
device = "cuda:0"

# cache_dir = "./model"
# ko-sroberta-multitask
# model = SentenceTransformer('jhgan/ko-sroberta-multitask')
# model.save('E:/model_clone/ko-sroberta-multitask')
# 서버 초기화 시 워밍업 이미지로 1회 추론
def warmup_yolo(model):
    # import numpy as np
    # from PIL import Image

    dummy_img = Image.fromarray(np.zeros((640, 640, 3), dtype=np.uint8))
    print("YOLO 워밍업 중...")
    _ = model(dummy_img)
    print("YOLO 워밍업 완료")

def full_pipeline_warmup(model):
    dummy = Image.fromarray(np.zeros((640, 640, 3), dtype=np.uint8)).convert("RGB")
    buf = BytesIO()
    dummy.save(buf, format="JPEG")
    buf.seek(0)
    image_data = buf.read()
    img = Image.open(BytesIO(image_data)).convert("RGB")
    model(img)  # full path warmup

# # YOLO 모델 로딩 (최초에 한 번만)
# model_objdet = YOLO('yolov5s.pt')  # 또는 'yolov8n.pt' 등
# model_sentence = SentenceTransformer('E:/model_clone/ko-sroberta-multitask')

# with torch.no_grad():
#     model_sentence.encode('warmup model')
#     warmup_yolo(model_objdet)

TIME_OUT = 1
app = FastAPI()

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

objdet_input_q = Queue()
objdet_output_q = Queue()
similarity_input_q = Queue()
similarity_output_q = Queue()

def draw_boxes_and_save(image_data: bytes, results, save_path="output_images/result.jpg"):
    img = Image.open(BytesIO(image_data)).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 폰트 설정 (시스템에 맞는 경로 지정 필요)
    try:
        font = ImageFont.truetype("arial.ttf", size=16)
    except:
        font = ImageFont.load_default()

    for bbox, class_name, score in results:
        x1, y1, x2, y2 = bbox
        label = f"{class_name} {int(score * 100)}%"

        # 텍스트 크기 계산
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # 바운딩 박스 그리기
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

        # 텍스트 배경 박스
        draw.rectangle([x1, y1 - text_height, x1 + text_width, y1], fill="red")

        # 텍스트 그리기
        draw.text((x1, y1 - text_height), label, fill="white", font=font)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    img.save(save_path)
    print(f"바운딩 박스 이미지 저장 완료: {save_path}")


# 멀티프로세싱 큐 생성


# 추론 백엔드 워커
def object_detect_worker(objdet_input_q: Queue, objdet_output_q: Queue):
    logger.info("객체검출 워커 시작")  
    logger.info("객체검출 워커, yolo model load start")       
    model_objdet = YOLO('yolov5s.pt')  # 또는 'yolov8n.pt' 등
    model_objdet.to(device)
    with torch.no_grad():
        # warmup_yolo(model_objdet)
        full_pipeline_warmup(model_objdet)
    logger.info("객체검출 워커 시작, yolo model loading finished")    
    logger.info(f"###########객체검출 워커 시작, model_objdet device={model_objdet.device}")
    # print("객체검출 워커 시작")    

    while True:
        try:
            task = objdet_input_q.get(timeout=TIME_OUT)
        except queue.Empty:
            # 큐가 비어 있으면 잠시 대기하고 루프 계속
            # time.sleep(0.1)
            continue

        if task is None:
            continue
        task_id = task["task_id"]
        logger.info(f'object_detect_worker: {task_id}')

        try:
            image_data = base64.b64decode(task["image_b64"])
            results = yolo_objdetect(model_objdet, image_data)
            logger.info(f'object_detect_worker 결과: {results}')
            objdet_output_q.put({"task_id": task_id, "results": results})
        except Exception as e:
            logger.error("객체 검출 처리 중 오류 발생:\n%s", traceback.format_exc())
         
    

@app.post("/api/vlm/v1/detect_object/")
async def detect_object_api(image: UploadFile = File(...)):
    image_data = await image.read()
    image_b64 = base64.b64encode(image_data).decode('utf-8')
    task_id = str(uuid4())
    logger.info(f"요청 수신: detect_object_api task_id={task_id}")
    # 큐에 이미지 전달
    objdet_input_q.put({
        "task_id": task_id,
        "image_b64": image_b64
    })

    # 결과 대기 (최대 10초 타임아웃)
    start_time = time.time()
    # timeout = 10
    poll_interval = 0.1
    waited = 0    

    while waited < TIME_OUT:        
        try:
            result = objdet_output_q.get(timeout=TIME_OUT)
        except queue.Empty:
            # 큐가 비어 있으면 잠시 대기하고 루프 계속
            # time.sleep(0.1)
            continue

        if result is None:
            continue
        print('****** detect_object_api',result)
        if result["task_id"] == task_id:
            logger.info(f"결과 반환: {result}")
            return JSONResponse(
                content={
                    "code": 200,
                    "message": "객체검출 성공!",
                    "results": result["results"]
                }
            )
        else:
            # 다른 작업일 경우 다시 대기열에 넣음
            objdet_output_q.put(result)

    time.sleep(poll_interval)
    waited += poll_interval
    
    logger.warning("객체검출 처리 시간 초과")
    return JSONResponse(content={"code": 504, "message": "객체검출 처리 시간 초과"})

def text_similarity_worker(similarity_input_q: Queue, similarity_output_q: Queue):
    logger.info("텍스트 유사도 워커 시작")
    logger.info("텍스트 유사도 워커: SentenceTranceformer 모델 loading start")
    model_sentence = SentenceTransformer('E:/model_clone/ko-sroberta-multitask',device=device)
    logger.info("텍스트 유사도 워커: SentenceTranceformer 모델 loading finished")
    logger.info(f"###########텍스트 유사도 워커, model_sentence device={model_sentence.device}")


    with torch.no_grad():
        model_sentence.encode('warmup model')

    while True:
        try:        
            task = similarity_input_q.get(timeout=TIME_OUT)
        except queue.Empty:
            # 큐가 비어 있으면 잠시 대기하고 루프 계속
            time.sleep(0.1)
            continue
        if task is None:
            continue        
        task_id = task["task_id"]
        logger.info(f"text_similarity_worker: {task_id}")

        try:
            text0 = task["text0"]
            text1 = task["text1"]

            similarity = get_similarity(model_sentence, text0, text1)

            # 결과 큐에 결과 넣기
            similarity_output_q.put({
                "task_id": task_id,
                "similarity": similarity
            })
        except Exception as e:
            logger.error("유사도 계산 실패:\n%s", traceback.format_exc())


@app.post("/api/vlm/v1/get_text_similarity/")
async def get_text_similarity_api(
    text0: str = Form(...),
    text1: str = Form(...)
):
    task_id = str(uuid4())
    logger.info(f"유사도 요청 수신: task_id={task_id}")
    # 입력 큐에 작업 전달
    similarity_input_q.put({
        "task_id": task_id,
        "text0": text0,
        "text1": text1
    })

    # 결과 대기 (최대 10초)
    # timeout = 10
    poll_interval = 0.1
    waited = 0

    while waited < TIME_OUT:
        # while not similarity_output_q.empty():
        try:
            logger.info("유사도 결과 대기 중...")
            result = similarity_output_q.get(timeout=TIME_OUT)
        except queue.Empty:
            # 큐가 비어 있으면 잠시 대기하고 루프 계속
            # time.sleep(0.1)
            continue

        if result is None:
            continue
        if result["task_id"] == task_id:
            return JSONResponse(
                content={
                    "code": 200,
                    "message": "텍스트 유사도 추출 성공!",
                    "simimarity": result["similarity"]
                }
            )
        else:
            # 다른 요청 결과는 다시 큐에 보관
            similarity_output_q.put(result)

    time.sleep(poll_interval)
    waited += poll_interval

    logger.warning("유사도 처리 시간 초과")
    return JSONResponse(
        content={"code": 504, "message": "유사도 처리 시간 초과"}
    )


if __name__ == "__main__":
    import uvicorn
    from multiprocessing import Process
    import sys
    # torch.backends.cudnn.benchmark = True
    # 워커 프로세스 정의 및 시작
    worker_objdet = Process(target=object_detect_worker, args=(objdet_input_q, objdet_output_q))
    worker_similarity = Process(target=text_similarity_worker, args=(similarity_input_q, similarity_output_q))

    worker_objdet.start()
    worker_similarity.start()

    try:
        logger.info("FastAPI 서버 시작 중...")        
        # uvicorn.run(app, host="localhost", port=8081)
        # uvicorn.run(app, host="172.16.15.191", port=8081)
        uvicorn.run(app, host="0.0.0.0", port=8081)

    except KeyboardInterrupt:
        logger.warning("종료 시그널 감지됨 (Ctrl+C)")
    finally:
        logger.info("워커 프로세스 종료 중...")
        # 워커 종료
        worker_objdet.terminate()
        worker_similarity.terminate()
        # 워커 종료 대기
        worker_objdet.join()
        worker_similarity.join()
        logger.info("모든 프로세스가 정상적으로 종료되었습니다.")
        sys.exit(0)

