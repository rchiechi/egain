/*
* Keep serial communication functions here
*/

void handle_request() {  // Handle incoming Serial requests
  // read the incoming byte:
  String incomingCmd = Serial.readStringUntil(terminator);

  if (incomingCmd == "INIT") {
    Serial.print(F("{\"INITIALIZED:\":"));
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
  }
  if (incomingCmd == "RIGHTON") {
    peltier_on[RIGHT] = true;
  }
  if (incomingCmd == "RIGHTOFF") {
    peltier_on[RIGHT] = false;
  }
  if (incomingCmd == "SETLEFTTEMP") {
    setDegC[LEFT] = Serial.parseFloat();
  }
  if (incomingCmd == "SETRIGHTTEMP") {
    setDegC[RIGHT] = Serial.parseFloat();
  }
  if (incomingCmd == "LEFTHEAT") {
    flow[LEFT] = HEAT;
  }
  if (incomingCmd == "LEFTCOOL") {
    flow[LEFT] = COOL;
  }
  if (incomingCmd == "RIGHTHEAT") {
    flow[RIGHT] = HEAT;
  }
  if (incomingCmd == "RIGHTCOOL") {
    flow[RIGHT] = COOL;
  }

  if (incomingCmd == "POLL") {
    Serial.print(F("{\"LEFT\":"));
    Serial.print(avgTC[LEFT].getAverage());
    Serial.print(F(",\"RIGHT\":"));
    Serial.print(avgTC[RIGHT].getAverage());
    Serial.print(F(","));
    Serial.print(F("\"LTARGET\":"));
    Serial.print(setDegC[LEFT]);
    Serial.print(F(","));
    Serial.print(F("\"RTARGET\":"));
    Serial.print(setDegC[RIGHT]);
    Serial.print(F(","));
    checkPeltier();
    Serial.println(F("}"));
  }
}

void checkPeltier() {
  Serial.print(F("\"Peltier_on\":["));
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
  Serial.print(F(", \"LeftPower\":"));
  Serial.print(power[LEFT]);
  Serial.print(F(", \"RightPower\":"));
  Serial.print(power[RIGHT]);
}