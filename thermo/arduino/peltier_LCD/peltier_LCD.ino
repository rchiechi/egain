/***************************************************
/* Wiring diagram
 *  https://ali-atwa.medium.com/how-to-use-a-peltier-with-arduino-a35b0d4e52c2
 */

#include <SPI.h>
#include "Adafruit_MAX31855.h"
#include <Adafruit_RGBLCDShield.h>
#include "RunningAverage.h"
#include "peltier_LCD.h"

// The thermocouple objects initialized with software SPI
Adafruit_MAX31855 Thermocouples[] = { Adafruit_MAX31855(CLK, LCS, DO),
                                      Adafruit_MAX31855(CLK, RCS, DO) };
//The LCD display object.
Adafruit_RGBLCDShield lcd = Adafruit_RGBLCDShield();

// Terminator expected for Serial input from host
#define terminator ';'

// Strings
// const char left[] PROGMEM = "left";
// const char right[] PROGMEM = "right";
// char side[16];
// const char* const sides[] PROGMEM = {left, right};
/*
    Set the values of these pins in the header file
*/

// **** Initialize global variables
double setDegC[] = { 25.0, 25.0 };     // Target temperatures
uint8_t power[] = { 0, 0 };            // Power to MOSTFETs
bool peltier_on[] = { false, false };  // Keep track of left pletier power state
uint8_t flow[] = { HEAT, COOL };       // Whether peltiers are in heating or cooling mode
uint8_t peltier_polarity[] = { LPETLIER_POLARITY, RPLETIER_POLARITY };
uint8_t const peltier_addr[] = { LPELTIER, RPELTIER };
uint8_t const peltier_relay[] = { LPELTIER_RELAY, RPELTIER_RELAY };
bool initialized;

// Running averages for temperatures
RunningAverage avgTC[] = {
  RunningAverage(10),  // LEFT
  RunningAverage(10)   //RIGHT
};

void (*state)() = NULL;                // The current state.
void (*last_state)() = NULL;           // The state prior to the current state.
unsigned long last_state_change_time;  // The time in milliseconds since the last state change.
unsigned long time;                    // The current time in milliseconds since boot.
uint8_t selected_menu_idx;             // The currently selected menu index.
uint8_t clicked_buttons;               // The bitmask of currently clicked buttons.

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


/*!
  Custom icons created using: http://www.quinapalus.com/hd44780udg.html
*/
byte icons[6][8] = {  // Array of custom bitmap icons.
  { 0x0c, 0x12, 0x12, 0x0c, 0x00, 0x00, 0x00 },
  { 0x00, 0x08, 0x0c, 0x0e, 0x0c, 0x08, 0x00 },
  { 0x00, 0x02, 0x06, 0x0e, 0x06, 0x02, 0x00 },
  { 0x00, 0x1b, 0x0e, 0x04, 0x0e, 0x1b, 0x00 },
  { 0x00, 0x0a, 0x1b, 0x04, 0x1b, 0x0a, 0x00 },
  { 0x0a, 0x00, 0x15, 0x15, 0x0a, 0x0e, 0x04 }
};
// Index into the bitmap array for degree symbol.
const uint8_t DEGREE_ICON_IDX = 0;
const uint8_t LEFT_TRIANGLE_IDX = 1;
const uint8_t RIGHT_TRIANGLE_IDX = 2;
const uint8_t X_IDX = 3;
const uint8_t COOL_IDX = 4;
const uint8_t HEAT_IDX = 5;

/* 
 ###########################################################################
                setup
 ###########################################################################
*/
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
  for (uint8_t side = LEFT; side < RIGHT; ++side) {
    pinMode(peltier_relay[side], OUTPUT);  // sets the digital pin as output
    pinMode(peltier_addr[side], OUTPUT);   // sets the PWM pin as output
    avgTC[side].clear();                   // Clear the running average objects
  }
  // Start the LCD screen
  lcd.begin(16, 2);
  // Define custom symbols
  lcd.createChar(DEGREE_ICON_IDX, icons[DEGREE_ICON_IDX]);
  lcd.createChar(LEFT_TRIANGLE_IDX, icons[LEFT_TRIANGLE_IDX]);
  lcd.createChar(RIGHT_TRIANGLE_IDX, icons[RIGHT_TRIANGLE_IDX]);
  lcd.createChar(X_IDX, icons[X_IDX]);
  lcd.createChar(COOL_IDX, icons[COOL_IDX]);
  lcd.createChar(HEAT_IDX, icons[HEAT_IDX]);
  
  lcd.clear(); // Clear the screen
  lcd.setCursor(0, 0); // Set cursor to origin
  lcd.setBacklight(ON); // Switch on the LCD backlight (future: set backlight color)
  lcd.print("LCD initialized");
  /*
   * The state variable holds a pointer to the current state function
   * when the device powers on, the first state is the splash screen
   * to let the user know that everything has been set to power-on defaults
   */
  state = begin_splash_screen;
}


/* 
 ###########################################################################
                main loop
 ###########################################################################
*/
void loop() {
  // Read thermocouples
  double c;
  for (uint8_t side = LEFT; side < RIGHT; ++side) {
    c = Thermocouples[side].readCelsius();
    if (!isnan(c)) {
      avgTC[side].addValue(c);
    }
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
  // Handle any buffered Serial requests
  if (Serial.available() > 0) {
    handle_request();
  }
  // Set peltier states according to peltier_on
  togglePeltier();
  // Set the power to the MOSFETS according to setDegC
  for (uint8_t side = LEFT; side < RIGHT; ++side) {
    setPeltier(side);
  }
  delay(100);
}
// ###########################################################################
