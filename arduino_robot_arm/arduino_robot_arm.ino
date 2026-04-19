#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// PCA9685 설정
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define SERVO_MIN  150 // 0도 펄스 (모터마다 다를 수 있음)
#define SERVO_MAX  600 // 180도 펄스
#define NUM_SERVOS 14

void setup() {
  Serial.begin(115200); // 파이썬 코드와 속도를 맞춥니다.
  pwm.begin();
  pwm.setPWMFreq(60);  // 서보 모터 주파수 60Hz
  delay(10);
  Serial.println("Robot Hand Ready!");
}

void loop() {
  // 바이너리 수신: 헤더(1) + 각도 14바이트 = 15바이트
  if (Serial.available() >= 15) {
    if (Serial.read() == 0x41) {  // 'A' sync
      for (int i = 0; i < NUM_SERVOS; i++) {
        int angle = Serial.read();
        int pulse = map(constrain(angle, 0, 180), 0, 180, SERVO_MIN, SERVO_MAX);
        pwm.setPWM(i, 0, pulse);
      }
    }
  }
}