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
model_sentence = SentenceTransformer('jhgan/ko-sroberta-multitask')
model_sentence.save('D:/model_clone/ko-sroberta-multitask')

def get_similarity(model_sentence: SentenceTransformer, text0: str, text1: str) -> float:
    if not text0 or not text1:
        logger.warning("입력 문장 중 하나 이상이 비어 있습니다.")
        return 0.0

    try:
        with torch.no_grad():
            emb0 = model_sentence.encode(text0).reshape(1, -1)
            emb1 = model_sentence.encode(text1).reshape(1, -1)

        dot_product = np.dot(emb0, emb1.T).item()
        norm_product = np.linalg.norm(emb0) * np.linalg.norm(emb1)

        similarity = dot_product / norm_product if norm_product != 0 else 0.0
        logger.info(f"유사도 계산: {similarity:.4f} (\"{text0}\" ↔ \"{text1}\")")
        return similarity

    except Exception as e:
        logger.error("텍스트 유사도 계산 실패: %s", e)
        logger.error(traceback.format_exc())
        return 0.0
		
		
if __name__ == '__main__':
    # 비교할 텍스트 정의
    text0 = "이 사진에는 여섯 명이 있습니다."
    text1 = "완전히 다릅니다."

    model_sentence = SentenceTransformer('D:/model_clone/ko-sroberta-multitask',device=device)

    similarity = get_similarity(model_sentence, text0, text1)		