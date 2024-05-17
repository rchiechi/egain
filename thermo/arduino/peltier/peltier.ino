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
#include "peltier.h"


// initialize the Thermocouple
Adafruit_MAX31855 lowerThermocouple(CLK, LOWCS, DO);
Adafruit_MAX31855 upperThermocouple(CLK, HICS, DO);

#define terminator ';'
//int peltier_level = 0;
//int peltier_level = map(power, 0, 99, 0, 255); //This is a value from 0 to 255 that actually controls the MOSFET
int lowerDegC = 25;
int power = 0;
bool peltier_on = false;
bool initialized = false;
double upperTemp = -999.9;
double lowerTemp = -999.9;
uint8_t peltier_state = HEAT;

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

  pinMode(PELTIER_RELAY, OUTPUT);    // sets the digital pin PELTIER_RELAY as output
  pinMode(PELTIER_POLARITY, OUTPUT);    // sets the digital pin PELTIER_POLARITY as output
  pinMode(PELTIER, OUTPUT); // sets the PWM pin as output
  
}

void checkPeltier() {
  Serial.print("\"Peltier_on\":");
  if (peltier_on){
    Serial.print("true");
  }else{
    Serial.print("false");
  }
  Serial.print(", \"Power\":");
  Serial.print(power);
}

void setPower(){
  int setpower = 0;
  double lowerDegK = lowerDegC + 273.15;
  int k = lowerTemp + 273.15;
  setpower = (1 - (lowerDegK / k)) * 100;
  int deltaK = abs(lowerDegK - k);
  if (deltaK < 1){
    setpower += 5;
  }else if (deltaK < 5){
    setpower += 25;
  }else if (deltaK < 10){
    setpower += 50;
  }else{
    setpower = 100;
  }

  String mode = getPeltierPolarity();
  if ( (lowerTemp >= lowerDegC) && (mode == "COOL") ){
    setPeltier(setpower);
  }else if ( (lowerTemp <= lowerDegC) && (mode == "HEAT") ){
    setPeltier(setpower);
  }else {
    setPeltier(0);
  }
}

void setPeltier(int setpower){
  if(setpower > 100){
    power = 100;
  }else if(setpower < 0) {
    power = 0;
  }else {
    power = setpower;
  }
  if (peltier_on){
    int peltier_level = map(power, 0, 100, 0, 255);
    analogWrite(PELTIER, peltier_level); //Write this new value out to the port
  }else{
    analogWrite(PELTIER, 0);
  }
}

void setPeltierPolarity(uint8_t new_state){
  static uint8_t current_state;
  if (current_state != new_state){
    digitalWrite(PELTIER_POLARITY, new_state);
  }
  current_state = digitalRead(PELTIER_POLARITY);
}
  

String getPeltierPolarity() {
  uint8_t polarity = digitalRead(PELTIER_POLARITY);
  if (polarity == HEAT){
    return "HEAT";
  }else if (polarity == COOL ){
    return "COOL";
  }else{
    return "?";
  }
}

void loop() {

  double c = lowerThermocouple.readCelsius();
  if (!isnan(c)){
   lowerTemp = c;
  }
  c = upperThermocouple.readCelsius();
  if (!isnan(c)){
    upperTemp = c;
  }

  String incomingCmd = "null";
  if (Serial.available() > 0) {
      // read the incoming byte:
      incomingCmd = Serial.readStringUntil(terminator);
  }
  if (incomingCmd == "ON"){
    peltier_on = true;
    digitalWrite(PELTIER_RELAY, HIGH); // sets the digital pin PELTIER_RELAY on
  }
  if (incomingCmd == "OFF"){
    peltier_on = false;
    digitalWrite(PELTIER_RELAY, LOW);  // sets the digital pin PELTIER_RELAY off
  }
  if (incomingCmd == "HEAT"){
    setPeltierPolarity(HEAT); // sets the polarity of the peltier
  }
  if (incomingCmd == "COOL"){
    setPeltierPolarity(COOL); // sets the polarity of the peltier
  }
  if (incomingCmd == "SETTEMP"){
    lowerDegC = Serial.parseFloat();
  } 
  if (incomingCmd == "POLL"){
    Serial.print("{\"LOWER\":");
    Serial.print(lowerTemp);
    Serial.print(",\"UPPER\":");
    Serial.print(upperTemp);
    Serial.print(",\"TARGET\":");
    Serial.print(lowerDegC);
    Serial.print(",\"MODE\":\"");
    Serial.print(getPeltierPolarity());
    Serial.print("\",");
    checkPeltier();
    Serial.println("}");
  }
  
  setPower();
  delay(100);

}
