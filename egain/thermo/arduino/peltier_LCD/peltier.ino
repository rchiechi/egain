/* 
* Keep peltier control functions here
*/

// Convenience function to invert a digital pin
inline void digitalToggle(byte pin) {
  digitalWrite(pin, !digitalRead(pin));
}

/* NEW PID LOGIC */

void setPeltier(int _side){
  if (peltier_on[_side]){
    PIDs[_side].Compute();
    analogWrite(peltier_addr[_side], PID_value[_side]);
  }
  else {
    analogWrite(peltier_addr[_side], 0); // Explicitly set PWM to 0
    // Optional: reset the PID output variable
    PID_value[_side] = 0.0;
  }
}

/* OLD PELTIER LOGIC


void setPeltier(int _side) {
  int _setpower = 0;
  double c = Thermocouples[_side].readCelsius();
  if (!isnan(c) && peltier_on[_side]) {
    double DegK = setDegC[_side] + 273.15;
    int k = c + 273.15;
    int deltaK = 0;
    if (flow[_side] == COOL) {
      if (c < setDegC[_side]) {
        _setpower = 0;
      } else {
        deltaK = k - DegK;
        _setpower = (1 - (DegK / k)) * 2500;
      }
    }
    if (flow[_side] == HEAT) {
      if (c > setDegC[_side]) {
        _setpower = 0;
      } else {
        deltaK = DegK - k;
        _setpower = (1 - (k / DegK)) * 2500;
      }
    }
    // if (deltaK < 2) {
    //   _setpower = 0;
    // } else if (deltaK < 5) {
    //   _setpower += 25;
    // } 
    // else if (deltaK < 10) {
    //   _setpower += 50;
    // }
    if (_setpower > 100){
      _setpower = 100;
    }
    setpower(_side, _setpower);
    power[_side] = _setpower;
  }
}


void setpower(uint8_t _side, uint8_t _power) {
  uint8_t* set_power;
  if (_power > 100) {
    set_power = 100;
  } else if (_power < 0) {
    set_power = 0;
  } else {
    set_power = _power;
  }
  if (peltier_on[_side]) {
    uint8_t peltier_level = map(set_power, 0, 100, 0, 255);
    analogWrite(peltier_addr[_side], peltier_level);  //Write this new value out to the port
  } else {
    analogWrite(peltier_addr[_side], 0);
  }
}
/*

/*
* Set the on/off state of a peltier based on the value of peltier_on
*/
void togglePeltier() {
  for (uint8_t side = LEFT; side <= RIGHT; ++side) {
    if (peltier_on[side]) {
      digitalWrite(peltier_relay[side], HIGH);
    }
    // With only one power supply, this statement will turn both off
    // if (!peltier_on[side]) {
    //   digitalWrite(peltier_relay[side], LOW);
    // }
  }
  if (!peltier_on[LEFT] && !peltier_on[RIGHT]) {
    for (uint8_t side = LEFT; side <= RIGHT; ++side) {
      digitalWrite(peltier_relay[side], LOW);
    }
  }
}

/*
* Switch off both peltier relays and then 
* Set the polarity of a peltier based on the value of flow[side]
*/
void togglePolarity() {
  static uint8_t current_state;
  // Set both relays to off
  for (int side = LEFT; side <= RIGHT; ++side) {
    digitalWrite(peltier_relay[side], LOW);
  }
  delay(10);
  // Set flow direction
  for (int side = LEFT; side <= RIGHT; ++side) {
    digitalWrite(peltier_polarity[side], flow[side]);
  }
  delay(10);
  // Sync PID controllers with flow direction
  for (int side = LEFT; side <= RIGHT; ++side) {
    current_state = getPolarity(side);
    if (current_state == HEAT){
      PIDs[side].SetControllerDirection(DIRECT);
    }else if (current_state == COOL ){
      PIDs[side].SetControllerDirection(REVERSE);
    }
  }
  delay(10);
  
  togglePeltier();
}

uint8_t getPolarity(uint8_t _side) {
  return digitalRead(peltier_polarity[_side]);
}