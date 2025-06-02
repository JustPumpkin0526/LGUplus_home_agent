from PIL import Image

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage

from sentence_transformers import SentenceTransformer

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from inference_client import infer_from_server_with_image_object
from textsimilarity import get_similarity

import time
import cv2
import os
import math

code_start = time.time()

#엑셀의 셀을 이미지 크기에 맞게 변환하기 위해 크기를 조정하는 코드
def get_img_size(img_width, img_height):
    col_width = img_width*31.5/252.19
    row_height = img_height*149.1/198.96
    return (col_width, row_height)

#폴더 내부 요소 전부 삭제
def DeleteAllFiles(folderpath):
    if os.path.exists(folderpath):
        for file in os.scandir(folderpath):
            os.remove(file.path)
        return 'Remove All File'
    else:
        return 'Directory Not Found'

#엑셀 연동하기
write_wb = Workbook()
write_ws = write_wb.active

#영상 불러오기
filepath = 'video/baby_test_video(LGU+2).mp4'
video = cv2.VideoCapture(filepath)

if not video.isOpened():
    print("열리지 않는 파일")
    exit(0)

#프레임별 추출한 이미지 담을 폴더 생성
try:
    if not os.path.exists(filepath[:-4]):
        os.makedirs(filepath[:-4])
    else:
        DeleteAllFiles(filepath[:-4])
except OSError:
    print('Error: Creating directory. ' + filepath[:-4])

count = 1
fps = video.get(cv2.CAP_PROP_FPS)
get_frame = math.trunc(fps * 20)

write_ws.append(["추출 이미지","타임스탬프","Descript","유사도 스코어","장면 전환 여부"])
#프레임별 이미지 추출 및 타임스탬프, descript 받아오기
folder_name = filepath[:-4]
while(video.isOpened()):
    ret, image = video.read()
    if not ret:
        break
    
    #180프레임마다 이미지 추출(180프레임 = 6초) / 추출한 이미지를 vlm서버에 보내 descript 받아오기
    if(int(video.get(1)) % get_frame == 0):
        start = time.time()
        frame = str(int(video.get(1)))
         #추출한 이미지를 처음에 생성한 폴더에 frame<count>.jpg의 형태로 저장함
        
        #현재 프레임에 fps를 나눠 현재 몇초인지를 알 수 있음
        frame_second = round(int(frame) / fps)
        second = frame_second%60
        minute = (frame_second//60)%60 
        hour = frame_second//60//60
 
        #타임 스탬프 구하기
        Time = f"{hour:02d}:{minute:02d}:{second:02d}"
        file_time = f"{hour:02d}_{minute:02d}_{second:02d}"

        file_name = f"baby_test_{file_time}.jpg"
        cv2.imwrite(folder_name + "/%s" % file_name, image)

        count += 1

        image_path = folder_name + "/%s" %file_name
        request_img = Image.open(image_path)
        # 이전 프롬포트:아기가 잠을 자는 중인가요? 잠을 자는 중이 아니라면 무슨 행동을 하고있나요?, 아기 상황을 설명해주세요, 아기가 자는 중인가요? ‘네’ 혹은 ‘아니요’로 대답을 통일하세요, 아기의 상태와 행동을 설명헤주세요
        start_time = time.time()
        result = infer_from_server_with_image_object("http://172.16.8.52:8000", request_img, "아기가 무슨 상태인가요?","Llama3.2-VIX-M-3B-KO")
        end_time = time.time()
        
        img = XLImage(image_path)
        img.width = 300
        img.height = 200

        image_cell = 'A'+ str(count)
        descript = result.get('result')
        #if descript == '네':
        #    descript = '아기가 자는 중입니다.'
        #    if act_count > 0:
        #        act_count -= 1
        #elif descript == '아니요':
        #    descript = '아기가 깨어있습니다.'
        #    if act_count == 1:   
        #        act = infer_from_server_with_image_object("http://172.16.8.52:8000", request_img, "잠에서 깬 아기가 무슨 행동을 했나요?","Llama3.2-VIX-M-3B-KO")
        #        descript = act.get('result')
        #    else:
        #        act_count += 1
    
        write_ws.add_image(img, image_cell)
        write_ws.append({'B':Time, 'C':descript})

        width, height = get_img_size(img.width, img.height)

        write_ws.column_dimensions['A'].width = width
        write_ws.row_dimensions[count].height = height
        end = time.time()
        print(f"vlm 요청 시간은 {end_time - start_time:.5f}초 입니다.\n")
        print(f"{end - start:.5f} sec\n")
        

write_wb.save(filename="D:/excel/description.xlsx")
video.release()

read_wb = load_workbook(filename="D:/excel/description.xlsx")
read_ws = read_wb["Sheet"]

for des_count in range(count, 1, -1):
    device = "cuda:0"
    model_sentence = SentenceTransformer('D:/model_clone/ko-sroberta-multitask',device=device)
    if (des_count == 1):
        descript_value = str(read_ws['C'+str(des_count)].value)
        descript_check = str(read_ws['C'+str(des_count+1)].value)
    else:
        descript_value = str(read_ws['C'+str(des_count)].value)
        descript_check = str(read_ws['C'+str(des_count-1)].value)
    score = get_similarity(model_sentence, descript_value, descript_check)
    write_ws['D'+str(des_count)] = score

    if score > 0.7:
        write_ws['E'+str(des_count)] = "X"
    else:
        write_ws['E'+str(des_count)] = "O"

result_ws = write_wb.create_sheet('result')
result_ws.append(["추출 이미지","타임스탬프","Descript","유사도 스코어","장면 전환 여부"])

cell_num = 1
count_img = -1
file_list = os.listdir(folder_name + "/")
for row in write_ws.iter_rows():
    if row[4].value == 'O':
        cell_num +=1
        file_name = file_list[count_img]
        image_path = folder_name + "/%s" %file_name

        result_img = XLImage(image_path)
        result_img.width = 300
        result_img.height = 200

        result_ws.add_image(result_img, 'A'+str(cell_num))
        result_ws.append((cell.value for cell in row))

        width, height = get_img_size(img.width, img.height)
        result_ws.column_dimensions['A'].width = width
        result_ws.row_dimensions[cell_num].height = height
        
    count_img += 1
    
write_wb.save(filename="D:/excel/description.xlsx")
code_end = time.time()

print(f"{(code_end - code_start) // 60}분 {(code_end - code_start) % 60}초")