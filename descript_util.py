from PIL import Image

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from urllib.parse import quote

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage

from inference_client import infer_from_server_with_image_object
from textsimilarity import get_similarity

from sentence_transformers import SentenceTransformer

import pandas as pd

import json
import shutil
import random
import time
import cv2
import os
import math

def get_img_size(img_width, img_height):
    col_width = img_width*31.5/252.19
    row_height = img_height*149.1/198.96
    return (col_width, row_height)

def DeleteAllFiles(folderpath):
    if os.path.exists(folderpath):
        for file in os.scandir(folderpath):
            os.remove(file.path)
        return 'Remove All File'
    else:
        return 'Directory Not Found'
    
def baby_sleep_check(descript, model_sentence):
    keywards = ["자고", "자는", "수면", "잠"]
    for keyword in keywards:
        if keyword in descript:
            check = True
            break
        else:
            check = False        
    if check == True:
        sleep_score = max(get_similarity(model_sentence, descript, "아기가 자고 있습니다."), get_similarity(model_sentence, descript, "아기가 자는 중입니다."), get_similarity(model_sentence, descript, "아기가 수면 중입니다."), get_similarity(model_sentence, descript, "아기가 잠에 들었습니다."))

        if sleep_score >= 0.7:
            sleep_descript = "아기가 자는 중입니다."
        else :
            sleep_descript = "아기가 깨어 있습니다."
    else :
        sleep_descript = "아기가 깨어 있습니다."
    return sleep_descript

def get_image_description(file_name):
    file_path = f"uploaded_files/{file_name}"

    request_img = Image.open(file_path)

    result = infer_from_server_with_image_object("http://172.16.8.52:8000", request_img, "아기가 자고 있나요? 아니면 아기가 깨어 있나요?","Llama3.2-VIX-M-3B-KO")

    descript = result.get('result')

    return descript
    
def get_sample(file_name, request_sec = 0):
    file_path = f"uploaded_files/{file_name}"
    video = cv2.VideoCapture(file_path) 
    folder_name = file_path[:-4]

    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        else:
            DeleteAllFiles(folder_name)
    except OSError:
        print('Error: Already created directory. ' + folder_name)

    sample_count = 1

    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = math.trunc(video.get(cv2.CAP_PROP_FPS))
    get_frame = math.trunc(fps * request_sec)

    sample_list = []

    for frame_idx in range(0, frame_count, get_frame):
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, image = video.read()

        if not ret:
            break
        print(frame_idx, flush=True)
        sample_count += 1 

        #현재 프레임에 fps를 나눠 현재 몇초인지를 알 수 있음
        frame_second = frame_idx // fps
        second = frame_second%60
        minute = (frame_second//60)%60 
        hour = frame_second//60//60

        #타임 스탬프 구하기
        file_time = f"{hour:02d}_{minute:02d}_{second:02d}"
        file_name = f"baby_test_{file_time}.jpg"

        image_path = folder_name + "/%s" %file_name

        sample_list.append({"Time":frame_second, "File_path":image_path})
        
        cv2.imwrite(image_path, image)
        
    return sample_list
    
def get_description(sample_list):

    device = "cuda:0"
    model_sentence = SentenceTransformer('/model_clone/ko-sroberta-multitask',device=device)

    description_dict = {}
    for sample in sample_list:
        request_img = Image.open(sample["File_path"])

        result = infer_from_server_with_image_object("http://172.16.8.52:8000", request_img, "아기가 자고 있나요? 아니면 아기가 깨어 있나요?","Llama3.2-VIX-M-3B-KO")

        descript = result.get('result')

        sleep_descript = baby_sleep_check(descript, model_sentence)

        description_dict[sample["Time"]] = sleep_descript

    return description_dict

def make_excel(file_name, sample_list, description_dict):
    write_wb = Workbook()
    write_ws = write_wb.active

    write_ws.append(["IMAGE","TIMESTAMP","DESCRIPT","SLEEP_CHANGE", "SLEEP_DESCRIPT"])

    sample_count = 1

    folder_name, _ = os.path.splitext(file_name)

    check_sleep_descript = ""

    for sample in sample_list:

        sample_count += 1
        
        img = XLImage(sample["File_path"])
        img.width = 300
        img.height = 200

        image_cell = 'A'+ str(sample_count)
        write_ws.add_image(img, image_cell)

        frame_second = sample["Time"]
        second = frame_second%60
        minute = (frame_second//60)%60 
        hour = frame_second//60//60

        Time = f"{hour:02d}:{minute:02d}:{second:02d}"

        descript = description_dict[str(sample["Time"])]

        write_ws['B'+str(sample_count)] = Time
        write_ws['C'+str(sample_count)] = descript

        width, height = get_img_size(img.width, img.height)
        write_ws.column_dimensions['A'].width = width
        write_ws.row_dimensions[sample_count].height = height
        
        if descript == check_sleep_descript:
            write_ws['D'+str(sample_count)] = 'X'
        else:
            check_sleep_descript = descript
            write_ws['D'+str(sample_count)] = 'O'
        write_ws['E'+str(sample_count)] = descript
    write_wb.save(filename=f"uploaded_files/{folder_name}.xlsx")