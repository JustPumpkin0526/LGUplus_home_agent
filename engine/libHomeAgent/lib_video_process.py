from engine.libHomeAgent.import_lib import *

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

from library.vlm_inference_client import infer_from_server_with_image_object
from library.textsimilarity import get_similarity

from sentence_transformers import SentenceTransformer

# Load Model
device = "cuda:0"
model_sentence = SentenceTransformer('./model_clone/ko-sroberta-multitask', device=device)

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

#엑셀의 셀을 이미지 크기에 맞게 변환하기 위해 크기를 조정하는 코드
def get_excel_img_size(img_width, img_height):
    col_width = img_width*31.5/252.19
    row_height = img_height*149.1/198.96
    return (col_width, row_height)

#타임 스탬프 구하기
def get_timestamp_from_sec(sec):
    second = sec%60
    minute = (sec//60)%60 
    hour = sec//60//60

    timestamp = f"{hour:02d}:{minute:02d}:{second:02d}"
    return timestamp

def get_sec_from_timestamp(timestamp:str):
    h, m, s = map(int, timestamp.split(":"))
    total_seconds = h * 3600 + m * 60 + s
    return total_seconds

#프레임별 추출한 이미지 담을 폴더 생성
def create_image_save_folders(file_path):
    folder_path = Path(file_path).parent
    file_name = Path(file_path).stem
    folder_path = Path(f"{folder_path}/{file_name}")
    print(folder_path)
    if folder_path.exists() and folder_path.is_dir():
        files = list(folder_path.iterdir())
        files = [file for file in files if file.is_file()]
        for file in files:
            file.unlink()
    else:
        os.makedirs(folder_path)

def video_sampling(video_file_path, save_root, interval, b_save=True):
    file_name = Path(video_file_path).stem
    folder_path = Path(video_file_path).parent
    video_info = []

    #영상 불러오기
    print(video_file_path, flush=True)
    video = cv2.VideoCapture(video_file_path)

    if not video.isOpened():
        print("열리지 않는 파일")
        return video_info
 
    count = 1
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / fps  # 총 영상 시간 (초)
    # interval = config["interval"] * 1000  # 10초 간격 (ms)
    interval = interval * 1000  # 10초 간격 (ms)

    current_time = 0 #3240000

    if b_save:
        save_dst_path = f"{save_root}/{file_name}"
        create_image_save_folders(save_dst_path)

    print(duration, interval, flush=True)
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

def load_sampled_video(root_path:str):
    img_paths = list(Path(root_path).iterdir())
    print(len(img_paths))
    img_paths = sorted_data = sorted(img_paths, key=lambda x: int(x.stem.split('_')[-1]))

    video_info = []
    for img_path in img_paths:
        img_path = Path(img_path)
        file_name = img_path.stem
        sec = re.split(r'[_]', file_name)[-1]
        timestamp_str = get_timestamp_from_sec(int(sec))
        video_info.append({"img_path":img_path, "timestamp":timestamp_str})
        print(img_path)

    return video_info

def vlm_video_process(model, url : str, prompt :str, video_infos):
    for idx, video_info in enumerate(video_infos):
        frame_path = video_info["img_path"]
        request_img = Image.open(frame_path)
        
        # 이전 프롬포트:아기가 잠을 자는 중인가요? 잠을 자는 중이 아니라면 무슨 행동을 하고있나요?, 아기 상황을 설명해주세요
        start_time = time.time()
        # result = infer_from_server_with_image_object(config["url"], request_img, config["prompt"], config["model"])
        result = infer_from_server_with_image_object(url, request_img, prompt, model)
        end_time = time.time()
        print(idx, frame_path, flush=True)
        print(result, flush=True)
        video_info["result"] = result["result"]
        # print(f"vlm 요청 시간은 {end_time - start_time:.5f}초 입니다.")
        # print(result)
    
    return video_infos

def vlm_image_process(model, url : str, prompt :str, img_info):
    frame_path = img_info["img_path"]
    request_img = Image.open(frame_path)
    
    # 이전 프롬포트:아기가 잠을 자는 중인가요? 잠을 자는 중이 아니라면 무슨 행동을 하고있나요?, 아기 상황을 설명해주세요
    start_time = time.time()
    # result = infer_from_server_with_image_object(config["url"], request_img, config["prompt"], config["model"])
    result = infer_from_server_with_image_object(url, request_img, prompt, model)
    end_time = time.time()
    print(0, frame_path, flush=True)
    print(result, flush=True)
    img_info["result"] = result["result"]
    # print(f"vlm 요청 시간은 {end_time - start_time:.5f}초 입니다.")
    # print(result)

    return img_info

def excel_process(save_excel_path, video_info : list, img_width, img_height):
    #엑셀 연동하기
    excel_wb = Workbook()
    excel_mgr = excel_wb.active

    excel_header = ["IMAGE", "TIMESTAMP", "DESCRIPT", "SCORE", "CHANGE2", "CHANGE"]
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

        img = XLImage(img_path)
        img.width = img_width
        img.height = img_height
        img_col = 'A' + str(idx+2)
        excel_mgr.add_image(img, img_col)
        excel_mgr.append({'B':timestamp, 'C':descript})

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
    for row_idx in range(2, excel_mgr.max_row + 1):
        excel_mgr.row_dimensions[row_idx].height = all_row_size
    
    excel_wb.save(filename=save_excel_path)

def descript_similarity_process(excel_path):
    # result 시트 생성
    excel_wb = load_workbook(excel_path)
    origin_sheet = excel_wb["Sheet"]

    # descript 유사도 측정

    # 첫번째 프레임은 항상 O
    origin_sheet['D'+str(2)] = 1.0
    origin_sheet['E'+str(2)] = "O"
    
    for row_idx in range(2, origin_sheet.max_row):
        descript_src = str(origin_sheet['C'+str(row_idx)].value)
        descript_trg = str(origin_sheet['C'+str(row_idx + 1)].value)

        score = get_similarity(model_sentence, descript_src, descript_trg)

        origin_sheet['D'+str(row_idx+1)] = score
        origin_sheet['E'+str(row_idx+1)] = "X" if score > 0.7 else "O"

        # keyword description 생성 시
        if "SLEEP" in descript_src.upper():
            descript_src = "SLEEP"
        else:
            descript_src = "AWAKE"
        if "SLEEP" in descript_trg.upper():
            descript_trg = "SLEEP"
        else:
            descript_trg = "AWAKE"
        origin_sheet['F'+str(row_idx+1)] = "X" if descript_src != descript_trg else "O"


    # 새 시트 생성
    result = excel_wb.create_sheet(title="result")

    # 열 너비 복사
    for col in origin_sheet.columns:
        col_letter = get_column_letter(col[0].column)
        result.column_dimensions[col_letter].width = origin_sheet.column_dimensions[col_letter].width

    # 타이틀 복사
    for col_idx, cell in enumerate(origin_sheet[1], start=1):
        result.cell(row=1, column=col_idx, value=cell.value)
    result.row_dimensions[1].height = origin_sheet.row_dimensions[1].height

    # A열 이미지만 수집: {행 번호: 이미지}
    image_map = {
        img.anchor._from.row + 1: img
        for img in origin_sheet._images if img.anchor._from.col == 0
    }

    result_row = 2
    max_row = origin_sheet.max_row

    for i in range(2, max_row):
        if i == 2 or origin_sheet[f'E{i}'].value == "O":
            cur_row = i

            # 행 높이 복사
            result.row_dimensions[result_row].height = origin_sheet.row_dimensions[cur_row].height

            # 셀 값 복사
            for col in range(1, origin_sheet.max_column + 1):
                if cur_row == 2:
                    if col == 4:
                        result.cell(row=result_row, column=col, value=1.0)
                    if col == 5:
                        result.cell(row=result_row, column=col, value="O")
                    else:
                        cell = origin_sheet.cell(row=cur_row, column=col)
                        result.cell(row=result_row, column=col, value=cell.value)
                else:
                    cell = origin_sheet.cell(row=cur_row, column=col)
                    result.cell(row=result_row, column=col, value=cell.value)

            # A열 이미지 복사 (있으면)
            if cur_row in image_map:
                img = image_map[cur_row]
                anchor = copy.deepcopy(img.anchor)

                img_data = img.ref
                if hasattr(img_data, "seek"):
                    img_data.seek(0)
                pil_img = Image.open(img_data)

                buf = io.BytesIO()
                pil_img.save(buf, format='PNG')
                buf.seek(0)

                new_img = XLImage(buf)
                new_img.anchor = anchor
                new_img.anchor._from.row = result_row - 1
                result.add_image(new_img)

            result_row += 1

    excel_wb.save(filename=excel_path)

def test_text_similarity(text1 : str, text2 : str):
    score = get_similarity(model_sentence, text1, text2)
    return score
