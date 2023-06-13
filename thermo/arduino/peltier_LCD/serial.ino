/*
* Keep serial communication functions here
*/

void handle_request() {  // Handle incoming Serial requests
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