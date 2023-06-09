/***************************************************
/* Wiring diagram
 *  https://ali-atwa.medium.com/how-to-use-a-peltier-with-arduino-a35b0d4e52c2
 */

#include <SPI.h>
#include "Adafruit_MAX31855.h"
#include <Adafruit_RGBLCDShield.h>

// Default connection is using software SPI, but comment and uncomment one of
// the two examples below to switch between software SPI and hardware SPI:

// Example creating a thermocouple instance with software SPI on any three
// digital IO pins.
#define DO 11
#define RCS 9
#define CLK 13
// #define LDO   8
#define LCS 10
// #define LCLK  10
// initialize the Thermocouple
Adafruit_MAX31855 leftThermocouple(CLK, LCS, DO);
Adafruit_MAX31855 rightThermocouple(CLK, RCS, DO);

#define RPELTIER 4
#define RPELTIER_RELAY 6
#define LPELTIER 5
#define LPELTIER_RELAY 7  // Currently unused

// Example creating a thermocouple instance with hardware SPI
// on a given CS pin.
//#define MAXCS   10
//Adafruit_MAX31855 thermocouple(MAXCS);

// Example creating a thermocouple instance with hardware SPI
// on SPI1 using specified CS pin.
//#define MAXCS   10
//Adafruit_MAX31855 thermocouple(MAXCS, SPI1);

#define terminator ';'
#define LEFT 0
#define RIGHT 1
#define COOL 0
#define HEAT 1
//int peltier_level = 0;
//int peltier_level = map(power, 0, 99, 0, 255); //This is a value from 0 to 255 that actually controls the MOSFET
double leftDegC = 25.0;
int leftpower = 0;
double rightDegC = 25.0;
int rightpower = 0;
bool left_peltier_on = false;
bool right_peltier_on = false;
int left_flow = HEAT;
int right_flow = COOL;

bool initialized = false;


//! The current state.
void (*state)() = NULL;

//! The state prior to the current state.
void (*last_state)() = NULL;

//! The time in milliseconds since the last state change.
unsigned long last_state_change_time;

//! The current time in milliseconds since boot.
unsigned long time;

//! The currently selected menu index.
uint8_t selected_menu_idx;

//! The LCD display object.
Adafruit_RGBLCDShield lcd = Adafruit_RGBLCDShield();

//! Enum of backlight colors.
enum BackLightColor { ON = 0x1,
                      OFF = 0x0,
                      RED = 0x1,
                      YELLOW = 0x3,
                      GREEN = 0x2,
                      TEAL = 0x6,
                      BLUE = 0x4,
                      VIOLET = 0x5,
                      WHITE = 0x7 };

//! The bitmask of currently clicked buttons.
uint8_t clicked_buttons;

//! Array of custom bitmap icons.
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
//! Index into the bitmap array for degree symbol.
const int DEGREE_ICON_IDX = 0;
const int LEFT_TRIANGLE_IDX = 1;
const int RIGHT_TRIANGLE_IDX = 2;
const int X_IDX = 3;
const int COOL_IDX = 4;
const int HEAT_IDX = 5;

void setup() {
  Serial.begin(115200);

  while (!Serial) delay(1);  // wait for Serial on Leonardo/Zero, etc

  // Serial.println("{\"message\":\"MAX31855 test\"}");
  // wait for MAX chip to stabilize
  delay(500);
  Serial.println("{\"message\":\"Left Thermocouple Initializing\"}");
  if (!leftThermocouple.begin()) {
    Serial.println("{\"message\":\"ERROR\"}");
    while (1) delay(10);
  }
  Serial.println("{\"message\":\"Right Thermocouple Initializing\"}");
  if (!rightThermocouple.begin()) {
    Serial.println("{\"message\":\"ERROR\"}");
    while (1) delay(10);
  }
  Serial.println("{\"message\":\"Done initializing thermocouples\"}");
  initialized = true;

  pinMode(LPELTIER_RELAY, OUTPUT);  // sets the digital pin as output
  pinMode(LPELTIER, OUTPUT);        // sets the PWM pin as output
  pinMode(RPELTIER_RELAY, OUTPUT);  // sets the digital pin as output
  pinMode(RPELTIER, OUTPUT);        // sets the PWM pin as output

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



void loop() {
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
    // read the incoming byte:
    String incomingCmd = Serial.readStringUntil(terminator);
    if (incomingCmd == "ONLEFT") {
      left_peltier_on = true;
      digitalWrite(LPELTIER_RELAY, HIGH);  // sets the digital pin on
    }
    if (incomingCmd == "OFFLEFT") {
      left_peltier_on = false;
      digitalWrite(LPELTIER_RELAY, LOW);  // sets the digital pin off
    }
    if (incomingCmd == "ONRIGHT") {
      right_peltier_on = true;
      digitalWrite(RPELTIER_RELAY, HIGH);  // sets the digital pin on
    }
    if (incomingCmd == "OFFRIGHT") {
      right_peltier_on = false;
      digitalWrite(RPELTIER_RELAY, LOW);  // sets the digital pin off
    }
    if (incomingCmd == "SETLTEMP") {
      leftDegC = Serial.parseFloat();
    }
    if (incomingCmd == "SETRTEMP") {
      rightDegC = Serial.parseFloat();
    }
    if (incomingCmd == "LHEAT") {
      left_flow = HEAT;
    }
    if (incomingCmd == "LCOOL") {
      left_flow = COOL;
    }
    if (incomingCmd == "RHEAT") {
      right_flow = HEAT;
    }
    if (incomingCmd == "RCOOL") {
      right_flow = COOL;
    }

    if (incomingCmd == "POLL") {
      Serial.print("{\"LEFT\":");
      double c = leftThermocouple.readCelsius();
      if (!isnan(c)) {
        Serial.print(c);
      } else {
        Serial.print(-999.9);
      }
      Serial.print(",\"RIGHT\":");
      c = rightThermocouple.readCelsius();
      if (!isnan(c)) {
        Serial.print(c);
      } else {
        Serial.print(-999.9);
      }
      Serial.print(",");
      Serial.print("\"LTARGET\":");
      Serial.print(leftDegC);
      Serial.print(",");
      Serial.print("\"RTARGET\":");
      Serial.print(rightDegC);
      Serial.print(",");
      checkPeltier();
      Serial.println("}");
    }
  }
  setLeft();
  setRight();



  delay(100);
}

// ###########################################################################

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
  if (right_peltier_on) {
    if (right_flow == HEAT) {
      lcd.write(HEAT_IDX);
    } else if (right_flow == COOL) {
      lcd.write(COOL_IDX);
    }
  } else {
    lcd.write(X_IDX);
  }
  lcd.setCursor(0, 1);
  lcd.print(F("L: "));
  if (left_peltier_on) {
    if (left_flow == HEAT) {
      lcd.write(HEAT_IDX);
    } else if (left_flow == COOL) {
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

  double lc = leftThermocouple.readCelsius();
  double rc = rightThermocouple.readCelsius();

  if (update) {
    lcd.setBacklight(ON);
    lcd.setCursor(0, 0);
    if (left_peltier_on) {
      if (left_flow == HEAT) {
        lcd.write(HEAT_IDX);
      } else if (left_flow == COOL) {
        lcd.write(COOL_IDX);
      }
    } else {
      lcd.write(X_IDX);
    }
    lcd.print(F("R: "));
    lcd.print(lc, 1);
    lcd.write(0x7E);
    lcd.print(leftDegC, 1);
    lcd.print(" ");
    lcd.write(DEGREE_ICON_IDX);
    lcd.print(F("C "));
    lcd.setCursor(0, 1);
    if (right_peltier_on) {
      if (right_flow == HEAT) {
        lcd.write(HEAT_IDX);
      } else if (right_flow == COOL) {
        lcd.write(COOL_IDX);
      }
    } else {
      lcd.write(X_IDX);
    }
    lcd.print(F("L: "));
    lcd.print(rc, 1);
    lcd.write(0x7E);
    lcd.print(rightDegC, 1);
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
      leftDegC = leftDegC + 0.5;
    }
    if (clicked_buttons & BUTTON_DOWN) {
      leftDegC = leftDegC - 0.5;
    }
    if (clicked_buttons & BUTTON_RIGHT) {
      rightDegC = rightDegC + 0.5;
    }
    if (clicked_buttons & BUTTON_LEFT) {
      rightDegC = rightDegC - 0.5;
    }
  }
}

void checkPeltier() {
  Serial.print("\"Peltier_on\":[");
  if (left_peltier_on) {
    Serial.print("true");
  } else {
    Serial.print("false");
  }
  Serial.print(", ");
  if (right_peltier_on) {
    Serial.print("true");
  } else {
    Serial.print("false");
  }
  Serial.print("]");
  // int peltier_level = analogRead(PELTIER);
  // int power = map(peltier_level, 0, 1024, 0, 100);
  Serial.print(", \"LeftPower\":");
  Serial.print(leftpower);
  Serial.print(", \"RightPower\":");
  Serial.print(rightpower);
}

void setLeft() {
  int setpower = 0;
  double c = leftThermocouple.readCelsius();
  if (!isnan(c) && left_peltier_on) {
    double leftDegK = leftDegC + 273.15;
    int k = c + 273.15;
    setpower = (1 - (leftDegK / k)) * 100;
    int deltaK = abs(leftDegK - k);
    if (deltaK < 5) {
      setpower += 50;
    } else if (deltaK < 10) {
      setpower += 75;
    } else {
      setpower = 100;
    }
    if (left_flow == COOL) {
      if (c >= leftDegC) {
        setPeltier(LEFT, setpower);
      } else {
        setPeltier(LEFT, 0);
      }
    }
    if (left_flow == HEAT) {
      if (c <= leftDegC) {
        setPeltier(LEFT, setpower);
      } else {
        setPeltier(LEFT, 0);
      }
    }
  }
}

void setRight() {
  int setpower = 0;
  double c = rightThermocouple.readCelsius();
  if (!isnan(c) && right_peltier_on) {
    double rightDegK = rightDegC + 273.15;
    int k = c + 273.15;
    setpower = (1 - (rightDegK / k)) * 100;
    int deltaK = abs(rightDegK - k);
    if (deltaK < 5) {
      setpower += 50;
    } else if (deltaK < 10) {
      setpower += 75;
    } else {
      setpower = 100;
    }
    if (right_flow == COOL) {
      if (c >= rightDegC) {
        setPeltier(RIGHT, setpower);
      } else {
        setPeltier(RIGHT, 0);
      }
    }
    if (right_flow == HEAT) {
      if (c <= rightDegC) {
        setPeltier(RIGHT, setpower);
      } else {
        setPeltier(RIGHT, 0);
      }
    }
  }
}

void setPeltier(int side, int setpower) {
  int *power;
  int peltier_addr;
  if (side == LEFT) {
    peltier_addr = LPELTIER;
    power = &leftpower;
  } else if (side == RIGHT) {
    peltier_addr = RPELTIER;
    power = &rightpower;
  }
  if (setpower > 100) {
    power = 100;
  } else if (setpower < 0) {
    power = 0;
  } else {
    power = setpower;
  }
  bool peltier_on;
  if (side == LEFT && left_peltier_on) {
    peltier_on = true;
  }
  if (side == RIGHT && right_peltier_on) {
    peltier_on = true;
  }
  if (peltier_on) {
    int peltier_level = map(power, 0, 100, 0, 255);
    analogWrite(peltier_addr, peltier_level);  //Write this new value out to the port
  } else {
    analogWrite(peltier_addr, 0);
  }
}
