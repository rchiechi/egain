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
#include <PID_v1.h>
#include "Adafruit_MAX31855.h"
#include "peltier.h"


// initialize the Thermocouple
Adafruit_MAX31855 lowerThermocouple(CLK, LOWCS, DO);
Adafruit_MAX31855 upperThermocouple(CLK, HICS, DO);

#define terminator ';'
//int peltier_level = 0;
//int peltier_level = map(power, 0, 99, 0, 255); //This is a value from 0 to 255 that actually controls the MOSFET
double lowerTarget = 25;
double PID_value = 0;
bool peltier_on = false;
bool initialized = false;
double upperTemp = -999.9;
double lowerTemp = -999.9;
uint8_t peltier_state = HEAT;

//PID constants
double Kp = 9.1;
double Ki = 0.3;
double Kd = 1.8;

PID heaterPID(&lowerTemp, &PID_value, &lowerTarget, Kp, Ki, Kd, DIRECT);
PID coolerPID(&lowerTemp, &PID_value, &lowerTarget, Kp, Ki, Kd, REVERSE);

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
  int power = map(PID_value, 0, 255, 0, 100);
  Serial.print("\"Peltier_on\":");
  if (peltier_on){
    Serial.print("true");
  }else{
    Serial.print("false");
  }
  Serial.print(",\"Power\":");
  Serial.print(power);
  Serial.print(",\"PID\":");
  Serial.print(PID_value);
}

void setPID(){
  String mode = getPeltierPolarity();
  if (mode == "COOL"){
    coolerPID.Compute();
  }else if (mode == "HEAT"){
    heaterPID.Compute();
  }else {
    PID_value = -1;
  }
  if(PID_value < 0)
  {    PID_value = 0;    }
  if(PID_value > 255)  
  {    PID_value = 255;  }
  analogWrite(PELTIER, PID_value);
}

// void setPower(){
//   float lowerTargetK = lowerTarget + 273.15;
//   float lowerTempK = lowerTemp + 273.15;
//   // String mode = getPeltierPolarity();
//   // if (mode == "COOL"){
//   //   setCoolPower(lowerTargetK, lowerTempK);
//   // }else if (mode == "HEAT"){
//   //   setHeatPower(lowerTargetK, lowerTempK);
//   // }
//   setPID(float lowerTargetK, float lowerTempK);
// }

// void setPID(){
//   static float previous_error, elapsedTime, timePrev;
//   static float Time = millis();
//   static int PID_p = 0;
//   static int PID_i = 0;
//   static int PID_d = 0;
//   
//   float lowerTargetK = lowerTarget + 273.15;
//   float lowerTempK = lowerTemp + 273.15;
//   
//   // calculate the error between the setpoint and the real value
//   float PID_error = lowerTargetK - lowerTempK;
//   
//   // keep PID_error positive when approaching set point
//   String mode = getPeltierPolarity();
//   if (mode == "COOL"){
//     PID_error = -1 * PID_error;
//   }
//   
//   //Calculate the P value
//   PID_p = kp * PID_error;
// 
//   //Calculate the I value in a range on +-3
//   if(-3 < PID_error < 3)
//   {
//     PID_i = PID_i + (ki * PID_error);
//   }
//   
//   //For derivative we need real time to calculate speed change rate
//   timePrev = Time;                            // the previous time is stored before the actual time read
//   Time = millis();                            // actual time read
//   elapsedTime = (Time - timePrev) / 1000; 
//   //Now we can calculate the D value
//   PID_d = kd*((PID_error - previous_error)/elapsedTime);
//   //Final total PID value is the sum of P + I + D
//   PID_value = PID_p + PID_i + PID_d;
//   
//   //We define PWM range between 0 and 255
//   if(PID_value < 0)
//   {    PID_value = 0;    }
//   if(PID_value > 255)  
//   {    PID_value = 255;  }
//   //Now we can write the PWM signal to the mosfet
//   analogWrite(PELTIER, PID_value);
//   previous_error = PID_error;     //Remember to store the previous error for next loop.
// }

// void setHeatPower(float lowerTargetK, float lowerTempK){
//   int setpower = 0;
//   float deltaK = abs(lowerTargetK - lowerTempK);
//   setpower = (1 - (lowerTempK / lowerTargetK)) * 100;
//   if ((deltaK > 5) && (deltaK < 10)){
//     setpower += 10;
//   }else if (deltaK < 20){
//     setpower += 25;
//   }else{
//     setpower = 100;
//   }
//   if (lowerTemp < lowerTarget){
//     setPeltier(setpower);
//   }else {
//     setPeltier(0);
//   }
// }
// 
// void setCoolPower(float lowerTargetK, float lowerTempK){
//   int setpower = 0;
//   float deltaK = abs(lowerTargetK - lowerTempK);
//   setpower = (1 - (lowerTargetK / lowerTempK)) * 200;
//   if ((deltaK > 1) && (deltaK < 5)){
//     setpower += 50;
//   // }else if (deltaK < 10){
//   //   setpower += 50;
//   }else{
//     setpower = 100;
//   }
//   if (lowerTemp > lowerTarget){
//     setPeltier(setpower);
//   }else {
//     setPeltier(0);
//   }
// }
// 
// void setPeltier(int setpower){
//   if(setpower > 100){
//     power = 100;
//   }else if(setpower < 0) {
//     power = 0;
//   }else {
//     power = setpower;
//   }
//   if (peltier_on){
//     int peltier_level = map(power, 0, 100, 0, 255);
//     analogWrite(PELTIER, peltier_level); //Write this new value out to the port
//   }else{
//     analogWrite(PELTIER, 0);
//   }
// }

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
  static int loop_counter;
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
    lowerTarget = Serial.parseFloat();
  } 
  if (incomingCmd == "POLL"){
    loop_counter = 0;
    Serial.print("{\"LOWER\":");
    Serial.print(lowerTemp);
    Serial.print(",\"UPPER\":");
    Serial.print(upperTemp);
    Serial.print(",\"TARGET\":");
    Serial.print(lowerTarget);
    Serial.print(",\"MODE\":\"");
    Serial.print(getPeltierPolarity());
    Serial.print("\",");
    checkPeltier();
    Serial.print(",\"INITIALIZED\":");
    Serial.print(initialized);
    Serial.println("}");
  }
  if (++loop_counter > 600) {
    // communication with instrument lost
    peltier_on = false;
    digitalWrite(PELTIER_RELAY, LOW);
  }
  setPID();
  delay(100);

}
