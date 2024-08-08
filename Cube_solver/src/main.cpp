#include <Arduino.h>
#include <string>
#include <BluetoothSerial.h>

#define RED_LED 22
#define BLUE_LED 1
#define GREEN_LED 3
#define BUTTON 23

#define t_servo 32  // Top flip/cover servo
#define b_servo 33  // Botton turn servo

#define SERVO_B 0
#define SERVO_T 1
#define FREQUENCY 50
#define RESOLUTION 10

// Pulse width range: 0.5～2.5ms 
// Servo duty value za -90deg | resoluiton * max_PW / frequency = 2^10 * 2.5ms / (1/50Hz / 10^(-3))
// Servo duty value za 90deg  | resoluiton * min_PW / frequency
// Servo duty value za 0deg   | resoluiton * mid_PW / frequency

// Preset vrijednosti za upravljanje servo motorima
const int t_servo_flip = 54;         // top servo position to flip the cube
const int t_servo_open = 68;         // top servo position to free up the top cover from the cube, and keep the lifter out of the way
const int t_servo_close = 76;            // top servo position to constrain the cube mid and top layer
const int t_flip_to_close_time = 800;         // time needed to the servo to lower the cover/flipper from flip to close position
const int t_close_to_flip_time = 1000;        // time needed to the servo to raise the cover/flipper from close to flip position
const int t_flip_open_time = 600;             // time needed to the servo to raise/lower the flipper between open and flip positions
const int t_open_close_time = 400;            // time needed to the servo to raise/lower the flipper between open and close positions

const int b_servo_CCW = 51;                   // bottom servo position when fully CW 
const int b_home = 76;                        // bottom servo home position
const int b_servo_CW = 101;                   // bottom servo position when fully CCW
const int b_spin_time = 800;                 // time needed to the bottom servo to spin about 90deg
const int b_rotate_time = 800;               // time needed to the bottom servo to rotate about 90deg
const int b_rel_time = 100;                   // time needed to the servo to rotate slightly back, to release tensions

const int b_home_from_CW = b_home - 2;        // bottom servo extra home position, when moving back from full CW
const int b_home_from_CCW = b_home + 2;       // bottom servo extra home position, when moving back from full CCW


int t_top_cover = 1;           // Stanje gornjeg servo motora (0 - closed, 1 - open, 2 - flip) 
bool b_servo_operable = true;  // Varijabla za blokiranje/dopuštanje rada donjeg servo motora 
bool b_servo_stopped = true;   // Varijabla pozicije donjeg servo motora za omogućavanje kretanja gornjeg servo motora  
bool b_servo_home = true;      // Varijabla za poziciju donjeg servo motora na 0°
bool b_servo_CW_pos = false;   // Varijabla za poziciju donjeg servo motora na 90°
bool b_servo_CCW_pos = false;  // Varijabla za poziciju donjeg servo motora na -90°
bool stop_servos = true;

// Funckije
void customDelay(unsigned long delayTime);
void flip_up();
void flip_to_open();
void flip_to_close();
void open_cover();
void close_cover();
void spin_out(String direction);
void spin_home();
void rotate_home(String direction);
void rotate_out(String direction);
void servo_solve_cube(String moves);

String remaining_moves = "";   // Global variable to store remaining moves

BluetoothSerial SerialBT;

unsigned long previousMillis = 0;
const long interval = 50; // interval for checking the button


void setup() {
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
    ledcWrite(SERVO_B, 76);
    ledcWrite(SERVO_T, 68);

    delay(4000);

    SerialBT.begin("LolinD32");

}

void loop() {
    if (SerialBT.hasClient()) {
        digitalWrite(BLUE_LED, HIGH);
    }
    else {
        digitalWrite(BLUE_LED, LOW);
    }
    
    if (SerialBT.available()) {
        remaining_moves = SerialBT.readString();
    }

    if (digitalRead(BUTTON) == HIGH && remaining_moves.length() > 0) {
            stop_servos = !stop_servos;  // Toggle the stop_servos variable
            delay(200);  // Debounce delay

        }

    if (!stop_servos && remaining_moves.length() > 0) {
            digitalWrite(GREEN_LED, HIGH);
            servo_solve_cube(remaining_moves);
        }

    if (remaining_moves.length() > 0 && stop_servos) {
        digitalWrite(GREEN_LED, HIGH);
        customDelay(500);
        digitalWrite(GREEN_LED, LOW);
        customDelay(500);
    }

    if (remaining_moves.length() == 0) {
        stop_servos = true;
        digitalWrite(GREEN_LED, LOW);
    }
   
}

// Delay koji ne blokira ostale naredbe
void customDelay(unsigned long delayTime) {
    unsigned long startTime = millis();
    while (millis() - startTime < delayTime) {
        unsigned long currentMillis = millis();
        if (currentMillis - previousMillis >= interval) {
            previousMillis = currentMillis;
            if (digitalRead(BUTTON) == HIGH) {
                stop_servos = !stop_servos;
                delay(200); // debounce delay
            }
        }
    }
}


void flip_up() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        if (t_top_cover == 0) {
            ledcWrite(SERVO_T, t_servo_flip);
            customDelay(t_close_to_flip_time);
        } else if (t_top_cover == 1) {
            ledcWrite(SERVO_T, t_servo_flip);
            customDelay(t_flip_open_time);
        }
        t_top_cover = 2;
    }
}

void flip_to_open() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        ledcWrite(SERVO_T, t_servo_open);
        customDelay(t_flip_open_time);
        t_top_cover = 1;
        b_servo_operable = true;
    }
    
}

void flip_to_close() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        ledcWrite(SERVO_T, t_servo_close);
        if (t_top_cover == 2) {
            customDelay(t_flip_to_close_time);
        } else if (t_top_cover == 1) {
            customDelay(t_open_close_time);
        }
        t_top_cover = 0;
        b_servo_operable = true;
    }
}

void open_cover() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        ledcWrite(SERVO_T, t_servo_open);
        customDelay(t_open_close_time);
        t_top_cover = 1;
        b_servo_operable = true;
    }
}

void close_cover() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        ledcWrite(SERVO_T, t_servo_close);
        delay(t_open_close_time);
        t_top_cover = 0;
        b_servo_operable = true;
    }
}

void spin_out(String direction) {
    if (b_servo_operable) {
        if (b_servo_home) {
            if (t_top_cover != 1) {
                flip_to_open();
            }

            b_servo_stopped = false;
            b_servo_CW_pos = false;
            b_servo_CCW_pos = false;

            if (direction == "CCW") {
                ledcWrite(SERVO_B, b_servo_CCW);
                customDelay(b_spin_time);
                b_servo_CCW_pos = true;
            } else if (direction == "CW") {
                ledcWrite(SERVO_B, b_servo_CW);
                customDelay(b_spin_time);
                b_servo_CW_pos = true;
            }
            b_servo_stopped = true;
            b_servo_home = false;
        }
    }
}

void spin_home() {
    if (b_servo_home == false) {
        if (t_top_cover != 1) {
                open_cover();
            }
        b_servo_stopped = false;
        ledcWrite(SERVO_B, b_home);
        customDelay(b_spin_time);
        b_servo_stopped = true;
        b_servo_home = true;
        b_servo_CW_pos = false;
        b_servo_CCW_pos = false;
    }
}

void rotate_home(String direction) {
    if (b_servo_operable) {
        if (!b_servo_home) {
            if (t_top_cover != 0) {
                b_servo_stopped = true;
                close_cover();
                b_servo_stopped = false;
            }
            if (direction == "CCW") {
                if (b_servo_CW_pos) {
                    ledcWrite(SERVO_B, b_home_from_CW);
                }
            } else if (direction == "CW") {
                if (b_servo_CCW_pos) {
                    ledcWrite(SERVO_B, b_home_from_CCW);
                }
            }
            customDelay(b_rotate_time);
            ledcWrite(SERVO_B, b_home);
            customDelay(b_rel_time);
            b_servo_stopped = true;
            b_servo_home = true;
            b_servo_CW_pos = false;
            b_servo_CCW_pos = false;
            open_cover();
        }
    }
}

void rotate_out(String direction) {
    if (b_servo_operable) {
        if (b_servo_home) {
            if (t_top_cover != 1) {
                flip_to_open();
            }

            b_servo_stopped = false;
            if (direction == "CCW") {
                ledcWrite(SERVO_B, b_servo_CW);
                customDelay(b_rotate_time);
                b_servo_CW_pos = true;
                b_servo_home = false;
                rotate_home(direction);
            } 
            
            else if (direction == "CW") {
                ledcWrite(SERVO_B, b_servo_CCW);
                customDelay(b_rotate_time);
                b_servo_CCW_pos = true;
                b_servo_home = false;
                rotate_home(direction);
            }
        }
    }
}


void servo_solve_cube(String moves) {
    // Function that translates the received string of moves, into servos sequence activations.
    // This is substantially the main function.

    int string_len = moves.length();  // number of characters in the moves string

    for (int i = 0; i < string_len; i++) {  // iteration over the characters of the moves string
        if (stop_servos) {                                  // case there is a stop request for servos
            break;
        }
        if (moves[i] == 'F') {  // case there is a flip on the move string
            int flips = moves[i + 1] - '0';  // number of flips

            for (int flip = 0; flip < flips; flip++) {  // iterates over the number of requested flips
                if (stop_servos) {                      // case there is a stop request for servos
                    break;
                }

                flip_up();  // lifter is operated to flip the cube

                if (flip < (flips - 1)) {  // case there are further flippings to do
                    flip_to_open();  // lifter is lowered stopping the top cover in open position (cube not constrained)
                    remaining_moves[1] -= 1; // counter is decreased
                }

                if (flip == (flips - 1) && string_len - (i + 2) > 0) {  // case it's the last flip and there is a following command on the move string
                    if (moves[i + 2] == 'R') {  // case the next action is a 1st layer cube rotation
                        flip_to_close();  // top cover is lowered to close position
                    } else if (moves[i + 2] == 'S') {  // case the next action is a cube spin
                        flip_to_open();  // top cover is lowered to open position
                    }
                    remaining_moves.remove(0, 2);
                }
            }

        } 
        
        else if (moves[i] == 'S') {  // case there is a cube spin on the move string
            int direction = moves[i + 1] - '0';  // rotation direction is retrieved

            String set_dir;
            if (direction == 3) {  // case the direction is CCW
                set_dir = "CCW";  // CCW direction is assigned to the variable
            } else {  // case the direction is CW
                set_dir = "CW";  // CW direction is assigned to the variable
            }

            if (b_servo_home) {  // case bottom servo is at home
                spin_out(set_dir);  // call to function to spin the full cube to full CW or CCW
                remaining_moves.remove(0, 2);
            } else if (b_servo_CW_pos || b_servo_CCW_pos) {  // case the bottom servo is at full CW or CCW position
                spin_home();  // call to function to spin the full cube toward home position
                remaining_moves.remove(0, 2);
            }


        } else if (moves[i] == 'R') {  // case there is a cube 1st layer rotation
            int direction = moves[i + 1] - '0';  // rotation direction is retrieved

            String set_dir;
            if (direction == 3) {  // case the direction is CCW
                set_dir = "CCW";  // CCW direction is assigned to the variable
            } else {  // case the direction is CW
                set_dir = "CW";  // CW direction is assigned to the variable
            }

            if (b_servo_CW_pos && set_dir == "CW" || b_servo_CCW_pos && set_dir == "CCW") { // case bottom servo is at the rotate diretion position
                spin_home();
            }

            if (b_servo_home) {  // case bottom servo is at home
                rotate_out(set_dir);  // call to function to rotate cube 1st layer on the set direction, moving out from home
                remaining_moves.remove(0, 2);
            } 
            else if (b_servo_CW_pos && set_dir == "CCW") {  // case the bottom servo is at full CW position
                rotate_home(set_dir);  // call to function to spin the full cube toward home position
                remaining_moves.remove(0, 2);
            } 
            else if (b_servo_CCW_pos && set_dir == "CW") {  // case the bottom servo is at full CCW position
                rotate_home(set_dir);  // call to function to spin the full cube toward home position
                remaining_moves.remove(0, 2);
            }
        }
    }
}