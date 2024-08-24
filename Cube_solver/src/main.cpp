#include <Arduino.h>
#include <string>
#include <BluetoothSerial.h>

#define RED_LED 22
#define BLUE_LED 1
#define GREEN_LED 3
#define BUTTON 23

#define t_servo 32  // Gornji flip/cover servo
#define b_servo 33  // Donji turn servo

#define SERVO_B 0
#define SERVO_T 1
#define FREQUENCY 50
#define RESOLUTION 10

// Pulse width range: 0.5～2.5ms 
// Servo duty value = pulse_width * resoluiton / frequency = 2.5ms * 2^10 / (1/50Hz / 10^(-3))

// Preset vrijednosti za upravljanje servomotorima
const int t_servo_flip = 54;             // Gornji servo - flip pozicija
const int t_servo_open = 68;             // Gornji servo - open pozicija 
const int t_servo_close = 76;            // Gornji servo - close pozicija
const int t_flip_to_close_time = 800;    // vrijeme potrebno za spuštanje iz flipa u closed poziciju
const int t_close_to_flip_time = 1000;   // vrijeme potrebno za podzianje iz close u flip poziciju
const int t_flip_open_time = 600;        // vrijeme potrebno za podzianje/spuštanje između open i flip pozicije
const int t_open_close_time = 400;       // vrijeme potrebno za podzianje/spuštanje između open i close pozicije

const int b_servo_CCW = 51;              // Donji servo - CW pozicija  
const int b_home = 76;                   // Donji servo - home pozicija
const int b_servo_CW = 101;              // Donji servo - CCW pozicija
const int b_spin_time = 800;             // vrijeme potrebno za okretanje cijele kocke za 90°
const int b_rotate_time = 800;           // vrijeme potrebno za rješavanje kocke rotacijom za 90°
const int b_rel_time = 100;              // vrijeme potrebno za otpuštanje, okretanje korak unazad
const int b_home_from_CW = b_home - 2;   // rotacija za 2 koraka više tijekom rješavanja zbog kompenzacije razmaka 
const int b_home_from_CCW = b_home + 2;  // rotacija za 2 koraka više tijekom rješavanja zbog kompenzacije razmaka

int t_top_cover = 1;           // Stanje gornjeg ora (0 - closed, 1 - open, 2 - flip) 
bool b_servo_operable = true;  // Varijabla za blokiranje/dopuštanje rada donjeg servomotora 
bool b_servo_stopped = true;   // Varijabla pozicije donjeg servomotora za omogućavanje kretanja gornjeg servomotora  
bool b_servo_home = true;      // Varijabla za poziciju donjeg servomotora na 0°
bool b_servo_CW_pos = false;   // Varijabla za poziciju donjeg servomotora na 90°
bool b_servo_CCW_pos = false;  // Varijabla za poziciju donjeg servomotora na -90°
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

String remaining_moves = "";   // Globalna varijabla za spremanje koraka

BluetoothSerial SerialBT;

unsigned long previousMillis = 0;
const long interval = 50; // Interval provjere pritiska buttona


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
    ledcWrite(SERVO_B, 76);      // Početna pozicija donjeg servomotora
    ledcWrite(SERVO_T, 68);      // Početna pozicija gornjeg servomotora

    delay(4000);

    SerialBT.begin("LolinD32");  // Pokretanje bluetooth komunikacije

}

void loop() {
    // Provjera bluetooth konekcije
    if (SerialBT.hasClient()) {         
        digitalWrite(BLUE_LED, HIGH);
    }
    else {
        digitalWrite(BLUE_LED, LOW);
    }

    // Primanje i postavljanje koraka
    if (SerialBT.available()) {         
        remaining_moves = SerialBT.readString();
    }

    // Izmjena stop_servo varijable buttonom
    if (digitalRead(BUTTON) == HIGH && remaining_moves.length() > 0) {
            stop_servos = !stop_servos;  
            delay(200);  // Debounce delay
        }

    // Pokretanje slaganja rubikove kocke
    if (!stop_servos && remaining_moves.length() > 0) {
            digitalWrite(GREEN_LED, HIGH);
            servo_solve_cube(remaining_moves);
        }
    
    // Treptanje LED diode ako je preostalo koraka
    if (remaining_moves.length() > 0 && stop_servos) {
        digitalWrite(GREEN_LED, HIGH);
        customDelay(500);
        digitalWrite(GREEN_LED, LOW);
        customDelay(500);
    }

    // Isključi LED diodu ako nema koraka
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


// Funkcija za postavljanje flip poziciju
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


// Funkcija za prijelaz iz flip u open poziciju
void flip_to_open() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        ledcWrite(SERVO_T, t_servo_open);
        customDelay(t_flip_open_time);
        t_top_cover = 1;
        b_servo_operable = true;
    }
    
}


// Funkcija za prijelaz iz flip u closed poziciju
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


// Funkcija za postavljanje u open poziciju
void open_cover() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        ledcWrite(SERVO_T, t_servo_open);
        customDelay(t_open_close_time);
        t_top_cover = 1;
        b_servo_operable = true;
    }
}


// Funkcija za postavljanje u closed poziciju
void close_cover() {
    if (b_servo_stopped) {
        b_servo_operable = false;
        ledcWrite(SERVO_T, t_servo_close);
        delay(t_open_close_time);
        t_top_cover = 0;
        b_servo_operable = true;
    }
}


// Funkcija za okretanje u CW ili CCW poziciju (90° ili -90°)
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


// Funkcija za okretanje u nultu poziciju (0°)
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


// Funkcija za rješavanje rotacijom u nultu poziciju (0°)
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

// Funkcija za upravljanje servomotorima i rješavanje kocke
void servo_solve_cube(String moves) {
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