import os
import cv2
import time
import numpy as np
from skimage.metrics import structural_similarity as ssim

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

def is_different_diff(f1, f2, threshold=1.3):  # threshold는 mean 차이 30
    diff = cv2.absdiff(f1, f2)
    mean_diff = np.mean(diff)
    return mean_diff > threshold

    # # 그레이스케일로 변환 (채널 통합)
    # if len(diff.shape) == 3:
    #     diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    # else:
    #     diff_gray = diff

    # # threshold 이상 차이나는 부분만 감지
    # _, diff_mask = cv2.threshold(diff_gray, 20, 255, cv2.THRESH_BINARY)

    # # 마스크를 색상으로 바꿈 (예: 빨간색)
    # color_mask = np.zeros_like(f1)
    # color_mask[diff_mask > 0] = [0, 0, 255]  # 빨간색 (BGR)

    # # 원본 이미지에 overlay
    # vis_image = cv2.addWeighted(f1, 0.7, color_mask, 0.3, 0)

    # return mean_diff > threshold, vis_image, diff_mask

def is_different_ssim(f1, f2, threshold=0.97):  # SSIM은 0~1, 1은 완전히 동일 0.85
    gray1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(gray1, gray2, full=True)
    return score < threshold

def video_filtering(file_name:str, sampling_type="diff", sampling_time=1):
    # file_name = "baby_test_video(LGU+2)"
    # sampling_type = "diff"
    # sampling_type = "ssim"
    # sampling_time = 1

    cap = cv2.VideoCapture(f"videos/{file_name}.mp4")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = int(total_frames / fps)
    saved_frames = []

    prev_frame = None
    cnt = 0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"원본 해상도: {width} x {height}")

    save_root = f"results/filtered_imgs/{file_name}/{sampling_type}"
    os.makedirs(save_root, exist_ok=True)

    start_time = time.time()
    for sec in range(0, duration_sec, sampling_time):
        frame_number = int(sec * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (850, 480))

        is_save_frame = False
        overlay = None
        mask = None

        if prev_frame is None:
            is_save_frame = True
        else:
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
            if sampling_type == "diff":
                is_diff = is_different_diff(prev_frame, frame)
            elif sampling_type == "ssim":
                is_diff = is_different_ssim(prev_frame, frame)
            if is_diff == True:
                is_save_frame = True
        
        if is_save_frame:
            saved_frames.append(frame_number)
            # prev_frame = frame
            save_frame = cv2.resize(frame, (width, height))
            imwrite(f"{save_root}/{file_name}_{sec}.jpg", frame)
            # imwrite(f"{save_root}/{file_name}_{sec}_overlay.jpg", overlay)
            # imwrite(f"{save_root}/{file_name}_{sec}_mask.jpg", mask)

        prev_frame = frame
        print(f"{sec + 1}/{duration_sec}초 처리 완료")
        cnt += 1

    cap.release()

    elapsed = time.time() - start_time
    print(f"[{sampling_type} 방식] 저장된 주요 프레임 수: {len(saved_frames)}")
    print(f"[{sampling_type} 방식] 처리 시간: {elapsed:.2f}초")
