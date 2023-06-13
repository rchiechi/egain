/* 
* Keep peltier control functions here
*/

// Convenience function to invert a digital pin
inline void digitalToggle(byte pin) {  
  digitalWrite(pin, !digitalRead(pin));
}

/*
* Computhe power of a peltier based on the value of setDegC[side]
* and then call the setpower function
*/
void setPeltier(int _side) {
  int _setpower = 0;
  double c = Thermocouples[_side].readCelsius();
  if (!isnan(c) && peltier_on[_side]) {
    double DegK = setDegC[_side] + 273.15;
    int k = c + 273.15;
    _setpower = (1 - (DegK / k)) * 100;
    int deltaK = abs(DegK - k);
    if (deltaK < 5) {
      _setpower += 50;
    } else if (deltaK < 10) {
      _setpower += 75;
    } else {
      _setpower = 100;
    }
    if (flow[_side] == COOL) {
      if (c >= setDegC[_side]) {
        setpower(_side, _setpower);
      } else {
        setpower(_side, 0);
      }
    }
    if (flow[_side] == HEAT) {
      if (c <= setDegC[_side]) {
        setpower(_side, _setpower);
      } else {
        setpower(_side, 0);
      }
    }
  }
}

/*
* Set the power of a peltier
*/
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
    uint8_t peltier_level = map(power, 0, 100, 0, 255);
    analogWrite(peltier_addr[_side], peltier_level);  //Write this new value out to the port
  } else {
    analogWrite(peltier_addr[_side], 0);
  }
}

/*
* Set the on/off state of a pletier based on the value of peltier_on
*/
void togglePeltier() {
  for (uint8_t side = LEFT; side < RIGHT; ++side) {
    if (peltier_on[side]) {
      digitalWrite(peltier_relay[side], HIGH);
    }
    if (peltier_on[side]) {
      digitalWrite(peltier_relay[side], HIGH);
    }
  }
  if (!peltier_on[LEFT] & !peltier_on[RIGHT]) {
    for (uint8_t side = LEFT; side < RIGHT; ++side) {
      digitalWrite(peltier_relay[side], LOW);
    }
  }
}

/*
* Switch off both peltier relays and then 
* Set the polarity of a peltier based on the value of flow[side]
*/
void setPolarity(uint8_t _side, uint8_t _flow) {
  // Set both relays to off
  for (int side = LEFT; side < RIGHT; ++side) {
    digitalWrite(peltier_relay[side], LOW);
  }
  delay(100);
  for (int side = LEFT; side < RIGHT; ++side) {
    digitalWrite(peltier_polarity[_side], flow[_side]);
  }
  delay(100);
  togglePeltier();
}

uint8_t getPolarity(uint8_t _side) {
  return digitalRead(peltier_polarity[_side]);
}