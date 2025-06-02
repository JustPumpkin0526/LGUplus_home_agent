import numpy as np
import torch
from PIL import Image
from io import BytesIO
import traceback
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer

from logger_config import logger  # 로거 설정 파일에서 가져오기

def yolo_objdetect(model_objdet: YOLO, image_data: bytes) -> list:
    try:
        img = Image.open(BytesIO(image_data)).convert("RGB")
    except Exception as e:
        logger.error("이미지 디코딩 실패: %s", e)
        logger.error(traceback.format_exc())
        raise ValueError(f"이미지 디코딩 실패: {e}")

    output = []
    with torch.no_grad():
        results = model_objdet(img)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            try:
                xyxy = [round(coord) for coord in box.xyxy[0].tolist()]
                cls_id = int(box.cls[0])
                score = float(box.conf[0])
                class_name = model_objdet.names[cls_id] if cls_id in model_objdet.names else str(cls_id)
                logger.info(f"객체 검출: {class_name} @ {xyxy} (score={score:.4f})")
                output.append([xyxy, class_name, round(score, 4)])
            except Exception as e:
                logger.warning("객체 처리 중 오류 발생: %s", e)
                logger.warning(traceback.format_exc())
                continue

    return output


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
