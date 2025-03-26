/*
* Keep serial communication functions here
*/

// Terminator expected for Serial input from host
#define terminator ';'

void handle_request() {  // Handle incoming Serial requests
  // read the incoming byte:
  String incomingCmd = Serial.readStringUntil(terminator);

  if (incomingCmd == "INIT") {
    Serial.print(F("{\"INITIALIZED\":"));
    if (initialized) {
      Serial.print(F("true"));
    } else {
      Serial.print(F("false"));
    };
    Serial.println(F("}"));
  }

  if (incomingCmd == "LEFTON") {
    peltier_on[LEFT] = true;
  }
  if (incomingCmd == "LEFTOFF") {
    peltier_on[LEFT] = false;
    // power[LEFT] = 0;
  }
  if (incomingCmd == "RIGHTON") {
    peltier_on[RIGHT] = true;
  }
  if (incomingCmd == "RIGHTOFF") {
    peltier_on[RIGHT] = false;
    // power[RIGHT] = 0;
  }
  if (incomingCmd == "SETLEFTTEMP") {
    setDegC[LEFT] = Serial.parseFloat();
  }
  if (incomingCmd == "SETRIGHTTEMP") {
    setDegC[RIGHT] = Serial.parseFloat();
  }
  if (incomingCmd == "LEFTHEAT") {
    flow[LEFT] = HEAT;
    togglePolarity();
  }
  if (incomingCmd == "LEFTCOOL") {
    flow[LEFT] = COOL;
    togglePolarity();
  }
  if (incomingCmd == "RIGHTHEAT") {
    flow[RIGHT] = HEAT;
    togglePolarity();
  }
  if (incomingCmd == "RIGHTCOOL") {
    flow[RIGHT] = COOL;
    togglePolarity();
  }
  if (incomingCmd == "SHOWSTATUS") {
    state = show_summary;
  }

  if (incomingCmd == "POLL") {
    Serial.print(F("{\"LEFT\":"));
    Serial.print(avgTC[LEFT].getAvg());
    Serial.print(F(",\"RIGHT\":"));
    Serial.print(avgTC[RIGHT].getAvg());
    Serial.print(F(","));
    Serial.print(F("\"LEFTTARGET\":"));
    Serial.print(setDegC[LEFT]);
    Serial.print(F(","));
    Serial.print(F("\"RIGHTTARGET\":"));
    Serial.print(setDegC[RIGHT]);
    Serial.print(F(","));
    checkPeltier();
    Serial.println(F("}"));
  }
}


void checkPeltier() {
  static int power[] = {0, 0};
  for (uint8_t side = LEFT; side <= RIGHT; ++side) {
    power[side] = map(PID_value[side], 0, 255, 0, 100);
  }
  Serial.print(F("\"PELTIERON\":["));
  if (peltier_on[LEFT]) {
    Serial.print(F("true"));
  } else {
    Serial.print(F("false"));
  }
  Serial.print(F(", "));
  if (peltier_on[RIGHT]) {
    Serial.print(F("true"));
  } else {
    Serial.print(F("false"));
  }
  Serial.print(F("]"));
  Serial.print(F(", \"LEFTPOWER\":"));
  Serial.print(power[LEFT]);
  Serial.print(F(", \"RIGHTPOWER\":"));
  Serial.print(power[RIGHT]);

  Serial.print(F(", \"LEFTFLOW\":\""));
  if (flow[LEFT] == HEAT){
    Serial.print(F("HEAT"));
  } else if (flow[LEFT] == COOL){
    Serial.print(F("COOL"));
  }
  Serial.print(F("\""));

  Serial.print(F(", \"RIGHTFLOW\":\""));
  if (flow[RIGHT] == HEAT){
    Serial.print(F("HEAT"));
  } else if (flow[RIGHT] == COOL){
    Serial.print(F("COOL"));
  }
  Serial.print(F("\""));
 
}