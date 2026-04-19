import os
import struct
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python.core import base_options as base_options_lib
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
import serial
import time
import math

# --- 설정 ---
ARDUINO_PORT = "COM3"  # 아두이노 연결된 포트에 맞게 수정 (예: COM3, COM4)
BAUD_RATE = 115200 
USE_SERIAL = True   # 실제 아두이노 연결 시 True로 변경

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
SIM_W, SIM_H = 600, 700 

def get_angle_abc(a, b, c):
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6: return 0
    cosine_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    angle = math.degrees(math.acos(np.clip(cosine_angle, -1.0, 1.0)))
    return int(180 - angle)

def calculate_detailed_angles(pts):
    if not pts or len(pts) < 21: return None
    
    # 순서대로: 엄지(2), 검지(3), 중지(3), 약지(3), 소지(3) = 총 14개
    angle_data = {
        "Thumb_MCP": get_angle_abc(pts[1], pts[2], pts[3]),
        "Thumb_IP":  get_angle_abc(pts[2], pts[3], pts[4]),
        "Index_MCP": get_angle_abc(pts[0], pts[5], pts[6]),
        "Index_PIP": get_angle_abc(pts[5], pts[6], pts[7]),
        "Index_DIP": get_angle_abc(pts[6], pts[7], pts[8]),
        "Middle_MCP":get_angle_abc(pts[0], pts[9], pts[10]),
        "Middle_PIP":get_angle_abc(pts[9], pts[10], pts[11]),
        "Middle_DIP":get_angle_abc(pts[10], pts[11], pts[12]),
        "Ring_MCP":  get_angle_abc(pts[0], pts[13], pts[14]),
        "Ring_PIP":  get_angle_abc(pts[13], pts[14], pts[15]),
        "Ring_DIP":  get_angle_abc(pts[14], pts[15], pts[16]),
        "Pinky_MCP": get_angle_abc(pts[0], pts[17], pts[18]),
        "Pinky_PIP": get_angle_abc(pts[17], pts[18], pts[19]),
        "Pinky_DIP": get_angle_abc(pts[18], pts[19], pts[20]),
    }
    return angle_data

def draw_ui(canvas, angle_data, pts_world):
    offset_x, offset_y = SIM_W // 2, 250
    scale = 1200
    connections = [
        (0,1),(1,2),(2,3),(3,4), (0,5),(5,6),(6,7),(7,8),
        (0,9),(9,10),(10,11),(11,12), (0,13),(13,14),(14,15),(15,16),
        (0,17),(17,18),(18,19),(19,20), (5,9),(9,13),(13,17)
    ]
    for start, end in connections:
        p1 = (int(pts_world[start][0] * scale + offset_x), int(pts_world[start][1] * scale + offset_y))
        p2 = (int(pts_world[end][0] * scale + offset_x), int(pts_world[end][1] * scale + offset_y))
        cv2.line(canvas, p1, p2, (150, 150, 150), 2)

    y_start = 450
    cv2.rectangle(canvas, (20, y_start-30), (SIM_W-20, SIM_H-20), (40, 40, 40), -1)
    for i, (name, val) in enumerate(angle_data.items()):
        col, row = i // 7, i % 7
        x_pos, y_pos = 50 + (col * 280), y_start + (row * 35)
        color = (150, 255, 150) if val > 30 else (200, 200, 200)
        cv2.putText(canvas, f"{name}:", (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        cv2.putText(canvas, f"{val} deg", (x_pos + 130, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

def run_tracker():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "hand_landmarker.task")
    if not os.path.exists(model_path): urllib.request.urlretrieve(MODEL_URL, model_path)

    options = HandLandmarkerOptions(
        base_options=base_options_lib.BaseOptions(model_asset_path=model_path),
        num_hands=1, min_hand_detection_confidence=0.5,
    )
    landmarker = HandLandmarker.create_from_options(options)
    
    # --- 시리얼 초기화 ---
    ser = None
    if USE_SERIAL:
        try:
            ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2) # 아두이노 리셋 대기
            print(f"아두이노 연결 성공: {ARDUINO_PORT}")
        except Exception as e:
            print(f"시리얼 연결 실패: {e}")

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

        sim_canvas = np.zeros((SIM_H, SIM_W, 3), dtype=np.uint8)
        sim_canvas[:] = (30, 30, 30)

        if result.hand_world_landmarks:
            pts_world = [(lm.x, lm.y, lm.z) for lm in result.hand_world_landmarks[0]]
            angle_data = calculate_detailed_angles(pts_world)
            print(f"발사 데이터: {list(angle_data.values())}", flush=True)
            draw_ui(sim_canvas, angle_data, pts_world)
            
            # --- 아두이노 전송 로직 (binary) ---
            angle_list = list(angle_data.values())
            if USE_SERIAL and ser is not None:
                # 바이너리: 0x41(헤더) + 14바이트 각도(0~180, uint8)
                angles_clamped = [min(180, max(0, a)) for a in angle_list]
                data_bytes = struct.pack('B' + 'B' * len(angles_clamped), 0x41, *angles_clamped)
                ser.write(data_bytes)

        cv2.imshow("Robot Hand Status", sim_canvas)
        if cv2.waitKey(1) & 0xFF == 27: break

    if ser: ser.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_tracker()