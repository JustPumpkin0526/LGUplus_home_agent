from engine.libHomeAgent.import_lib import *

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

from collections import defaultdict

import numpy as np

from library.vlm_inference_client import infer_from_server_with_image_object
import os
import json

from _tools import *

def imread(file_path):
    npArr = np.fromfile(file_path, dtype=np.uint8) 
    return cv2.imdecode(npArr, cv2.IMREAD_COLOR)
 
def imwrite(file_path, img, params=None): 
    try: 
        ext = os.path.splitext(file_path)[1] 
        result, n = cv2.imencode(ext, img, params)
        
        if result:
            with open(file_path, mode='w+b') as f:
                n.tofile(f)
            return True 
        else: 
            return False 
    except Exception as e: 
        print(e)
        return False

def create_image_save_folders(file_path):
    folder_path = Path(file_path).parent
    file_name = Path(file_path).stem
    folder_path = Path(f"{folder_path}/{file_name}")
    print(folder_path)
    if folder_path.exists() and folder_path.is_dir():
        shutil.rmtree(folder_path)
        #files = list(folder_path.iterdir())
        #files = [file for file in files if file.is_file()]
        #for file in files:
        #    file.unlink()
        os.makedirs(folder_path)
    else:
        os.makedirs(folder_path)

def get_timestamp_from_sec(sec):
    second = sec%60
    minute = (sec//60)%60 
    hour = sec//60//60

    timestamp = f"{hour:02d}:{minute:02d}:{second:02d}"
    return timestamp

def video_sampling(video_file_path, save_root, interval, b_save=True):
    
    file_name = Path(video_file_path).stem
    print(f"비디오 샘플링 진입: {file_name}" )
    folder_path = Path(video_file_path).parent
    video_info = []

    #영상 불러오기
    video = cv2.VideoCapture(video_file_path)

    if not video.isOpened():
        print("열리지 않는 파일")
        return
     
    count = 1
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / fps  # 총 영상 시간 (초)
    # interval = config["interval"] * 1000  # 10초 간격 (ms)
    interval = interval * 1000  # 10초 간격 (ms)

    current_time = 0 #3240000

    if b_save:
        save_dst_path = f"{save_root}/{file_name}"

        create_image_save_folders(save_dst_path)

    #프레임별 이미지 추출 및 타임스탬프, descript 받아오기
    while current_time < duration * 1000:
        video.set(cv2.CAP_PROP_POS_MSEC, current_time)
        ret, frame = video.read()
        if not ret:
            break
        
        #180프레임마다 이미지 추출(180프레임 = 6초) / 추출한 이미지를 vlm서버에 보내 descript 받아오기
        current_frame_cnt = int(video.get(cv2.CAP_PROP_POS_FRAMES))
        
        timestamp_str = get_timestamp_from_sec(int(current_time / 1000))
        timestamp_file = timestamp_str.replace(":", "_")
        # print(timestamp_str, current_frame_cnt)

        #추출한 이미지를 처음에 생성한 폴더에 frame<count>.jpg의 형태로 저장함
        img_name = f"baby_test_{timestamp_file}.jpg"
        img_dst_path = f"{save_root}/{file_name}/{img_name}"
        video_info.append({"img_path":img_dst_path, "timestamp":timestamp_str, "time":int(current_time / 1000)})
        if b_save :
            imwrite(img_dst_path, frame)

        count += 1

        current_time += interval
        # print(current_time)
        # print("count : ", count, flush=True)

    video.release()
    return video_info

def vlm_video_process(model, url : str, prompt :str, video_infos, file_name):
    check_descript = ""
    count = 0
    vlm_process_time = 0
    json_dst_path = f"results/json/{file_name}.json"

    for idx, video_info in enumerate(video_infos):
        start_time = time.time()
        frame_path = video_info["img_path"]
        request_img = Image.open(frame_path)
        
        #if os.path.exists(json_dst_path):
        #    pred_json = fs.load_json(json_dst_path)
        #    print(pred_json[count]["result"])
        #    
        #    if pred_json[count]["result"] == "Sleep":
        #        change_description = "baby_sleep"
#
        #    elif pred_json[count]["result"] == "Awake":
        #        change_description = "baby_awake"
#
        #    elif pred_json[count]["result"] == "Moving":
        #        change_description = "baby_moving"
#
        #    elif pred_json[count]["result"] == "Crying":
        #        change_description = "baby_crying"
#
        #    elif pred_json[count]["result"] == "Unknown":
        #        change_description = "unknown"
#
        #    elif pred_json[count]["result"] == "NoBaby":
        #        change_description = "no_baby"
#
        #    else :
        #        change_description = "vlm_error"
#
        #    if change_description == check_descript:
        #        video_info["scene_change"] = 'X'
        #    else:
        #        check_descript = change_description
        #        video_info["scene_change"] = 'O'
#
        #    video_info["result"] = pred_json[count]["result"]
        #    video_info["change_result"] = change_description
#
        #    print(count)
        #    count += 1
        #    continue


        # 이전 프롬포트:아기가 잠을 자는 중인가요? 잠을 자는 중이 아니라면 무슨 행동을 하고있나요?, 아기 상황을 설명해주세요
        
        # result = infer_from_server_with_image_object(config["url"], request_img, config["prompt"], config["model"])
        result = infer_from_server_with_image_object(url, request_img, prompt, model)
        result_description = result["result"]
        

        if result_description == "Sleep":
            change_description = "baby_sleep"
        elif result_description == "Awake":
            change_description = "baby_awake"
        elif result_description == "Moving":
            change_description = "baby_moving"
        elif result_description == "Crying":
            change_description = "baby_crying"
        elif result_description == "Unknown":
            change_description = "unknown"
        elif result_description == "NoBaby":
            change_description = "no_baby"
        else :
            change_description = "vlm_error"

        if change_description == check_descript:
            video_info["scene_change"] = 'X'
        else:
            check_descript = change_description
            video_info["scene_change"] = 'O'

        video_info["result"] = result_description
        video_info["change_result"] = change_description
        
        count += 1
        end_time = time.time()

        vlm_process_time += end_time - start_time
        print(f"vlm 요청 시간은 {end_time - start_time:.2f}초 입니다.")
        print(count)
        # print(result)
    print(f"vlm 요청 시간의 평균은 {vlm_process_time/count:.2f}초 입니다.")
    
    fs.save_json(json_dst_path, video_infos)

def video_process(video_list):
    for video_file in video_list:
        video_name = video_file.split(".")
        #if os.path.exists(f"./results/json/{video_name[0]}.json"):
        #    print("이미 존재합니다.")
        #    continue
        video_infos = video_sampling(f"videos/{video_file}","results/sampled_imgs",1, False)
        vlm_video_process("Llama3.2-VIX-1B-Small", "http://172.16.8.52:8000", query, video_infos, video_name[0])

        if os.path.exists(f"./results/vlm_excel{video_name[0]}.xlsx"):
            continue
        pred_json_path = f'{root_path}/results/json/{video_name[0]}.json'
        pred_datas = fs.load_json(pred_json_path)

        vlm_excel_root = f"results/vlm_excel"
        excel_path = f"{vlm_excel_root}/{video_name[0]}.xlsx"

        vlm_excel_process(excel_path, pred_datas, 300, 200)
#파일 상위 경로
root_path = "."


def get_timestamp_from_sec(sec):
    second = sec%60
    minute = (sec//60)%60 
    hour = sec//60//60

    timestamp = f"{hour:02d}:{minute:02d}:{second:02d}"
    return timestamp

def get_sec_from_timestamp(timestamp:str):
    h, m, s = map(int, timestamp.split(":"))
    total_seconds = h * 3600 + m * 60 + s
    return str(total_seconds)

def datetime_str_to_seconds(datetime_str, format):
    dt = datetime.strptime(datetime_str, format)
    return int(dt.timestamp())

def seconds_to_datetime_str(seconds, format):
    dt = datetime.fromtimestamp(seconds)
    return dt.strftime(format)

# def convert_infer_res_xlsx_to_json(xlsx_path:str):
#     wb = load_workbook(xlsx_path)
#     ws = wb.active

#     # 헤더 추출 (1행)
#     headers = [cell.value for cell in ws[1]]

#     # 데이터 추출 (2행부터)
#     json_data = []
#     for row in ws.iter_rows(min_row=2, values_only=True):
#         row_dict = dict(zip(headers, row))
#         row_dict["TIME"] = get_sec_from_timestamp(row_dict["TIMESTAMP"])
#         row_dict["SCORE"] = round(row_dict["SCORE"], 3)
#         row_dict["DESCRIPT"] = re.sub(r'[^A-Z]', '', row_dict["DESCRIPT"].upper())
#         if row_dict["DESCRIPT"] == "SLEEP":
#             row_dict["IS_SLEEP"] = "O"
#             row_dict["DESCRIPT"] = "SLEEP"
#         else:
#             row_dict["IS_SLEEP"] = "X"
#             row_dict["DESCRIPT"] = "AWAKE"
#         # print(row_dict)
            
#         json_data.append(row_dict)
    
#     return json_data

def gt_to_pred_json(gt_json_path):
    gt_json_datas = fs.load_json(gt_json_path)

    result = {}
    gt_video_time_diff = 0
    cnt = 0
    for idx, json_data in enumerate(gt_json_datas):
        start_time = json_data["start_time"]
        end_time = json_data["end_time"]
        event_lists = json_data["event"]
        start_sec = datetime_str_to_seconds(start_time, "%m-%d-%Y %H:%M:%S")
        end_sec = datetime_str_to_seconds(end_time, "%m-%d-%Y %H:%M:%S")

        # gt 시간이 비디오 내 적혀있는 녹화 당시 시간으로 되어있어 비디오 실행 시간으로 변환하기 위함
        if idx == 0:
            gt_video_time_diff = start_sec

        # baby_awake, baby_crying, baby_moving은 모두 baby_awake를 포함해야 하는데 그렇지 않은 케이스가 존재함
        # baby_cough는 대상이 아니므로 baby_awake로 변환함
        #if event_lists[0] not in ["baby_sleep", "baby_awake", "unknown", "no_baby", "baby_cough"]:
        #    event_lists.insert(0, "baby_awake")
        # gt와 pred의 클래스명이 서로 상이함
        
        for tidx, gt_sec in enumerate(range(start_sec, end_sec+1, 1)):
            video_sec = gt_sec - gt_video_time_diff
            # print(video_sec)
            # start time이 겹치는 gt data가 가끔 존재하여 이를 처리하기 위함
            if video_sec in result:
                continue

            temp_result = {}
            temp_result["record_start_time"] = seconds_to_datetime_str(gt_sec, "%m-%d-%Y %H:%M:%S")
            temp_result["record_end_time"] = seconds_to_datetime_str(gt_sec + 1, "%m-%d-%Y %H:%M:%S")
            temp_result["time"] = video_sec
            
            temp_result["event_full"] = event_lists
            temp_result["event"] = [event_lists[0]]

            # if tidx == 0:
            #     temp_result["scene_change"] = "O"
            # else:
            #     temp_result["scene_change"] = "X"

            result.update({video_sec : temp_result})
            # print(video_sec, result[video_sec])

    gt_dst_path = f"{root_path}/gt/json/{file_name}.json"
    fs.save_json(gt_dst_path, result)

def convert_infer_res_xlsx_to_json(xlsx_path:str):
    wb = load_workbook(xlsx_path)
    ws = wb.active

    # 헤더 추출 (1행)
    headers = [cell.value for cell in ws[1]]

    # 데이터 추출 (2행부터)
    json_data = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        row_dict = dict(zip(headers, row))
        row_dict["TIME"] = get_sec_from_timestamp(row_dict["TIMESTAMP"])
        # row_dict["DESCRIPT"] = re.sub(r'[^A-Z]', '', row_dict["DESCRIPT"].upper())
        # if row_dict["DESCRIPT"] == "SLEEP":
        #     row_dict["IS_SLEEP"] = "O"
        #     row_dict["DESCRIPT"] = "Sleep"
        # else:
        #     row_dict["IS_SLEEP"] = "X"
        #     row_dict["DESCRIPT"] = "Awake"
        # print(row_dict)
            
        json_data.append(row_dict)
    
    return json_data

#def change_pred(pred_datas):
#    n = len(pred_datas)
#    i = 0
#    while i < n:
#        # target 값을 찾으면
#        if pred_datas[i] == target:
#            # 다음에 target이 아닌 구간이 있는지 탐색
#            j = i + 1
#            # 중간 구간의 시작 인덱스를 저장
#            start = j
#            # 연속으로 target이 아닌 값들 지나치기
#            while j < n and lst[j] != target:
#                j += 1
#            # 만약 j가 범위 내에 있고 lst[j] == target 이라면,
#            # i(=start-1)와 j 사이를 모두 target으로 채움
#            if j < n and lst[j] == target:
#                for k in range(start, j):
#                    lst[k] = target
#                # i를 j까지 점프시켜서 중복 채우기 방지
#                i = j
#            else:
#                # 더 이상 뒤에 target이 없으면 끝
#                break
#        else:
#            i += 1
#    return lst

def GT_check_process(pred_datas, gt_datas, file_name):
    print(f"GT 체크 진입 : {file_name}")
    #type_num = 4

    y_true = [data["event_full"] for time, data in gt_datas.items()]
    y_pred = ["baby_awake" if data["change_result"] == "baby_moving" else data["change_result"] for data in pred_datas]

    labels = ["baby_sleep", "baby_awake", "baby_crying", "no_baby", "unknown"]
    check_description = pred_datas[0]["change_result"]
    des_count = 0
    for idx, pred in enumerate(pred_datas):
        pred.setdefault('GT_check', " ")
        pred.setdefault('GT_timestamp', " ")
        pred.setdefault('GT_descript', " ")
        pred.setdefault('GT_change_descript', " ")
        pred.setdefault('use_sample', " ")
        pred.setdefault('use_video', "X")

        if pred["change_result"] == check_description:
            des_count += 1
            if des_count == 60:
                for i in range(idx-60, idx+1):
                    pred_datas[i]["use_video"] = "O"
            elif des_count >= 61:
                pred["use_video"] = "O"
        else:
            check_description = pred["change_result"]
            des_count = 0
    for pred, (time, GT) in zip(pred_datas, gt_datas.items()):
        pred["GT_descript"] =  ", ".join(GT["event"])
        pred["GT_timestamp"] = GT["record_start_time"]


    #if type_num == 2:
    #    labels = ["Sleep", "Awake"]
    #    y_true = [data["event_full"] for time, data in gt_datas.items()]
    #    y_pred = [data["change_result"] for data in pred_datas]
    #    for idx, events in enumerate(y_true):
    #        y_temp = []
    #        
    #        for true in events:
    #            if true in ["Awake", "Moving", "Crying", "Nobaby", "Unknown"]:
    #                if "Awake" in y_temp:
    #                    continue
    #                y_temp.append("Awake")
    #            else:
    #                y_temp.append(true)
    #        y_true[idx] = y_temp
    #    # y_true = [["Sleep"] if "Sleep" in event else ["Awake"] for event in y_true]
    #    y_pred = ["Sleep" if event == "Sleep" else "Awake" for event in y_pred]
    #elif type_num == 4:
    #    for pred in pred_datas:
    #        pred.setdefault('GT_check', " ")
    #        pred.setdefault('GT_timestamp', " ")
    #        pred.setdefault('GT_descript', " ")
    #        pred.setdefault('GT_change_descript', " ")
    #        pred.setdefault('use_sample', " ")
#
    #    labels = ["baby_sleep", "baby_awake", "no_baby", "unknown"]
#
    #    y_true = [data["event_full"] for time, data in gt_datas.items()]
    #    count = 0
    #    for pred in pred_datas:
    #        count += 1
    #        if count >= len(y_true):
    #            break
    #        pred["GT_descript"] = ", ".join(y_true[count])
    #        
#
    #    for evt in y_true:
    #        if "unknown" == evt[0]:
    #            if len(evt) <= 1:
    #                continue
    #            if "baby_sleep" ==  evt[1] or "baby_awake" ==  evt[1]:
    #                evt[0] = evt[1]
#
    #    # y_true = [["Sleep"] if "Sleep" in event else event for event in y_true]
    #    # y_true = [["Awake"] if "Awake" in event else event for event in y_true] 
    #    # y_true = [["Awake"] if "Moving" in event else event for event in y_true]
    #    # y_true = [["Awake"] if "Crying" in event else event for event in y_true]
    #    
    #    y_temp = []
    #    for idx, events in enumerate(y_true):
    #        if idx >= len(pred_datas):
    #            break
    #        
    #        if events[0] == "baby_awake" or events[0] == "baby_sleep":
    #            y_temp.append(events[0])
#
    #        elif "baby_sleep" in events:
    #            y_temp.append("baby_sleep")
#
    #        elif "baby_awake" in events:
    #            y_temp.append("baby_awake")
#
    #        elif "unknown" in events:
    #            y_temp.append("unknown")
#
    #        elif "no_baby" in events:
    #            y_temp.append("no_baby")
    #        else:
    #            y_temp.append(events)
    #            
    #    for pred, (time, GT) in zip(pred_datas, gt_datas.items()):
    #        pred["GT_timestamp"] = GT["record_start_time"]
    #    # y_true = [["Sleep"] if "Sleep" in event else event for event in y_true]
    #    y_true = y_temp
    #    y_pred = [data["change_result"] for data in pred_datas]
#
    #    count = 0
    #    for pred in pred_datas:
    #        count += 1
    #        if count >= len(y_true):
    #            break
    #        pred["GT_change_descript"] = y_true[count]
    #elif type_num == 6:
    #    labels = ["Sleep", "Awake", "Moving", "Crying", "Nobaby", "Unknown"] 
    #    y_true = [data["event_full"] for time, data in gt_datas.items()]
    #    # y_true = [["Unknown"] if "Unknown" in event else event for event in y_true]
    #    # y_true = [["Sleep"] if "Sleep" in event else event for event in y_true]
    #    y_pred = [data["change_result"] for data in pred_datas] 
    
    scores = {}
    # print("GT", y_true)
    # print("Pred", y_pred)
    # print("-----------------\n")

    #print("---------------------------------------------------")
    #for label in labels:
    #    print(f"{label}(gt) : ", sum([label in true for true in y_true]))
    #print("---------------------------------------------------")
    #for label in labels:
    #    print(f"{label}(pred) : ", sum([label == pred for pred in y_pred]))
    #print("---------------------------------------------------")
    
 
    for cls in labels:
            
        tp = 0
        fp = 0
        fn = 0
        #print("Class", cls)
        for idx, (yt, yp) in enumerate(zip(y_true, y_pred)):
            if ("baby_cough" in yt):
                pred_datas[idx]["GT_check"] = "-"
                continue

            if cls in yt and cls == yp:
                pred_datas[idx]["GT_check"] = "O"
                tp += 1
            if cls not in yt and cls == yp:
                pred_datas[idx]["GT_check"] = "X"
                fp += 1
            if cls in yt and cls != yp:
                fn += 1
                
        #tp = sum((cls in yt and cls == yp) for yt, yp in zip(y_true, y_pred))
        #fp = sum((cls not in yt and cls == yp) for yt, yp in zip(y_true, y_pred))
        #fn = sum((cls in yt and cls != yp) for yt, yp in zip(y_true, y_pred))

        # fn = sum((cls in yt and cls != yp and "Unknown" != yp) for yt, yp in zip(y_true, y_pred))

        precision = round(tp / (tp + fp), 3) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 3) if (tp + fn) > 0 else 0.0
        f1 = round((2 * precision * recall / (precision + recall)), 3) if (precision + recall) > 0 else 0.0

        scores[cls] = {
            "tp" : tp,
            "fp" : fp,
            "fn" : fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

        #print(scores[cls])
    
    # 클래스별 support 계산
    supports = {cls: sum(1 for yt in y_true if cls in yt) for cls in labels}
    valid_classes = [cls for cls, sup in supports.items() if sup > 0]

    # Macro
    # if valid_classes:
    #     macro_precision = sum(scores[cls]["precision"] for cls in valid_classes) / len(valid_classes)
    #     macro_recall = sum(scores[cls]["recall"] for cls in valid_classes) / len(valid_classes)
    #     macro_f1 = sum(scores[cls]["f1"] for cls in valid_classes) / len(valid_classes)
    # else:
    #     macro_precision = macro_recall = macro_f1 = 0.0

    # print("---------------------------------------------------")
    # print("[Macro]")
    # print("Macro Precision:", macro_precision)
    # print("Macro Recall:", macro_recall)
    # print("Macro F1:", macro_f1)

    # Micro
    total_tp = sum(s["tp"] for s in scores.values())
    total_fp = sum(s["fp"] for s in scores.values())
    total_fn = sum(s["fn"] for s in scores.values())

    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if (micro_precision + micro_recall) > 0 else 0.0

    micro_score = {"precision":micro_precision, "recall" : micro_recall, "micro_f1": micro_f1}

    #print("---------------------------------------------------")
    #print("[Micro]")
    #print("Micro Precision:", round(micro_precision, 3))
    #print("Micro Recall:", round(micro_recall, 3))
    #print("Micro F1:", round(micro_f1, 3))
    

    # Weighted
    # total_support = sum(supports[cls] for cls in valid_classes)

    # if total_support > 0:
    #     weighted_precision = sum(scores[cls]["precision"] * supports[cls] for cls in valid_classes) / total_support
    #     weighted_recall = sum(scores[cls]["recall"] * supports[cls] for cls in valid_classes) / total_support
    #     weighted_f1 = sum(scores[cls]["f1"] * supports[cls] for cls in valid_classes) / total_support
    # else:
    #     weighted_precision = weighted_recall = weighted_f1 = 0.0

    # print("---------------------------------------------------")
    # print("[Weighted]")
    # print("Weighted Precision:", weighted_precision)
    # print("Weighted Recall:", weighted_recall)
    # print("Weighted F1:", weighted_f1)
    # print("---------------------------------------------------")
    #print(pred_datas)

    fs.save_json(f"./gt/total_json/{file_name}.json", pred_datas)
    return pred_datas, micro_score, scores

def vlm_excel_process(save_excel_path, video_info : list, img_width, img_height):
    print("엑셀 제작 진입")
    #엑셀 연동하기
    excel_wb = Workbook()
    excel_mgr = excel_wb.active

    excel_header = ["IMAGE", "TIMESTAMP", "DESCRIPT", "CHANGE_DESCRIPT", "SCENE_CHANGE"]
    excel_mgr.append(excel_header)

    # img_col_size = config["img_width"] * 0.125
    # all_row_size = config["img_height"] * 0.75
    img_col_size = img_width * 0.125
    all_row_size = img_height * 0.75
    timestamp_col_size = 0
    descript_col_size = 0

    for idx, frame_info in enumerate(video_info):
        img_path = frame_info["img_path"]
        timestamp = frame_info["timestamp"]
        descript = frame_info["result"]
        change_descript = frame_info["change_result"]
        scene_change = frame_info["scene_change"]

        img = XLImage(img_path)
        img.width = img_width
        img.height = img_height
        img_col = 'A' + str(idx+2)
        excel_mgr.add_image(img, img_col)
        excel_mgr.append({'B':timestamp, 'C':descript,'D':change_descript ,'E':scene_change})

        if timestamp_col_size < len(timestamp):
            timestamp_col_size = len(timestamp)
        if descript_col_size < len(descript):
            descript_col_size = len(descript)

    timestamp_col_size = max(len(excel_header[1]), timestamp_col_size) * 1.2
    descript_col_size = max(len(excel_header[2]), descript_col_size) * 1.75

    excel_mgr.column_dimensions['A'].width = img_col_size
    excel_mgr.column_dimensions['B'].width = timestamp_col_size
    excel_mgr.column_dimensions['C'].width = descript_col_size
    excel_mgr.column_dimensions['D'].width = len(excel_header[3]) * 1.75
    excel_mgr.column_dimensions['E'].width = len(excel_header[4]) * 1.75
    for row_idx in range(2, excel_mgr.max_row + 1):
        excel_mgr.row_dimensions[row_idx].height = all_row_size

    excel_wb.save(filename=save_excel_path)

    print("엑셀 저장 완료")


def excel_process(save_excel_path, video_info : list, img_width, img_height, score, class_results):
    print("엑셀 제작 진입")
    #엑셀 연동하기
    excel_wb = Workbook()
    excel_mgr = excel_wb.active

    #excel_header = ["IMAGE", "TIMESTAMP", "DESCRIPT", "CHANGE_DESCRIPT", "SCENE_CHANGE", "GT_CHECK", "GT_TIME","GT_EVENTS","CHANGE_GT_EVENTS", "USE_SAMPLE" ]
    excel_header = ["IMAGE", "TIMESTAMP", "DESCRIPT", "CHANGE_DESCRIPT", "SCENE_CHANGE", "GT_CHECK", "GT_TIME","GT_EVENTS" ]
    excel_mgr.append(excel_header)

    # img_col_size = config["img_width"] * 0.125
    # all_row_size = config["img_height"] * 0.75
    img_col_size = img_width * 0.125
    all_row_size = img_height * 0.75
    timestamp_col_size = 0
    descript_col_size = 0

    for idx, frame_info in enumerate(video_info):
        img_path = frame_info["img_path"]
        timestamp = frame_info["timestamp"]
        descript = frame_info["result"]
        change_descript = frame_info["change_result"]
        scene_change = frame_info["scene_change"]
        GT_result = frame_info["GT_check"]
        GT_time = frame_info["GT_timestamp"]
        GT_event = frame_info["GT_descript"]
        #GT_change_event = frame_info["GT_change_descript"]
        #use_sample = frame_info["use_sample"]

        img = XLImage(img_path)
        img.width = img_width
        img.height = img_height
        img_col = 'A' + str(idx+2)
        excel_mgr.add_image(img, img_col)
        excel_mgr.append({'B':timestamp, 'C':descript,'D':change_descript ,'E':scene_change ,'F':GT_result, 'G':GT_time, 'H':GT_event })

        if timestamp_col_size < len(timestamp):
            timestamp_col_size = len(timestamp)
        if descript_col_size < len(descript):
            descript_col_size = len(descript)

    timestamp_col_size = max(len(excel_header[1]), timestamp_col_size) * 1.2
    descript_col_size = max(len(excel_header[2]), descript_col_size) * 1.75

    excel_mgr.column_dimensions['A'].width = img_col_size
    excel_mgr.column_dimensions['B'].width = timestamp_col_size
    excel_mgr.column_dimensions['C'].width = descript_col_size
    excel_mgr.column_dimensions['D'].width = len(excel_header[3]) * 1.75
    excel_mgr.column_dimensions['E'].width = len(excel_header[4]) * 1.75
    excel_mgr.column_dimensions['F'].width = len(excel_header[5]) * 1.75
    excel_mgr.column_dimensions['G'].width = len(excel_header[6]) * 1.75
    excel_mgr.column_dimensions['H'].width = len(excel_header[7]) * 1.75
    for row_idx in range(2, excel_mgr.max_row + 1):
        excel_mgr.row_dimensions[row_idx].height = all_row_size

    excel_wb.save(filename=save_excel_path)
    excel_wb.close()

    workbook = load_workbook(save_excel_path)
    total_score = workbook.create_sheet("total_score")

    total_header = ["TOTAL_SCORE", "EVENTS_SCORE", "CORRECT_SAMPLE_COUNT"]
    total_score.append(total_header)
    total_score['A2'] = f"precision_micro:{score['precision']}, \nrecall_micro:{score['recall']},\nmicro_f1_score:{score['micro_f1']}"
    total_score['B2'] = f"baby_sleep: {class_results['baby_sleep']['f1']}\nbaby_awake: {class_results['baby_awake']['f1']}\nbaby_crying: {class_results['baby_crying']['f1']}\nunknown: {class_results['unknown']['f1']}\nno_baby: {class_results['no_baby']['f1']}"
    total_score['C2'] = f"sleep Correct sample : {class_results['baby_sleep']['tp']}\nsleep inCorrect sample : {class_results['baby_sleep']['fp']}"
    total_score['C3'] = f"awake Correct sample : {class_results['baby_awake']['tp']}\nawake inCorrect sample : {class_results['baby_awake']['fp']}"
    total_score['C4'] = f"crying Correct sample : {class_results['baby_crying']['tp']}\ncrying inCorrect sample : {class_results['baby_crying']['fp']}"
    total_score['C5'] = f"unknown Correct sample : {class_results['unknown']['tp']}\nunknown inCorrect sample : {class_results['unknown']['fp']}"
    total_score['C6'] = f"nobaby Correct sample : {class_results['no_baby']['tp']}\nnobaby inCorrect sample : {class_results['no_baby']['fp']}"

    
    total_score.column_dimensions['A'].width = len(total_header[0]) * 1.75
    total_score.column_dimensions['B'].width = len(total_header[1]) * 1.75
    total_score.column_dimensions['C'].width = len(total_header[2]) * 1.75
    workbook.save(filename=save_excel_path)


    print("엑셀 저장 완료")

#sleep 평균 점수
sleep_correct_count = 0
sleep_count = 0

#awake 평균 점수
awake_correct_count = 0
awake_count = 0

#moving 평균 점수
#moving_correct_count = 0
#moving_count = 0

#crying 평균 점수
crying_correct_count = 0
crying_count = 0

#unknown 평균 점수
unknown_correct_count = 0
unknown_count = 0

#nobaby 평균 점수
nobaby_correct_count = 0
nobaby_count = 0

def make_total_excel_line(line_num, file_name, class_results, total_excel):
    
    global sleep_correct_count, sleep_count
    global awake_correct_count, awake_count
    #global moving_correct_count, moving_count
    global crying_correct_count, crying_count
    global unknown_correct_count, unknown_count
    global nobaby_correct_count, nobaby_count

    #sample_count = class_results["baby_sleep"]["tp"] + class_results["baby_sleep"]["fp"] + class_results["baby_awake"]["tp"] + class_results["baby_awake"]["fp"] + class_results["baby_crying"]["tp"] + class_results["baby_crying"]["fp"] + class_results["unknown"]["tp"] + class_results["unknown"]["fp"] + class_results["no_baby"]["tp"] + class_results["no_baby"]["fp"]
    sample_count = class_results["baby_sleep"]["tp"] + class_results["baby_sleep"]["fn"] + class_results["baby_awake"]["tp"] + class_results["baby_awake"]["fn"] + class_results["baby_crying"]["tp"] + class_results["baby_crying"]["fn"] + class_results["unknown"]["tp"] + class_results["unknown"]["fn"] + class_results["no_baby"]["tp"] + class_results["no_baby"]["fn"]    
    correct_count = class_results["baby_sleep"]["tp"] + class_results["baby_awake"]["tp"] + class_results["baby_crying"]["tp"] + class_results["unknown"]["tp"] + class_results["no_baby"]["tp"]
    
    #sleep_score = round((class_results["baby_sleep"]["tp"] / (class_results["baby_sleep"]["tp"]+ class_results["baby_sleep"]["fp"]))*100 if (class_results["baby_sleep"]["tp"]+ class_results["baby_sleep"]["fp"]) != 0 else 0, 2)
    #awake_score = round((class_results["baby_awake"]["tp"] / (class_results["baby_awake"]["tp"]+ class_results["baby_awake"]["fp"]))*100 if (class_results["baby_awake"]["tp"]+ class_results["baby_awake"]["fp"]) != 0 else 0, 2)
    #crying_score = round((class_results["baby_crying"]["tp"] / (class_results["baby_crying"]["tp"]+ class_results["baby_crying"]["fp"]))*100 if (class_results["baby_crying"]["tp"]+ class_results["baby_crying"]["fp"]) != 0 else 0, 2)
    #unknown_score = round((class_results["unknown"]["tp"] / (class_results["unknown"]["tp"]+ class_results["unknown"]["fp"]))*100 if (class_results["unknown"]["tp"]+ class_results["unknown"]["fp"]) != 0 else 0, 2)
    #nobaby_score = round((class_results["no_baby"]["tp"] / (class_results["no_baby"]["tp"]+ class_results["no_baby"]["fp"]))*100 if (class_results["no_baby"]["tp"]+ class_results["no_baby"]["fp"]) != 0 else 0, 2)

    sleep_score = round((class_results["baby_sleep"]["tp"] / (class_results["baby_sleep"]["tp"]+ class_results["baby_sleep"]["fn"]))*100 if (class_results["baby_sleep"]["tp"]+ class_results["baby_sleep"]["fn"]) != 0 else 0, 2)
    awake_score = round((class_results["baby_awake"]["tp"] / (class_results["baby_awake"]["tp"]+ class_results["baby_awake"]["fn"]))*100 if (class_results["baby_awake"]["tp"]+ class_results["baby_awake"]["fn"]) != 0 else 0, 2)
    crying_score = round((class_results["baby_crying"]["tp"] / (class_results["baby_crying"]["tp"]+ class_results["baby_crying"]["fn"]))*100 if (class_results["baby_crying"]["tp"]+ class_results["baby_crying"]["fn"]) != 0 else 0, 2)
    unknown_score = round((class_results["unknown"]["tp"] / (class_results["unknown"]["tp"]+ class_results["unknown"]["fn"]))*100 if (class_results["unknown"]["tp"]+ class_results["unknown"]["fn"]) != 0 else 0, 2)
    nobaby_score = round((class_results["no_baby"]["tp"] / (class_results["no_baby"]["tp"]+ class_results["no_baby"]["fn"]))*100 if (class_results["no_baby"]["tp"]+ class_results["no_baby"]["fn"]) != 0 else 0, 2)

    #moving_score = round((class_results["baby_moving"]["tp"] / (class_results["baby_moving"]["tp"]+ class_results["baby_moving"]["fp"]))*100 if (class_results["baby_moving"]["tp"]+ class_results["baby_moving"]["fp"]) != 0 else 0, 2)
    
    total_score = (correct_count/sample_count)*100

    #if class_results["baby_sleep"]["tp"] != 0 or class_results["baby_sleep"]["fp"] != 0:
    #    sleep_correct_count += class_results["baby_sleep"]["tp"]
    #    sleep_count += class_results["baby_sleep"]["tp"] + class_results["baby_sleep"]["fp"]

    if class_results["baby_sleep"]["tp"] != 0 or class_results["baby_sleep"]["fn"] != 0:
        sleep_correct_count += class_results["baby_sleep"]["tp"]
        sleep_count += class_results["baby_sleep"]["tp"] + class_results["baby_sleep"]["fn"]

    #if class_results["baby_awake"]["tp"] != 0 or class_results["baby_awake"]["fp"] != 0:
    #    awake_correct_count += class_results["baby_awake"]["tp"]
    #    awake_count += class_results["baby_awake"]["tp"] + class_results["baby_awake"]["fp"]

    if class_results["baby_awake"]["tp"] != 0 or class_results["baby_awake"]["fn"] != 0:
        awake_correct_count += class_results["baby_awake"]["tp"]
        awake_count += class_results["baby_awake"]["tp"] + class_results["baby_awake"]["fn"]

    #if class_results["baby_crying"]["tp"] != 0 or class_results["baby_crying"]["fp"] != 0:
    #    crying_correct_count += class_results["baby_crying"]["tp"]
    #    crying_count += class_results["baby_crying"]["tp"] + class_results["baby_crying"]["fp"]

    if class_results["baby_crying"]["tp"] != 0 or class_results["baby_crying"]["fn"] != 0:
        crying_correct_count += class_results["baby_crying"]["tp"]
        crying_count += class_results["baby_crying"]["tp"] + class_results["baby_crying"]["fn"]

    #if class_results["unknown"]["tp"] != 0 or class_results["unknown"]["fp"] != 0:
    #    unknown_correct_count += class_results["unknown"]["tp"]
    #    unknown_count += class_results["unknown"]["tp"] + class_results["unknown"]["fp"]

    if class_results["unknown"]["tp"] != 0 or class_results["unknown"]["fn"] != 0:
        unknown_correct_count += class_results["unknown"]["tp"]
        unknown_count += class_results["unknown"]["tp"] + class_results["unknown"]["fn"]

    #if class_results["no_baby"]["tp"] != 0 or class_results["no_baby"]["fp"] != 0:
    #    nobaby_correct_count += class_results["no_baby"]["tp"]
    #    nobaby_count += class_results["no_baby"]["tp"] + class_results["no_baby"]["fp"]

    if class_results["no_baby"]["tp"] != 0 or class_results["no_baby"]["fn"] != 0:
        nobaby_correct_count += class_results["no_baby"]["tp"]
        nobaby_count += class_results["no_baby"]["tp"] + class_results["no_baby"]["fn"]

    #if class_results["baby_moving"]["tp"] != 0 or class_results["baby_moving"]["fp"] != 0:
    #    moving_correct_count += class_results["baby_moving"]["tp"]
    #    moving_count += class_results["baby_moving"]["tp"] + class_results["baby_moving"]["fp"]

    if line_num == 1:
        total_excel.append(["VIDEO_NAME","SAMPLE_COUNT","SLEEP_CORRECT","SLEEP_INCORRECT","SLEEP_CORRECT_SCORE","AWAKE_CORRECT","AWAKE_INCORRECT","AWAKE_CORRECT_SCORE","CRYING_CORRECT","CRYING_INCORRECT","CRYING_CORRECT_SCORE","UNKNOWN_CORRECT","UNKNOWN_INCORRECT","UNKNOWN_CORRECT_SCORE","NOBABY_CORRECT","NOBABY_INCORRECT","NOBABY_CORRECT_SCORE", "TOTAL_CORRECT_SCORE"])
    ln = line_num + 1
    total_excel['A'+str(ln)] = file_name
    total_excel['B'+str(ln)] = sample_count
    total_excel['C'+str(ln)] = class_results["baby_sleep"]["tp"]
    #total_excel['D'+str(ln)] = class_results["baby_sleep"]["fp"]
    total_excel['D'+str(ln)] = class_results["baby_sleep"]["fn"]
    total_excel['E'+str(ln)] = sleep_score

    total_excel['F'+str(ln)] = class_results["baby_awake"]["tp"] 
    #total_excel['G'+str(ln)] = class_results["baby_awake"]["fp"]
    total_excel['G'+str(ln)] = class_results["baby_awake"]["fn"]
    total_excel['H'+str(ln)] = awake_score

    #total_excel['I'+str(ln)] = class_results["baby_moving"]["tp"] 
    #total_excel['J'+str(ln)] = class_results["baby_moving"]["fp"]
    #total_excel['K'+str(ln)] = moving_score

    total_excel['I'+str(ln)] = class_results["baby_crying"]["tp"] 
    #total_excel['J'+str(ln)] = class_results["baby_crying"]["fp"]
    total_excel['J'+str(ln)] = class_results["baby_crying"]["fn"]
    total_excel['K'+str(ln)] = crying_score

    total_excel['L'+str(ln)] = class_results["unknown"]["tp"]
    #total_excel['M'+str(ln)] = class_results["unknown"]["fp"] 
    total_excel['M'+str(ln)] = class_results["unknown"]["fn"] 
    total_excel['N'+str(ln)] = unknown_score

    total_excel['O'+str(ln)] = class_results["no_baby"]["tp"]
    #total_excel['P'+str(ln)] = class_results["no_baby"]["fp"]
    total_excel['P'+str(ln)] = class_results["no_baby"]["fn"]
    total_excel['Q'+str(ln)] = nobaby_score

    total_excel['R'+str(ln)] = round(total_score, 2)

    return sample_count, correct_count

if __name__ == "__main__":
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
    
    video_list = os.listdir("videos")

    video_process(video_list)
    line_num = 0
    total_excel_wb = Workbook()
    total_excel = total_excel_wb.active
    summary_total_excel_wb = Workbook()
    summary_total_excel_ws = summary_total_excel_wb.active
    avg_total_score = 0
    total_sample_count = 0
    total_correct_count = 0
    for video_file in video_list:
        
        video = video_file.split(".")
        file_name = video[0]
        
        gt_lg_root = f'{root_path}/gt/new_lguplus_gt'

        # file_name = "김_현0426_5"
        # gt 형식의 json 데이터를 1초 단위로 가공한 json 파일 생성
        gt_json_path = f'{gt_lg_root}/{file_name}.json'

        if not os.path.exists(gt_json_path):
            print("GT가 없는 영상입니다.")
            continue
        gt_to_pred_json(gt_json_path)

        # 비디오 필터링 평가
        gt_root = f'{root_path}/gt/json'
        gt_json_path = f'{gt_root}/{file_name}.json'
        gt_datas = fs.load_json(gt_json_path)
        # 예측 xlsx to json
        # pred_excel_path = f'{root_path}/results/excel/{file_name}.xlsx'
        # pred_datas = convert_infer_res_xlsx_to_json(pred_excel_path)
        pred_json_path = f'{root_path}/results/json/{file_name}.json'
        pred_datas = fs.load_json(pred_json_path)

        #change_pred(pred_datas)

        GT_start_time = time.time()

        video_infos, check_score, class_results = GT_check_process(pred_datas, gt_datas, file_name)

        GT_end_time = time.time()
        print(f"정확도 평가에 소요되는 시간은 {GT_end_time - GT_start_time:.2f}입니다.")

        excel_start_time = time.time()
        
        excel_root = f"results/excel"
        excel_path = f"{excel_root}/{file_name}.xlsx"
        #excel_process(excel_path, video_infos, 300, 200, check_score, class_results)

        excel_end_time = time.time()
        #print(f"엑셀 파일 생성에 소요되는 시간은 {excel_end_time - excel_start_time}")

        line_num += 1
        
        sleep_GT = class_results["baby_sleep"]["fn"]
        awake_Gt = class_results["baby_awake"]["fn"]
        Crying_GT = class_results["baby_crying"]["fn"]
        Unknown_GT = class_results["unknown"]["fn"]
        No_Baby_GT = class_results["no_baby"]["fn"]


        print(f"Sleep GT Incorrct: {sleep_GT}")
        print(f"Awake GT Incorrct: {awake_Gt}")
        print(f"Crying GT Incorrct: {Crying_GT}")
        print(f"Unknown GT Incorrct: {Unknown_GT}")
        print(f"No_Baby GT Incorrct: {No_Baby_GT}")
        
        sample_count, correct_count = make_total_excel_line(line_num, file_name, class_results, total_excel)
        #summary_total_excel(file_name, class_results, summary_total_excel_ws)

        total_sample_count += sample_count
        total_correct_count += correct_count

    avg_total_score = ((total_correct_count / total_sample_count) * 100 if (avg_total_score + line_num) != 0 else 0)

    sleep_avg_score = ((sleep_correct_count / sleep_count) * 100 if (sleep_correct_count + sleep_count) != 0 else 0)
    awake_avg_score = ((awake_correct_count / awake_count) * 100 if (awake_correct_count + awake_count) != 0 else 0)
    #moving_avg_score = ((moving_correct_count / moving_count) * 100 if (moving_correct_count + moving_count) != 0 else 0)
    crying_avg_score = ((crying_correct_count / crying_count) * 100 if (crying_correct_count + crying_count) != 0 else 0)
    unknown_avg_score =((unknown_correct_count / unknown_count) * 100 if (unknown_correct_count + unknown_count) != 0 else 0)
    nobaby_avg_score = ((nobaby_correct_count / nobaby_count) * 100 if (nobaby_correct_count + nobaby_count) != 0 else 0)

    total_excel["B"+str(line_num+3)] = f"총 정답율 : {avg_total_score}" 

    total_excel["B"+str(line_num+4)] = f"Sleep 전체 정답 비율 : {sleep_avg_score}" 
    total_excel["B"+str(line_num+5)] = f"Awake 전체 정답 비율 : {awake_avg_score}" 
    #total_excel["B"+str(line_num+6)] = f"Moving 전체 정답 비율 : {moving_avg_score}" 
    total_excel["B"+str(line_num+6)] = f"Crying 전체 정답 비율: {crying_avg_score}" 
    total_excel["B"+str(line_num+7)] = f"Unknown 전체 정답 비율 : {unknown_avg_score}" 
    total_excel["B"+str(line_num+8)] = f"No_Baby 전체 정답 비율 : {nobaby_avg_score}" 

    total_excel_wb.save(filename="results/excel/total_excel.xlsx")
    