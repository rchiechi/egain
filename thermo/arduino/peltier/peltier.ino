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

#include <SPI.h>
#include "Adafruit_MAX31855.h"

// Default connection is using software SPI, but comment and uncomment one of
// the two examples below to switch between software SPI and hardware SPI:

// Example creating a thermocouple instance with software SPI on any three
// digital IO pins.
#define LOWDO   3
#define LOWCS   4
#define LOWCLK  5
#define HIDO   8
#define HICS   9
#define HICLK  10
// initialize the Thermocouple
Adafruit_MAX31855 lowerThermocouple(LOWCLK, LOWCS, LOWDO);
Adafruit_MAX31855 upperThermocouple(HICLK, HICS, HIDO);

#define PELTIER 6
#define PELTIER_RELAY 13

// Example creating a thermocouple instance with hardware SPI
// on a given CS pin.
//#define MAXCS   10
//Adafruit_MAX31855 thermocouple(MAXCS);

// Example creating a thermocouple instance with hardware SPI
// on SPI1 using specified CS pin.
//#define MAXCS   10
//Adafruit_MAX31855 thermocouple(MAXCS, SPI1);

#define terminator ';'
//int peltier_level = 0;
//int peltier_level = map(power, 0, 99, 0, 255); //This is a value from 0 to 255 that actually controls the MOSFET
int lowerDegC = 25;
bool peltier_on = false;
bool initialized = false;

void setup() {
  Serial.begin(9600);

  while (!Serial) delay(1); // wait for Serial on Leonardo/Zero, etc

  // Serial.println("{\"message\":\"MAX31855 test\"}");
  // wait for MAX chip to stabilize
  delay(500);
  Serial.println("{\"message\":\"Lower Thermocouple Initializing\"}");
  if (!lowerThermocouple.begin()) {
    Serial.println("{\"message\":\"ERROR\"}");
    while (1) delay(10);
  }
    Serial.println("{\"message\":\"Upper Thermocouple Initializing\"}");
  if (!upperThermocouple.begin()) {
    Serial.println("{\"message\":\"ERROR\"}");
    while (1) delay(10);
  }
  Serial.println("{\"message\":\"Done initializing\"}");
  initialized = true;

  pinMode(13, OUTPUT);    // sets the digital pin 13 as output
  
}


void checkPeltier() {
  Serial.print("\"Peltier_on\":");
  if (peltier_on){
    Serial.print("true");
  }else{
    Serial.print("false");
  }
}

void setLower(){
//  if(power > 99) power = 99;
//  if(power < 0) power = 0;
  double c = lowerThermocouple.readCelsius();
  if (c >= lowerDegC){
    setPeltier(50);
  }
  else {
    setPeltier(0);
  }

}

void setPeltier(int power){
  if (peltier_on){
    int peltier_level = map(power, 0, 99, 0, 255);
    analogWrite(PELTIER, peltier_level); //Write this new value out to the port
  }else{
    analogWrite(PELTIER, 0);
  }
}

void loop() {

  if (Serial.available() > 0) {
      // read the incoming byte:
      String incomingCmd = Serial.readStringUntil(terminator);
      if (incomingCmd == "ON"){
        peltier_on = true;
        digitalWrite(13, HIGH); // sets the digital pin 13 on
      }
      if (incomingCmd == "OFF"){
        peltier_on = false;
        digitalWrite(13, LOW);  // sets the digital pin 13 off
      }
      if (incomingCmd == "SETTEMP"){
        lowerDegC = Serial.parseFloat();
      }
    
  if (incomingCmd == "POLL"){
    Serial.print("{\"LOWER\":");
    double c = lowerThermocouple.readCelsius();
    if (!isnan(c)){
      Serial.print(c);
    } else{
      Serial.print(-100.0);
    }
    Serial.print(",\"UPPER\":");
    c = upperThermocouple.readCelsius();
    if (!isnan(c)){
      Serial.print(c);
    } else{
      Serial.print(-100.0);
    }
    Serial.print(",");
    Serial.print("\"TARGET\":");
    Serial.print(lowerDegC);
    Serial.print(",");
    checkPeltier();
    Serial.println("}");
  }
  }
  setLower();
  delay(250);

}
