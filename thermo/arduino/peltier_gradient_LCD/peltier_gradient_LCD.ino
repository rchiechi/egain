/***************************************************
  This is an example for the Adafruit Thermocouple Sensor w/MAX31855K

  Designed specifically to work with the Adafruit Thermocouple Sensor
  ----> https://www.adafruit.com/products/269

  These displays use SPI to communicate, 3 pins are required to
  interface
  Adafruit invests time and resources providing this open source code,
  please support Adafruit and open-source hardware by purchasing
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.
  BSD license, all text above must be included in any redistribution
 ****************************************************/

/* Wiring diagram
 *  https://ali-atwa.medium.com/how-to-use-a-peltier-with-arduino-a35b0d4e52c2
 */


// Tear down and rebuild in the style of https://github.com/adafruit/Hunt-The-Wumpus/blob/master/Hunt_The_Wumpus.ino

#include <SPI.h>
#include "Adafruit_MAX31855.h"
#include <Adafruit_RGBLCDShield.h>
// Default connection is using software SPI, but comment and uncomment one of
// the two examples below to switch between software SPI and hardware SPI:

// Example creating a thermocouple instance with software SPI on any three
// digital IO pins.
#define RDO   3
#define RCS   4
#define RCLK  5
#define LDO   8
#define LCS   9
#define LCLK  10
// initialize the Thermocouple
Adafruit_MAX31855 leftThermocouple(LCLK, LCS, LDO);
Adafruit_MAX31855 rightThermocouple(RCLK, RCS, RDO);

#define PELTIER_RELAY 13
#define RPELTIER 6
#define LPELTIER 11

// Example creating a thermocouple instance with hardware SPI
// on a given CS pin.
//#define MAXCS   10
//Adafruit_MAX31855 thermocouple(MAXCS);

// Example creating a thermocouple instance with hardware SPI
// on SPI1 using specified CS pin.
//#define MAXCS   10
//Adafruit_MAX31855 thermocouple(MAXCS, SPI1);

// These #defines make it easy to set the backlight color
#define OFF 0x0
#define ON 0x1
#define RED 0x1
#define YELLOW 0x3
#define GREEN 0x2
#define TEAL 0x6
#define BLUE 0x4
#define VIOLET 0x5
#define WHITE 0x7 

#define MODE_DISPLAY 0
#define SELECT_TOP 1
#define SELECT_BOTTOM 2
#define MENU_IDX1 3
#define MENU_IDX2 4
#define MENU_IDX3 5

Adafruit_RGBLCDShield lcd;

#define terminator ';'
#define LEFT 0
#define RIGHT 1
#define COOL 0
#define HEAT 1
//int peltier_level = 0;
//int peltier_level = map(power, 0, 99, 0, 255); //This is a value from 0 to 255 that actually controls the MOSFET
int leftDegC = 25;
int leftpower = 0;
int rightDegC = 25;
int rightpower = 0;
bool left_peltier_on = false;
bool right_peltier_on = false;
int left_flow = HEAT;
int right_flow = COOL;

bool initialized = false;

void setup() {
  Serial.begin(9600);

  while (!Serial) delay(1); // wait for Serial on Leonardo/Zero, etc

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

  pinMode(LPELTIER, OUTPUT); // sets the PWM pin as output
  pinMode(PELTIER_RELAY, OUTPUT);    // sets the digital pin as output
  pinMode(RPELTIER, OUTPUT); // sets the PWM pin as output
  
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.setBacklight(ON);
  lcd.print("Hello world");
}


void checkPeltier() {
  Serial.print("\"Peltier_on\":[");
  if (left_peltier_on){
    Serial.print("true");
  }else{
    Serial.print("false");
  }
  Serial.print(", ");
  if (right_peltier_on){
    Serial.print("true");
  }else{
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

void setLeft(){
  int setpower = 0;
  double c = leftThermocouple.readCelsius();
  if (!isnan(c) && left_peltier_on){
    double leftDegK = leftDegC + 273.15;
    int k = c + 273.15;
    setpower = (1 - (leftDegK / k)) * 100;
    int deltaK = abs(leftDegK - k);
    if (deltaK < 5){
      setpower += 50;
    }else if (deltaK < 10){
      setpower += 75;
    }else{
      setpower = 100;
    }
    if (left_flow == COOL){
      if (c >= leftDegC){
        setPeltier(LEFT, setpower);
      }
      else {
        setPeltier(LEFT, 0);
      }
    }
    if (left_flow == HEAT){
      if (c <= leftDegC){
        setPeltier(LEFT, setpower);
      }
      else {
        setPeltier(LEFT, 0);
        }
      }
  }
}

void setRight(){
  int setpower = 0;
  double c = rightThermocouple.readCelsius();
  if (!isnan(c) && right_peltier_on){
    double rightDegK = rightDegC + 273.15;
    int k = c + 273.15;
    setpower = (1 - (rightDegK / k)) * 100;
    int deltaK = abs(rightDegK - k);
    if (deltaK < 5){
      setpower += 50;
    }else if (deltaK < 10){
      setpower += 75;
    }else{
      setpower = 100;
    }
    if (right_flow == COOL){
      if (c >= rightDegC){
        setPeltier(RIGHT, setpower);
      }
      else {
        setPeltier(RIGHT, 0);
      }
    }
    if (right_flow == HEAT){
      if (c <= rightDegC){
        setPeltier(RIGHT, setpower);
      }
      else {
        setPeltier(RIGHT, 0);
      }
    }    
  }
}

void setPeltier(int side, int setpower){
  int *power;
  int peltier_addr;
  if(side == LEFT){
    peltier_addr = LPELTIER;
    power = &leftpower;
  }else if(side == RIGHT){
    peltier_addr = RPELTIER;
    power = &rightpower;
  }
  if(setpower > 100){
    power = 100;
  }else if(setpower < 0) {
    power = 0;
  }else {
    power = setpower;
  }
  bool peltier_on;
  if (side == LEFT && left_peltier_on){
    peltier_on = true;
  }
  if (side == RIGHT && right_peltier_on){
    peltier_on = true;
  }
  if (peltier_on){
    int peltier_level = map(power, 0, 100, 0, 255);
    analogWrite(peltier_addr, peltier_level); //Write this new value out to the port
  }else{
    analogWrite(peltier_addr, 0);
  }
}


void read_button_clicks() {
  static uint8_t last_buttons = 0;
  
  uint8_t buttons = lcd.readButtons();
  clicked_buttons = (last_buttons ^ buttons) & (~buttons);
  last_buttons = buttons;
}

class 

int select = SELECT_TOP;
int screen = MODE_DISPLAY;

void loop() {
  uint8_t buttons = lcd.readButtons();
  if (buttons) {
    lcd.clear();
    lcd.setCursor(0,0);
  }
  if ( (buttons BUTTON_UP){
    if (select == SELECT_TOP){
      select = SELECT_BOTTOM;
    }else{
      select = SELECT_TOP;
    }
  }
  if (buttons & BUTTON_DOWN) {
    lcd.print("DOWN ");
    lcd.setBacklight(YELLOW);
  }
  if (buttons & BUTTON_LEFT) {
    lcd.print("LEFT ");
    lcd.setBacklight(GREEN);
  }
  if (buttons & BUTTON_RIGHT) {
    lcd.print("RIGHT ");
    lcd.setBacklight(TEAL);
  }
  if (buttons & BUTTON_SELECT) {
    lcd.print("SELECT ");
    lcd.setBacklight(VIOLET);
  }

  if (Serial.available() > 0) {
      // read the incoming byte:
      String incomingCmd = Serial.readStringUntil(terminator);
      if (incomingCmd == "ONRIGHT"){
        right_peltier_on = true;
        digitalWrite(PELTIER_RELAY, HIGH); // sets the digital pin on
      }
      if (incomingCmd == "OFFRIGHT"){
        right_peltier_on = false;
        digitalWrite(PELTIER_RELAY, LOW);  // sets the digital pin off
      }
      if (incomingCmd == "SETLTEMP"){
        leftDegC = Serial.parseFloat();
      }
      if (incomingCmd == "SETRTEMP"){
        rightDegC = Serial.parseFloat();
      }
      if (incomingCmd == "LHEAT"){
        left_flow = HEAT;
      }
      if (incomingCmd == "LCOOL"){
        left_flow = COOL;
      }
      if (incomingCmd == "RHEAT"){
        right_flow = HEAT;
      }
      if (incomingCmd == "RCOOL"){
        right_flow = COOL;
      }
    
    if (incomingCmd == "POLL"){
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.setBacklight(ON);
      Serial.print("{\"LEFT\":");
      double c = leftThermocouple.readCelsius();
      if (!isnan(c)){
        Serial.print(c);
        lcd.print("L: ");
        lcd.print(c,2);
        lcd.print("C");
      } else{
        Serial.print(-999.9);
        uint8_t e = leftThermocouple.readError();
        if (e & MAX31855_FAULT_OPEN) lcd.print("FAULT:Open circuit");
        if (e & MAX31855_FAULT_SHORT_GND) lcd.print("FAULT: GND short");
        if (e & MAX31855_FAULT_SHORT_VCC) lcd.print("FAULT: VCC short");
      }
      Serial.print(",\"RIGHT\":");
      lcd.setCursor(0,1);
      c = rightThermocouple.readCelsius();
      if (!isnan(c)){
        Serial.print(c);
        lcd.print("R: ");
        lcd.print(c,2);
        lcd.print("C");
      } else{
        Serial.print(-999.9);
        uint8_t e = rightThermocouple.readError();
        if (e & MAX31855_FAULT_OPEN) lcd.print("FAULT:Open circuit");
        if (e & MAX31855_FAULT_SHORT_GND) lcd.print("FAULT: GND short");
        if (e & MAX31855_FAULT_SHORT_VCC) lcd.print("FAULT: VCC short");
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
  delay(250);
}
