#include <Arduino.h>
#include <BluetoothSerial.h>

#define RED_LED 22
#define BLUE_LED 1
#define GREEN_LED 3
#define BUTTON 23

#define t_servo 32  // Top flip/cover servo
#define b_servo 33  // Botton turn servo

#define SERVO_B 0
#define SERVO_T 2
#define FREQUENCY 50
#define RESOLUTION 10


const int max_500to2500us = 101;   //512  // Servo duty value for angle -100deg, beyond limit of a 0.5 to 2.5ms servo
const int min_500to2500us = 51;    //102.4  // Servo duty value for angle 100deg, beyond limit of a 0.5 to 2.5ms servo
const int mid_pos = 76;              // Servo duty value for angle 0deg, for 1to2ms and 0.5to2.5ms servo
const int mid_pos_CCW = 78;
const int mid_pos_CW = 74;

void swipe_and_center();

String remaining_moves1 = "";
BluetoothSerial SerialBT1;



void setup1() {  
    Serial.begin(9600);
    delay(4000);
    Serial.println("Start connectiong...");
    SerialBT1.begin("LolinD32");
    Serial.println("The device started, now you can pair it with bluetooth!");
    //remaining_moves1 = "a9b2c3d4e5f6g7h8i9j0";
}


void loop1() {
    if (SerialBT1.available()) {
        if (SerialBT1.readString() != "ping") {
            remaining_moves1 = SerialBT1.readString();
            Serial.println(remaining_moves1);
            Serial.println(remaining_moves1.length());
        }
    }

    if (remaining_moves1.length() > 0 && true) {
        digitalWrite(GREEN_LED, HIGH);
        Serial.println("Green ON");
        delay(500);
        Serial.println("Green OFF");
        digitalWrite(GREEN_LED, LOW);
        delay(500);
    }
}




/*
void setup2() {
    Serial.begin(9600);
    
    pinMode(RED_LED, OUTPUT);
    pinMode(BLUE_LED, OUTPUT);
    pinMode(GREEN_LED, OUTPUT);
    pinMode(BUTTON, INPUT_PULLDOWN);

    ledcSetup(SERVO_T, FREQUENCY, RESOLUTION);
    ledcAttachPin(t_servo, SERVO_T);              // Setup za gornji servo
    ledcSetup(SERVO_B, FREQUENCY, RESOLUTION);
    ledcAttachPin(b_servo, SERVO_B);              // Setup za donji servo

    delay(50);
    digitalWrite(RED_LED, HIGH);
    ledcWrite(SERVO_B, 76);         // Bottom servo in center position 0°
    ledcWrite(SERVO_T, 68);         // Center postion
}

void loop2() {
    if(digitalRead(BUTTON) == HIGH){
        digitalWrite(GREEN_LED, HIGH);
        ledcWrite(SERVO_B, min_500to2500us);     // CW position
        delay(700);
        ledcWrite(SERVO_T, 76);     // Home position
        delay(400);
        ledcWrite(SERVO_B, mid_pos_CCW);     // CCW position
        delay(700);
        ledcWrite(SERVO_B, mid_pos);     // Home position
        delay(100);
        ledcWrite(SERVO_T, 68);
        delay(400); 


        ledcWrite(SERVO_B, max_500to2500us);     // CW position
        delay(700);
        ledcWrite(SERVO_T, 76);     // Home position
        delay(400);
        ledcWrite(SERVO_B, mid_pos_CW);     // CCW position
        delay(700);
        ledcWrite(SERVO_B, mid_pos);     // Home position
        delay(100); 
        ledcWrite(SERVO_T, 67);
        delay(400);
        ledcWrite(SERVO_T, 68);
        delay(100);

        digitalWrite(GREEN_LED, LOW);
      }
}

void swipe_and_center() {
    ledcWrite(SERVO_T, 48);  // Set top servo to mid position
    ledcWrite(SERVO_B, mid_pos);  // Set bottom servo to mid position
    digitalWrite(GREEN_LED, HIGH);
    Serial.print("\nservos set to their middle position");
    delay(1200);  // Time for the servos to reach the mid position


    for (int i = mid_pos; i >= min_500to2500us; i--) {  // Swipe from mid to min position (CW)
        ledcWrite(SERVO_T, i);  // Set top servo to mid position
        ledcWrite(SERVO_B, i);
        Serial.print(i);
        delay(20);
    }
    delay(1000);

    for (int i = min_500to2500us; i <= max_500to2500us; i++) {  // Swipe from min to max position (CCW)
        ledcWrite(SERVO_B, i);
        delay(20);
    }
    delay(1000);

    for (int i = max_500to2500us; i >= mid_pos; i--) {  // Swipe from max to mid position
        ledcWrite(SERVO_B, i);
        delay(20);
    }

    digitalWrite(GREEN_LED, LOW);
}
*/