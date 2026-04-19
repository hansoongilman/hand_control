# 손 동작 → 아두이노 로봇팔 제어 시스템

손 움직임을 실시간으로 감지하여 아두이노 로봇팔을 제어하는 프로젝트입니다.

## 필요한 것들

### Python (PC)
- Python 3.8 이상
- OpenCV (`pip install opencv-python`)
- MediaPipe (`pip install mediapipe`)
- PySerial (`pip install pyserial`)
- NumPy (`pip install numpy`)

### 아두이노
- 아두이노 보드 (Uno, Mega 등)
- 서보모터 6개 (SG90 또는 MG90S 권장)
- 점퍼 케이블
- 외부 전원 (5V, 최소 2A) - 서보모터가 많으면 필수!

## 아두이노 연결 방법

### 서보모터 핀 연결
```
서보모터       아두이노 핀
--------------------------
손목 (Wrist)  → 3번 핀
엄지 (Thumb)  → 5번 핀
검지 (Index)  → 6번 핀
중지 (Middle) → 9번 핀
약지 (Ring)   → 10번 핀
소지 (Pinky)  → 11번 핀

모든 서보 GND → GND
모든 서보 VCC → 5V (외부 전원 권장)
```

### 주의사항 
1. **서보모터 전원**: 서보 6개를 동시에 움직이면 아두이노 보드의 5V 핀으로는 전류가 부족합니다.
   - 외부 5V 전원을 사용하세요 (2A 이상)
   - GND는 아두이노와 외부 전원을 공통으로 연결하세요

2. **핀 번호 변경**: `arduino_robot_arm.ino` 파일에서 사용하는 핀 번호를 수정할 수 있습니다:
   ```cpp
   const int PIN_WRIST = 3;   // 원하는 핀 번호로 변경
   const int PIN_THUMB = 5;
   // ...
   ```

## 사용 방법

### 1단계: 아두이노 업로드
1. Arduino IDE를 엽니다
2. `arduino_robot_arm.ino` 파일을 엽니다
3. 보드와 포트를 선택합니다 (도구 > 보드 / 도구 > 포트)
4. 업로드 버튼을 누릅니다

### 2단계: Python 설정
`hand_to_arduino.py` 파일을 열고 설정을 수정합니다:

```python
# 아두이노 포트 설정
ARDUINO_PORT = "COM3"  # Windows: COM3, COM4 등
                       # Mac: /dev/cu.usbmodem14101 등
                       # Linux: /dev/ttyUSB0, /dev/ttyACM0 등

# 아두이노 연결 여부
USE_SERIAL = True  # 아두이노 있으면 True, 없으면 False
```

### 3단계: 실행
```bash
python hand_to_arduino.py
```

## 데이터 형식

Python → Arduino로 전송되는 데이터:
```
W90,T120,I150,M140,R130,P110\n
```

- W: Wrist (손목 회전) 0-180도
- T: Thumb (엄지) 0-180도
- I: Index (검지) 0-180도
- M: Middle (중지) 0-180도
- R: Ring (약지) 0-180도
- P: Pinky (소지) 0-180도

## 디버깅

### 아두이노 없이 테스트
```python
USE_SERIAL = False  # 이렇게 설정
```
시뮬레이션 화면에서 각도 값만 확인할 수 있습니다.

### 시리얼 모니터로 확인
Arduino IDE에서 시리얼 모니터를 열면 (도구 > 시리얼 모니터):
```
Arduino Robot Arm Ready!
Received: W90,T120,I150,M140,R130,P110
Received: W92,T118,I152,M138,R128,P112
...
```

### 포트 찾기
**Windows:**
- 장치 관리자 → 포트(COM & LPT) 확인

**Mac/Linux:**
```bash
# Mac
ls /dev/cu.*

# Linux
ls /dev/ttyUSB* /dev/ttyACM*
```

## 사용 팁

1. **손 위치**: 카메라에서 50cm 정도 떨어진 곳에서 손을 펼치세요
2. **조명**: 밝은 곳에서 사용하면 인식률이 좋습니다
3. **각도 조정**: 서보모터가 반대로 움직이면 아두이노 코드에서 각도 반전:
   ```cpp
   angle = 180 - angle;  // 방향 반전
   ```

## 문제 해결

### "포트를 열 수 없습니다"
- 아두이노가 연결되어 있는지 확인
- 포트 번호가 맞는지 확인
- 다른 프로그램(Arduino IDE 시리얼 모니터 등)이 포트를 사용 중인지 확인

### 서보가 떨림
- 외부 전원 사용
- 전송 속도 조정: `SEND_INTERVAL = 0.1`로 늘리기

### 손 인식 안 됨
- 조명 확인
- 카메라 각도 조정
- 손을 카메라 중앙에 위치

##  커스터마이징

### 각도 보정
손가락이 너무 많이/적게 움직이면 `calculate_finger_angles()` 함수에서 조정:
```python
# 각도 범위 조정
angles[finger_name] = int((180 - angle) * 1.5)  # 1.5배 증폭
angles[finger_name] = np.clip(angles[finger_name], 0, 180)
```

### 전송 속도 변경
```python
SEND_INTERVAL = 0.05  # 50ms (20Hz)
# 값을 늘리면 느려지고, 줄이면 빨라집니다
```

##  작동 원리

1. **손 감지**: MediaPipe로 손의 21개 랜드마크 추적
2. **각도 계산**: 각 손가락의 펼침 정도를 0-180도로 변환
3. **시리얼 전송**: 50ms마다 아두이노로 각도 데이터 전송
4. **서보 제어**: 아두이노가 받은 각도로 서보모터 제어

##  파일 구성

```
hand_to_arduino.py          # Python 메인 코드
arduino_robot_arm.ino       # 아두이노 코드
hand_landmarker.task        # MediaPipe 모델 (자동 다운로드)
README.md                   # 이 파일
```

##  확장 아이디어

- 손가락 개별 제어가 아닌 손 포즈 인식
- 물건 잡기/놓기 동작 추가
- 양손 사용으로 2개 로봇팔 제어
- Bluetooth 무선 통신으로 변경

---

문제가 생기면 시리얼 모니터와 Python 터미널의 출력을 확인하세요!
echo "# hand_control" >> README.md
