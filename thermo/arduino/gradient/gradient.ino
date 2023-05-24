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

#include <SPI.h>
#include "Adafruit_MAX31855.h"

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

#define RPELTIER 6
#define RPELTIER_RELAY 13
#define LPELTIER 11
#define LPELTIER_RELAY 12

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
//int peltier_level = 0;
//int peltier_level = map(power, 0, 99, 0, 255); //This is a value from 0 to 255 that actually controls the MOSFET
int leftDegC = 25;
int leftpower = 0;
int rightDegC = 25;
int rightpower = 0;
bool peltier_on = false;
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
  Serial.println("{\"message\":\"Done initializing\"}");
  initialized = true;

  pinMode(LPELTIER_RELAY, OUTPUT);    // sets the digital pin as output
  pinMode(LPELTIER, OUTPUT); // sets the PWM pin as output
  pinMode(RPELTIER_RELAY, OUTPUT);    // sets the digital pin as output
  pinMode(RPELTIER, OUTPUT); // sets the PWM pin as output
  
}


void checkPeltier() {
  Serial.print("\"Peltier_on\":");
  if (peltier_on){
    Serial.print("true");
  }else{
    Serial.print("false");
  }
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
  if (!isnan(c)){
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
    if (c >= leftDegC){
      setPeltier(LEFT, setpower);
    }
    else {
      setPeltier(LEFT, 0);
    }
  }
}

void setRight(){
  int setpower = 0;
  double c = rightThermocouple.readCelsius();
  if (!isnan(c)){
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
    if (c >= rightDegC){
      setPeltier(RIGHT, setpower);
    }
    else {
      setPeltier(RIGHT, 0);
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
  if (peltier_on){
    int peltier_level = map(power, 0, 100, 0, 255);
    analogWrite(peltier_addr, peltier_level); //Write this new value out to the port
  }else{
    analogWrite(peltier_addr, 0);
  }
}

void loop() {

  if (Serial.available() > 0) {
      // read the incoming byte:
      String incomingCmd = Serial.readStringUntil(terminator);
      if (incomingCmd == "ON"){
        peltier_on = true;
        digitalWrite(LPELTIER_RELAY, HIGH); // sets the digital pin on
        digitalWrite(RPELTIER_RELAY, HIGH); // sets the digital pin on
      }
      if (incomingCmd == "OFF"){
        peltier_on = false;
        digitalWrite(LPELTIER_RELAY, LOW);  // sets the digital pin off
        digitalWrite(RPELTIER_RELAY, LOW);  // sets the digital pin off
      }
      if (incomingCmd == "SETLTEMP"){
        leftDegC = Serial.parseFloat();
      }
      if (incomingCmd == "SETRTEMP"){
        rightDegC = Serial.parseFloat();
      }
    
  if (incomingCmd == "POLL"){
    Serial.print("{\"LEFT\":");
    double c = leftThermocouple.readCelsius();
    if (!isnan(c)){
      Serial.print(c);
    } else{
      Serial.print(-999.9);
    }
    Serial.print(",\"RIGHT\":");
    c = rightThermocouple.readCelsius();
    if (!isnan(c)){
      Serial.print(c);
    } else{
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
  delay(250);
}
