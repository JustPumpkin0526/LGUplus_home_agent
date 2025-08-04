from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import os
import re
import json
import random
import shutil
import pandas as pd
from pathlib import Path
from openpyxl import load_workbook


from _tools import *
from engine.libHomeAgent import vp

sampled_img_root = f"results/sampled_imgs"

video_dir = os.path.join(os.path.dirname(__file__), "videos")
image_dir = os.path.join(os.path.dirname(__file__), sampled_img_root)

sampled_imgs_root = Path("./results/sampled_imgs")
if not sampled_imgs_root.exists():
    sampled_imgs_root.mkdir(parents=True, exist_ok=True)

excel_root = Path("./results/excel")
if not excel_root.exists():
    print("Creating excel result folder...")
    excel_root.mkdir(parents=True, exist_ok=True)

json_root = Path("./results/json")
if not json_root.exists():
    print("Creating excel result folder...")
    json_root.mkdir(parents=True, exist_ok=True)

query = '''
Classify the baby’s state in the given image.

Consider facial expression, posture, eye status, and visibility when making your decision. Facial expressions and eye status should only be judged if the baby's face is clearly visible.

Choose one of the following states:
- Unknown: Image is too dark, blurry, or includes a third person, making the baby’s state unidentifiable.
- No_baby: No baby is visible in the image.
- Crying: Baby’s face shows a crying expression (e.g., mouth open, visible distress).
- Moving: Baby is in a posture that requires effort, such as sitting, standing, or crawling.
- Awake: Baby is lying down with eyes open and not crying.
- Sleep: Baby is lying down with eyes closed and not crying.
'''

app = FastAPI()

# 정적 파일 경로 연결
app.mount("/engine/web_ui", StaticFiles(directory="engine/web_ui"), name="web_ui")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/results/sampled_imgs", StaticFiles(directory="results/sampled_imgs"), name="sample_results")
app.mount("/results/excel", StaticFiles(directory="results/excel"), name="excel_results")
app.mount("/results/json", StaticFiles(directory="results/json"), name="json_results")
app.mount(f"/{sampled_img_root}", StaticFiles(directory=image_dir), name="video_sampled")


# HTML 템플릿 폴더
templates = Jinja2Templates(directory="engine/web_ui/_templates")

# ---------------------------
# 🔹 메인 페이지
# ---------------------------
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    # video_path = f"/videos/{video_name}.mp4"
    return templates.TemplateResponse("index.html", {"request": request})
    # return templates.TemplateResponse("index.html", {"request": request, "video_path":video_path})

@app.post("/vlm_image_query")
async def vlm_image_query(file: UploadFile = File(...)):
    file_location = os.path.join("videos", file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # result = vp.vlm_image_process("Llama3.2-VIX-M-3B-KO", "http://172.16.8.52:8000", "당신은 아기 관찰자 입니다. 아기의 상태를 'Sleep', 'Awake', 'Seat', 'Stand', 'Play', 'None' 6가지 중 하나로 설명해주세요", {"img_path":file_location})
    result = vp.vlm_image_process("Llama3.2-VIX-1B-Small", "http://172.16.8.52:8000", query, {"img_path":file_location})
    descript = result.get('result')
    return JSONResponse(content={"descript": descript})

@app.post("/get_sample")
async def sample(file: UploadFile = File(...), sampling_interval: int = Form(0)):
    file_location = os.path.join("videos", file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    video_file_path = f"videos/{file.filename}"
    sample_list = vp.video_sampling(video_file_path, "results/sampled_imgs", sampling_interval, True)
    print(sample_list, flush=True)
    return JSONResponse(content={"sample_list":sample_list})
    # return JSONResponse(content={"sample_list":""})

@app.post("/vlm_video_query")
async def vlm_video_query(video_name: str = Form(...), sample_list: str = Form(...)):
    print("vlm_query", flush=True)
    sampled_video_infos = json.loads(sample_list)
    # print(sampled_video_infos, flush=True)
    vlm_results = vp.vlm_video_process("Llama3.2-VIX-1B-Small", "http://172.16.8.52:8000", query, sampled_video_infos)
    # vlm_results = vp.vlm_video_process("Llama3.2-VIX-M-3B-KO", "http://172.16.8.52:8000", "당신은 아기 관찰자 입니다. 아기의 상태를 'Sleep', 'Awake', 'Seat', 'Stand', 'Play', 'None' 6가지 중 하나로 설명해주세요", sampled_video_infos)

    # for vlm_result in vlm_results:
    #     print(vlm_result, flush=True)
    file_name = Path(video_name).stem
    json_dst_path = f"results/json/{file_name}.json"
    fs.save_json(json_dst_path, vlm_results)
    
    return JSONResponse(content={"descript_dict": vlm_results})

@app.post("/make_excel")
async def excel(
    video_name: str = Form(...),
    video_infos: str = Form(...),            # ✅ 문자열로 받기
):
    print("make_excel")
    video_infos = json.loads(video_infos)

    file_name = Path(video_name).stem
    excel_root = f"results/excel"
    excel_path = f"{excel_root}/{file_name}.xlsx"

    print(video_infos, flush=True)
    print(excel_path, flush=True)
    vp.excel_process(excel_path, video_infos, 300, 200)

    return JSONResponse(content={"message": "엑셀 생성 완료"})

@app.post("/load_excel_data")
async def get_excel_data(file: UploadFile = File(...)):
    file_name, file_extension = os.path.splitext(file.filename)
    excel_path = f"./results/excel/{file_name}.xlsx"
    result_sheet = pd.read_excel(excel_path, sheet_name='Sheet', usecols= [1,2,3,4])

    result_sheet = result_sheet.replace([float('inf'), float('-inf')], pd.NA)
    result_sheet = result_sheet.fillna('')

    result_wb = load_workbook(excel_path)
    result_ws = result_wb.active

    image_urls = []
    for row in result_ws.iter_rows(min_row=2):
        time_str = row[1].value
        h, m, s = map(int, time_str.split(":"))
        file_time = f"{h:02d}_{m:02d}_{s:02d}"
        image_filename = f"baby_test_{file_time}.jpg"
        image_urls.append(f"/results/sampled_imgs/{file_name}/{image_filename}")
    
    result_sheet.insert(0, "이미지", image_urls)

    return JSONResponse(content={
        "columns": list(result_sheet.columns),
        "data": result_sheet.values.tolist()
    })

# conda activate lguplus

# uvicorn app:app --reload

# from engine.libHomeAgent import vp

# if __name__ == "__main__":
#     # w, h = vp.get_excel_img_size(640, 480)
#     # print(w, h)

#     # test_sim_score = vp.test_text_similarity("텍스트 유사도 테스트", "두 텍스트의 유사도를 테스트 합니다.")
#     # print(test_sim_score)

#     root_folder = "./videos"
#     file_name = "류_상250426_11"
#     file_path = f"{root_folder}/{file_name}.mp4"
#     save_root = f"results/sampled_imgs"
#     vp.video_sampling(file_path, save_root, True)

# y_pred = ["A", "B", "C", "D", "E"]
# y_true = [["A"], ["B", "C", "D"], ["B", "C"], ["B"], ["E"]]

# # labels = ["A", "B", "C", "D", "E", ["A"], ["B", "C", "D"], ["B", "C"], ["B"], ["E"]]
# labels = ["A", "B", "C", "D", "E"]

# scores = {}

# print("GT", y_true)
# print("Pred", y_pred)
# print("-----------------\n")
# for true, pred in zip(y_true, y_pred):
#     print("GT", true)
#     print("Pred", pred)

# for cls in labels:
#     print("Class", cls)
    
#     tp = sum((cls in yt and cls == yp) for yt, yp in zip(y_true, y_pred))
#     fp = sum((cls not in yt and cls == yp) for yt, yp in zip(y_true, y_pred))
#     fn = sum((cls in yt and cls != yp) for yt, yp in zip(y_true, y_pred))

#     precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
#     recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
#     f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

#     scores[cls] = {
#         "precision": precision,
#         "recall": recall,
#         "f1": f1
#     }

#     print(scores[cls])
    
