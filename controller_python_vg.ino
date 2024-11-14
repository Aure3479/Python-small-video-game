#include <Adafruit_Keypad.h>

const byte ROWS = 3; // Trois lignes
const byte COLS = 3; // Trois colonnes

byte ROW_PINS[ROWS] = {20, 10, 0};    // Broches des lignes (à adapter selon votre câblage)
byte COL_PINS[COLS] = {7, 8, 1};      // Broches des colonnes (à adapter selon votre câblage)

char keys[ROWS][COLS] = {
  {'U', 'L', 'D'},
  {'R', 'S', 'R'},
  {'A', 'B', '9'}
};

Adafruit_Keypad keypad = Adafruit_Keypad(makeKeymap(keys), ROW_PINS, COL_PINS, ROWS, COLS);

void setup() {
  Serial.begin(115200);
  Serial.println("Hello from Arduino!");
  keypad.begin();
}

void loop() {
  keypad.tick();
  if(Serial.available()>0){
    String data = Serial.readString();



  }

  while (keypad.available()) {
    keypadEvent e = keypad.read();
    if (e.bit.EVENT == KEY_JUST_PRESSED) {
      char key = e.bit.KEY;
      if (key == 'U') {         // Bouton haut pressé
        Serial.println("UP");
      } else if (key == 'D') {  // Bouton bas pressé
        Serial.println("DOWN");
      } else if (key == 'A') {  // Bouton A pressé (action spéciale)
        Serial.println("RIGHT");
      } else if (key == 'B') {  // Bouton B pressé (action spéciale)
        Serial.println("LEFT");
      }
    }
  }
  delay(10);
}
