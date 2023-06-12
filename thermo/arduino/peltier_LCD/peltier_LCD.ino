/***************************************************
/* Wiring diagram
 *  https://ali-atwa.medium.com/how-to-use-a-peltier-with-arduino-a35b0d4e52c2
 */

#include <SPI.h>
#include "Adafruit_MAX31855.h"
#include <Adafruit_RGBLCDShield.h>
#include "RunningAverage.h"

// Create thermocouple instances with software SPI digital IO pins.
#define DO 11
#define RCS 9
#define CLK 13
#define LCS 10


// The thermocouple objects
Adafruit_MAX31855 Thermocouples[] = { Adafruit_MAX31855(CLK, LCS, DO), Adafruit_MAX31855(CLK, RCS, DO) };
// Define pins to control peltier relays and MOSFETs
#define RPELTIER 6
#define RPELTIER_RELAY 4
#define LPELTIER 5
#define LPELTIER_RELAY 4  // For future use if two power supplies are needed

// Constants
#define terminator ';'
#define LEFT 0
#define RIGHT 1
#define COOL 0
#define HEAT 1

// Strings
// const char left[] PROGMEM = "left";
// const char right[] PROGMEM = "right";
// char side[16];
// const char* const sides[] PROGMEM = {left, right};

// **** Initialize global variables 
double setDegC[] = {25.0, 25.0}; // Target temperatures
int power[] = {0, 0}; // Power to MOSTFETs
bool peltier_on[] = {false, false}; // Keep track of left pletier power state
int flow[] = {HEAT, COOL}; // Whether peltiers are in heating or cooling mode
int peltier_addr[] = {LPELTIER, RPELTIER};
int peltier_relay[] = {LPELTIER_RELAY, RPELTIER_RELAY};
bool initialized;
// Running averages for temperatures
RunningAverage avgTC[] = { RunningAverage(10), RunningAverage(10) };
void (*state)() = NULL; // The current state.
void (*last_state)() = NULL; // The state prior to the current state.
unsigned long last_state_change_time; // The time in milliseconds since the last state change.
unsigned long time; // The current time in milliseconds since boot.
uint8_t selected_menu_idx; // The currently selected menu index.
//The LCD display object.
Adafruit_RGBLCDShield lcd = Adafruit_RGBLCDShield();
// Enum of backlight colors for future use.
enum BackLightColor { ON = 0x1,
                      OFF = 0x0,
                      RED = 0x1,
                      YELLOW = 0x3,
                      GREEN = 0x2,
                      TEAL = 0x6,
                      BLUE = 0x4,
                      VIOLET = 0x5,
                      WHITE = 0x7 };
// The bitmask of currently clicked buttons.
uint8_t clicked_buttons;
// Array of custom bitmap icons.
/*!
  Custom icons created using: http://www.quinapalus.com/hd44780udg.html
*/
byte icons[6][8] = {
  { 0x0c, 0x12, 0x12, 0x0c, 0x00, 0x00, 0x00 },
  { 0x00, 0x08, 0x0c, 0x0e, 0x0c, 0x08, 0x00 },
  { 0x00, 0x02, 0x06, 0x0e, 0x06, 0x02, 0x00 },
  { 0x00, 0x1b, 0x0e, 0x04, 0x0e, 0x1b, 0x00 },
  { 0x00, 0x0a, 0x1b, 0x04, 0x1b, 0x0a, 0x00 },
  { 0x0a, 0x00, 0x15, 0x15, 0x0a, 0x0e, 0x04 }
};
// Index into the bitmap array for degree symbol.
const int DEGREE_ICON_IDX = 0;
const int LEFT_TRIANGLE_IDX = 1;
const int RIGHT_TRIANGLE_IDX = 2;
const int X_IDX = 3;
const int COOL_IDX = 4;
const int HEAT_IDX = 5;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(1);  // wait for Serial on Leonardo/Zero, etc
  // wait for MAX chip to stabilize
  delay(500);
  initialized = true;
  Serial.println("{\"message\":\"Left Thermocouple Initializing\"}");
  if (!Thermocouples[LEFT].begin()) {
    initialized = false;
    Serial.println("{\"message\":\"ERROR\"}");
    while (1) delay(10);
  }
  Serial.println("{\"message\":\"Right Thermocouple Initializing\"}");
  if (!Thermocouples[RIGHT].begin()) {
    initialized = false;
    Serial.println("{\"message\":\"ERROR\"}");
    while (1) delay(10);
  }
  Serial.println("{\"message\":\"Done initializing thermocouples\"}");
  pinMode(peltier_relay[LEFT], OUTPUT);  // sets the digital pin as output
  pinMode(peltier_addr[LEFT], OUTPUT);        // sets the PWM pin as output
  pinMode(peltier_relay[RIGHT], OUTPUT);  // sets the digital pin as output
  pinMode(peltier_addr[RIGHT], OUTPUT);        // sets the PWM pin as output
  // Clear the running average objects
  avgTC[LEFT].clear();
  avgTC[RIGHT].clear();
  lcd.begin(16, 2);
  // Define custom symbols
  lcd.createChar(DEGREE_ICON_IDX, icons[DEGREE_ICON_IDX]);
  lcd.createChar(LEFT_TRIANGLE_IDX, icons[LEFT_TRIANGLE_IDX]);
  lcd.createChar(RIGHT_TRIANGLE_IDX, icons[RIGHT_TRIANGLE_IDX]);
  lcd.createChar(X_IDX, icons[X_IDX]);
  lcd.createChar(COOL_IDX, icons[COOL_IDX]);
  lcd.createChar(HEAT_IDX, icons[HEAT_IDX]);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.setBacklight(ON);
  lcd.print("LCD initialized");
  // Initial state
  state = begin_splash_screen;
}
/* 
 ###########################################################################
                main loop
 ###########################################################################
*/
void loop() {
  // Read thermocouples
  double c[] = { Thermocouples[LEFT].readCelsius(), Thermocouples[RIGHT].readCelsius() };
  if (!isnan(c[LEFT])) {
    // leftTC.addValue(c[LEFT]);
    avgTC[LEFT].addValue(c[LEFT]);
  }
  if (!isnan(c[RIGHT])) {
    // rightTC.addValue(c[RIGHT]);
    avgTC[RIGHT].addValue(c[RIGHT]);
  }
  time = millis();
  // Record time of state change so animations
  // know when to stop
  if (last_state != state) {
    last_state = state;
    last_state_change_time = time;
  }
  // Read in which buttons were clicked
  read_button_clicks();
  // Call current state function
  state();
  if (Serial.available() > 0) {
    handle_request();
  }
  togglePeltier();
  setLeft();
  setRight();
  delay(100);
}
// ###########################################################################


void handle_request() { // Handle incoming Serial requests
  // read the incoming byte:
  String incomingCmd = Serial.readStringUntil(terminator);

  if (incomingCmd == "INIT") {
    Serial.print("{\"INITIALIZED:\":");
    if (initialized) {
      Serial.print("true");
    } else {
      Serial.print("false");
    };
    Serial.println("}");
  }

  if (incomingCmd == "ONLEFT") {
    peltier_on[LEFT] = true;
  }
  if (incomingCmd == "OFFLEFT") {
    peltier_on[LEFT] = false;
  }
  if (incomingCmd == "ONRIGHT") {
    peltier_on[RIGHT] = true;
  }
  if (incomingCmd == "OFFRIGHT") {
    peltier_on[RIGHT] = false;
  }
  if (incomingCmd == "SETLTEMP") {
    setDegC[LEFT] = Serial.parseFloat();
  }
  if (incomingCmd == "SETRTEMP") {
    setDegC[RIGHT] = Serial.parseFloat();
  }
  if (incomingCmd == "LHEAT") {
    flow[LEFT] = HEAT;
  }
  if (incomingCmd == "LCOOL") {
    flow[LEFT] = COOL;
  }
  if (incomingCmd == "RHEAT") {
    flow[RIGHT] = HEAT;
  }
  if (incomingCmd == "RCOOL") {
    flow[RIGHT] = COOL;
  }

  if (incomingCmd == "POLL") {
    Serial.print("{\"LEFT\":");
    avgTC[LEFT].getAverage();
    Serial.print(",\"RIGHT\":");
    avgTC[RIGHT].getAverage();
    Serial.print(",");
    Serial.print("\"LTARGET\":");
    Serial.print(setDegC[LEFT]);
    Serial.print(",");
    Serial.print("\"RTARGET\":");
    Serial.print(setDegC[RIGHT]);
    Serial.print(",");
    checkPeltier();
    Serial.println("}");
  }
}

//! Return a bitmask of clicked buttons.
/*!
  Examine the bitmask of buttons which are currently pressed and compare against
  the bitmask of which buttons were pressed last time the function was called.
  If a button transitions from pressed to released, return it in the bitmask.

  \return the bitmask of clicked buttons
*/
void read_button_clicks() {
  static uint8_t last_buttons = 0;

  uint8_t buttons = lcd.readButtons();
  clicked_buttons = (last_buttons ^ buttons) & (~buttons);
  last_buttons = buttons;
}

//! Initial state, draw the splash screen.
void begin_splash_screen() {
  lcd.clear();
  lcd.setBacklight(ON);
  lcd.print(F("PELTIER CONTROLS"));
  state = animate_splash_screen;
}

//! Animate the splash screen.
/*!
  Blink the text "PRESS SELECT" and wait for the user to press the select button.
*/
void animate_splash_screen() {
  static boolean blink = true;
  static unsigned long last_blink_time;

  if (time - last_blink_time >= 1000) {
    lcd.setCursor(0, 1);
    if (blink) {
      lcd.write(0x7E);
      lcd.print(F(" PRESS SELECT "));
      lcd.write(0x7F);
    } else {
      lcd.print(F("                "));
    }
    blink = !blink;
    last_blink_time = time;
  }

  if (clicked_buttons & BUTTON_SELECT) {
    lcd.clear();
    state = show_summary;
  }
}

float ctof(float c) {
  return (c * 1.8) + 32;
}

void show_set_menu() {
  static bool update = true;
  static uint8_t last_menu_idx = 0;
  lcd.setBacklight(ON);
  lcd.setCursor(0, 0);
  lcd.print(F("R: "));
  if (peltier_on[RIGHT]) {
    if (flow[RIGHT] == HEAT) {
      lcd.write(HEAT_IDX);
    } else if (flow[RIGHT] == COOL) {
      lcd.write(COOL_IDX);
    }
  } else {
    lcd.write(X_IDX);
  }
  lcd.setCursor(0, 1);
  lcd.print(F("L: "));
  if (peltier_on[LEFT]) {
    if (flow[LEFT] == HEAT) {
      lcd.write(HEAT_IDX);
    } else if (flow[LEFT] == COOL) {
      lcd.write(COOL_IDX);
    }
  } else {
    lcd.write(X_IDX);
  }

  // lcd.write(DEGREE_ICON_IDX);
  // lcd.print(F("C"));
  if (clicked_buttons) {
    lcd.clear();
  }
  if (clicked_buttons & BUTTON_SELECT) {
    state = show_summary;
  } else if ((clicked_buttons & BUTTON_DOWN) && (selected_menu_idx == 0)) {
    ++selected_menu_idx;
  } else if (clicked_buttons & BUTTON_UP) {
    --selected_menu_idx;
  } else {
    state = show_set_menu;
  }
}

void show_summary() {
  static double last_lc = 0;
  static double last_rc = 0;
  static bool update = true;

  // Read the temperature as Celsius:
  double lc = avgTC[LEFT].getAverage();
  double rc = avgTC[RIGHT].getAverage();

  if (update) {
    lcd.setBacklight(ON);
    lcd.setCursor(0, 0);
    if (peltier_on[LEFT]) {
      if (flow[LEFT] == HEAT) {
        lcd.write(HEAT_IDX);
      } else if (flow[LEFT] == COOL) {
        lcd.write(COOL_IDX);
      }
    } else {
      lcd.write(X_IDX);
    }
    lcd.print(F("R: "));
    lcd.print(lc, 1);
    lcd.write(0x7E);
    lcd.print(setDegC[LEFT], 1);
    lcd.print(" ");
    lcd.write(DEGREE_ICON_IDX);
    lcd.print(F("C "));
    lcd.setCursor(0, 1);
    if (peltier_on[RIGHT]) {
      if (flow[RIGHT] == HEAT) {
        lcd.write(HEAT_IDX);
      } else if (flow[RIGHT] == COOL) {
        lcd.write(COOL_IDX);
      }
    } else {
      lcd.write(X_IDX);
    }
    lcd.print(F("L: "));
    lcd.print(rc, 1);
    lcd.write(0x7E);
    lcd.print(setDegC[RIGHT], 1);
    lcd.print(" ");
    lcd.write(DEGREE_ICON_IDX);
    lcd.print(F("C "));
  }
  update = false;

  if (abs(last_lc - lc) > 0.5) {
    last_lc = lc;
    update = true;
  }
  if (abs(last_rc - rc) > 0.5) {
    last_rc = rc;
    update = true;
  }
  if (clicked_buttons) {
    update = true;
    if (clicked_buttons & BUTTON_SELECT) {
      lcd.clear();
      selected_menu_idx = 0;
      state = show_set_menu;
    } else {
      state = show_summary;
    }
    if (clicked_buttons & BUTTON_UP) {
      setDegC[LEFT] = setDegC[LEFT] + 0.5;
    }
    if (clicked_buttons & BUTTON_DOWN) {
      setDegC[LEFT] = setDegC[LEFT] - 0.5;
    }
    if (clicked_buttons & BUTTON_RIGHT) {
      setDegC[RIGHT] = setDegC[RIGHT] + 0.5;
    }
    if (clicked_buttons & BUTTON_LEFT) {
      setDegC[RIGHT] = setDegC[RIGHT] - 0.5;
    }
  }
}

void checkPeltier() {
  Serial.print("\"Peltier_on\":[");
  if (peltier_on[LEFT]) {
    Serial.print("true");
  } else {
    Serial.print("false");
  }
  Serial.print(", ");
  if (peltier_on[RIGHT]) {
    Serial.print("true");
  } else {
    Serial.print("false");
  }
  Serial.print("]");
  Serial.print(", \"LeftPower\":");
  Serial.print(power[LEFT]);
  Serial.print(", \"RightPower\":");
  Serial.print(power[RIGHT]);
}

void setPeltier(int side) {
  int _setpower = 0;
  double c = Thermocouples[side].readCelsius();
  if (!isnan(c) && peltier_on[side]) {
    double DegK = setDegC[side] + 273.15;
    int k = c + 273.15;
    _setpower = (1 - (DegK / k)) * 100;
    int deltaK = abs(DegK - k);
    if (deltaK < 5) {
      _setpower += 50;
    } else if (deltaK < 10) {
      _setpower += 75;
    } else {
      _setpower = 100;
    }
    if (flow[side] == COOL) {
      if (c >= setDegC[LEFT]) {
        setpower(side, _setpower);
      } else {
        setpower(side, 0);
      }
    }
    if (flow[side] == HEAT) {
      if (c <= setDegC[LEFT]) {
        setpower(side, _setpower);
      } else {
        setpower(side, 0);
      }
    }
  }
}

// void setLeft() {
//   int setpower = 0;
//   double c = Thermocouples[LEFT].readCelsius();
//   if (!isnan(c) && peltier_on[LEFT]) {
//     double leftDegK = setDegC[LEFT] + 273.15;
//     int k = c + 273.15;
//     setpower = (1 - (leftDegK / k)) * 100;
//     int deltaK = abs(leftDegK - k);
//     if (deltaK < 5) {
//       setpower += 50;
//     } else if (deltaK < 10) {
//       setpower += 75;
//     } else {
//       setpower = 100;
//     }
//     if (flow[LEFT] == COOL) {
//       if (c >= setDegC[LEFT]) {
//         setPeltier(LEFT, setpower);
//       } else {
//         setPeltier(LEFT, 0);
//       }
//     }
//     if (flow[LEFT] == HEAT) {
//       if (c <= setDegC[LEFT]) {
//         setPeltier(LEFT, setpower);
//       } else {
//         setPeltier(LEFT, 0);
//       }
//     }
//   }
// }

// void setRight() {
//   int setpower = 0;
//   double c = Thermocouples[RIGHT].readCelsius();
//   if (!isnan(c) && peltier_on[RIGHT]) {
//     double rightDegK = setDegC[RIGHT] + 273.15;
//     int k = c + 273.15;
//     setpower = (1 - (rightDegK / k)) * 100;
//     int deltaK = abs(rightDegK - k);
//     if (deltaK < 5) {
//       setpower += 50;
//     } else if (deltaK < 10) {
//       setpower += 75;
//     } else {
//       setpower = 100;
//     }
//     if (flow[RIGHT] == COOL) {
//       if (c >= setDegC[RIGHT]) {
//         setPeltier(RIGHT, setpower);
//       } else {
//         setPeltier(RIGHT, 0);
//       }
//     }
//     if (flow[RIGHT] == HEAT) {
//       if (c <= setDegC[RIGHT]) {
//         setPeltier(RIGHT, setpower);
//       } else {
//         setPeltier(RIGHT, 0);
//       }
//     }
//   }
// }

void setpower(int side, int _power) {
  int* set_power;
  if (_power > 100) {
    set_power = 100;
  } else if (_power < 0) {
    set_power = 0;
  } else {
    set_power = _power;
  }
  if (peltier_on[side]) {
    int peltier_level = map(power, 0, 100, 0, 255);
    analogWrite(peltier_addr[side], peltier_level);  //Write this new value out to the port
  } else {
    analogWrite(peltier_addr[side], 0);
  }
}

void togglePeltier() {
  bool _on = false;
  if (peltier_on[LEFT]) {
    _on = true;
    digitalWrite(peltier_relay[LEFT], HIGH);
  }
  if (peltier_on[RIGHT]) {
    _on = true;
    digitalWrite(eltier_relay[RIGHT], HIGH);
  }
  if (!peltier_on[LEFT] & !peltier_on[RIGHT]) {
    digitalWrite(peltier_relay[LEFT], LOW);
    digitalWrite(peltier_relay[RIGHT], LOW);
  }
}