/*
* Keep serial communication functions here
*/

// Terminator expected for Serial input from host
#define terminator ';'

String error_msg = ""; // Global variable to hold the last error message

// Handles setting temperature for a given side
void exec_set_temp(uint8_t side) {
    String valueString = Serial.readStringUntil(';'); // Read the value part
    if (valueString.length() > 0) {
        double newTemp = valueString.toFloat();
        // Optional: Add validation for temperature range here
        setDegC[side] = newTemp;
        // PIDs[side].SetTunings(PIDs[side].GetKp(), PIDs[side].GetKi(), PIDs[side].GetKd()); // Re-assert PID parameters if needed after Setpoint change - check if needed by PID lib
        update = true; // Flag LCD update
    } else {
        // Set the specific error message
        error_msg = "Missing value for SET";
        error_msg += (side == LEFT ? "LEFT" : "RIGHT"); // Append side info
        error_msg += "TEMP";
    }
}

// Handles setting flow (HEAT/COOL) for a given side
void exec_set_flow(uint8_t side, uint8_t direction) {
    // Note: The final ';' for this command was already consumed by readStringUntil
    flow[side] = direction;
    togglePolarity(); // Remember: this has blocking delays!
    update = true; // Flag LCD update
    // NO Serial output here
}

// Handles turning a peltier side on/off
void exec_set_power_state(uint8_t side, bool state) {
    // Note: The final ';' for this command was already consumed by readStringUntil
    peltier_on[side] = state;
    // Ensure setPeltier() has the else { analogWrite(pin, 0); } logic added!
    update = true; // Flag LCD update
    // NO Serial output here
}

// Handles polling status (This function *DOES* write to Serial, as intended)
void exec_poll() {
    // Note: The final ';' for this command was already consumed by readStringUntil
    Serial.print(F("{\"LEFT\":"));
    Serial.print(avgTC[LEFT].getAvg(), 1);
    Serial.print(F(",\"RIGHT\":"));
    Serial.print(avgTC[RIGHT].getAvg(), 1);
    Serial.print(F(",\"LEFTTARGET\":"));
    Serial.print(setDegC[LEFT], 1);
    Serial.print(F(",\"RIGHTTARGET\":"));
    Serial.print(setDegC[RIGHT], 1);
    Serial.print(F(","));
    checkPeltier(); // This function prints the rest (power, flow)
    // Check if an error message exists BEFORE closing the JSON object
    if (!error_msg.isEmpty()) { // Use isEmpty() for clarity
        Serial.print(F(",\"ERROR\":\"")); // Add the JSON key for the error
        Serial.print(error_msg);         // Print the actual error message
        Serial.print(F("\""));           // Close the error string in JSON
        error_msg = ""; // Clear the error message string after reporting it
    }
    Serial.println(F("}"));
}


// --- Main Serial Command Dispatcher ---

void handle_request() {
    if (Serial.available() == 0) {
        return; // Nothing to process
    }

    String incomingCmd = Serial.readStringUntil(';'); // Read the command part

    if (incomingCmd.length() == 0) {
        return; // Ignore empty commands or timeouts
    }

    // Use an if/else if structure for dispatching
    if (incomingCmd == "INIT") { // This command *DOES* write to Serial
        Serial.print(F("{\"INITIALIZED\":"));
        Serial.print(initialized ? F("true") : F("false"));
        Serial.println(F("}"));
    }
    else if (incomingCmd == "LEFTON")      { exec_set_power_state(LEFT, true); }
    else if (incomingCmd == "LEFTOFF")     { exec_set_power_state(LEFT, false); }
    else if (incomingCmd == "RIGHTON")     { exec_set_power_state(RIGHT, true); }
    else if (incomingCmd == "RIGHTOFF")    { exec_set_power_state(RIGHT, false); }
    else if (incomingCmd == "SETLEFTTEMP") { exec_set_temp(LEFT); }
    else if (incomingCmd == "SETRIGHTTEMP"){ exec_set_temp(RIGHT); }
    else if (incomingCmd == "LEFTHEAT")    { exec_set_flow(LEFT, HEAT); }
    else if (incomingCmd == "LEFTCOOL")    { exec_set_flow(LEFT, COOL); }
    else if (incomingCmd == "RIGHTHEAT")   { exec_set_flow(RIGHT, HEAT); }
    else if (incomingCmd == "RIGHTCOOL")   { exec_set_flow(RIGHT, COOL); }
    else if (incomingCmd == "SHOWSTATUS")  { state = show_summary; update = true; }
    else if (incomingCmd == "POLL")        { exec_poll(); } // This command *DOES* write to Serial
    else { // Handle unknown command
            error_msg = "Unknown command: " + incomingCmd; // Use '+' for concatenation
            // Consume potential arguments for the unknown command
            while (Serial.available() > 0 && Serial.read() != ';');
        }
}







// void handle_request() {  // Handle incoming Serial requests
//   // read the incoming byte:
//   String incomingCmd = Serial.readStringUntil(terminator);
// 
//   if (incomingCmd == "INIT") {
//     Serial.print(F("{\"INITIALIZED\":"));
//     if (initialized) {
//       Serial.print(F("true"));
//     } else {
//       Serial.print(F("false"));
//     };
//     Serial.println(F("}"));
//   }
// 
//   if (incomingCmd == "LEFTON") {
//     peltier_on[LEFT] = true;
//   }
//   if (incomingCmd == "LEFTOFF") {
//     peltier_on[LEFT] = false;
//     // power[LEFT] = 0;
//   }
//   if (incomingCmd == "RIGHTON") {
//     peltier_on[RIGHT] = true;
//   }
//   if (incomingCmd == "RIGHTOFF") {
//     peltier_on[RIGHT] = false;
//     // power[RIGHT] = 0;
//   }
//   if (incomingCmd == "SETLEFTTEMP") {
//     setDegC[LEFT] = Serial.parseFloat();
//   }
//   if (incomingCmd == "SETRIGHTTEMP") {
//     setDegC[RIGHT] = Serial.parseFloat();
//   }
//   if (incomingCmd == "LEFTHEAT") {
//     flow[LEFT] = HEAT;
//     togglePolarity();
//   }
//   if (incomingCmd == "LEFTCOOL") {
//     flow[LEFT] = COOL;
//     togglePolarity();
//   }
//   if (incomingCmd == "RIGHTHEAT") {
//     flow[RIGHT] = HEAT;
//     togglePolarity();
//   }
//   if (incomingCmd == "RIGHTCOOL") {
//     flow[RIGHT] = COOL;
//     togglePolarity();
//   }
//   if (incomingCmd == "SHOWSTATUS") {
//     state = show_summary;
//   }
// 
//   if (incomingCmd == "POLL") {
//     Serial.print(F("{\"LEFT\":"));
//     Serial.print(avgTC[LEFT].getAvg());
//     Serial.print(F(",\"RIGHT\":"));
//     Serial.print(avgTC[RIGHT].getAvg());
//     Serial.print(F(","));
//     Serial.print(F("\"LEFTTARGET\":"));
//     Serial.print(setDegC[LEFT]);
//     Serial.print(F(","));
//     Serial.print(F("\"RIGHTTARGET\":"));
//     Serial.print(setDegC[RIGHT]);
//     Serial.print(F(","));
//     checkPeltier();
//     Serial.println(F("}"));
//   }
// }


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