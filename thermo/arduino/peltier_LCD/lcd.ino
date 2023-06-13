/*
* Keep LCD-related functions here
*/



//! Return a bitmask of clicked buttons.
/*!
  Examine the bitmask of buttons which are currently pressed and compare against
  the bitmask of which buttons were pressed last time the function was called.
  If a button transitions from pressed to released, return it in the bitmask.

  \return the bitmask of clicked buttons
*/
void read_button_clicks() {
  static uint8_t last_buttons = 0;

  uint8_t buttons = lcd.readButtons();
  clicked_buttons = (last_buttons ^ buttons) & (~buttons);
  last_buttons = buttons;
}

//! Initial state, draw the splash screen.
void begin_splash_screen() {
  lcd.clear();
  lcd.setBacklight(ON);
  lcd.print(F("PELTIER CONTROLS"));
  state = animate_splash_screen;
}

//! Animate the splash screen.
/*!
  Blink the text "PRESS SELECT" and wait for the user to press the select button.
*/
void animate_splash_screen() {
  static boolean blink = true;
  static unsigned long last_blink_time;

  if (time - last_blink_time >= 1000) {
    lcd.setCursor(0, 1);
    if (blink) {
      lcd.write(0x7E);
      lcd.print(F(" PRESS SELECT "));
      lcd.write(0x7F);
    } else {
      lcd.print(F("                "));
    }
    blink = !blink;
    last_blink_time = time;
  }

  if (clicked_buttons & BUTTON_SELECT) {
    lcd.clear();
    state = show_summary;
  }
}

void show_set_menu() {
  static bool update = true;
  static uint8_t last_menu_idx = 0;
  lcd.setBacklight(ON);
  lcd.setCursor(0, 0);
  lcd.print(F("R: "));
  if (peltier_on[RIGHT]) {
    if (flow[RIGHT] == HEAT) {
      lcd.write(HEAT_IDX);
    } else if (flow[RIGHT] == COOL) {
      lcd.write(COOL_IDX);
    }
  } else {
    lcd.write(X_IDX);
  }
  lcd.setCursor(0, 1);
  lcd.print(F("L: "));
  if (peltier_on[LEFT]) {
    if (flow[LEFT] == HEAT) {
      lcd.write(HEAT_IDX);
    } else if (flow[LEFT] == COOL) {
      lcd.write(COOL_IDX);
    }
  } else {
    lcd.write(X_IDX);
  }

  // lcd.write(DEGREE_ICON_IDX);
  // lcd.print(F("C"));
  if (clicked_buttons) {
    lcd.clear();
  }
  if (clicked_buttons & BUTTON_SELECT) {
    state = show_summary;
  } else if ((clicked_buttons & BUTTON_DOWN) && (selected_menu_idx == 0)) {
    ++selected_menu_idx;
  } else if (clicked_buttons & BUTTON_UP) {
    --selected_menu_idx;
  } else {
    state = show_set_menu;
  }
}

void show_summary() {
  static double last_lc = 0;
  static double last_rc = 0;
  static bool update = true;

  // Read the temperature as Celsius:
  double lc = avgTC[LEFT].getAverage();
  double rc = avgTC[RIGHT].getAverage();

  if (update) {
    lcd.setBacklight(ON);
    lcd.setCursor(0, 0);
    if (peltier_on[LEFT]) {
      if (flow[LEFT] == HEAT) {
        lcd.write(HEAT_IDX);
      } else if (flow[LEFT] == COOL) {
        lcd.write(COOL_IDX);
      }
    } else {
      lcd.write(X_IDX);
    }
    lcd.print(F("R: "));
    lcd.print(lc, 1);
    lcd.write(0x7E);
    lcd.print(setDegC[LEFT], 1);
    lcd.print(" ");
    lcd.write(DEGREE_ICON_IDX);
    lcd.print(F("C "));
    lcd.setCursor(0, 1);
    if (peltier_on[RIGHT]) {
      if (flow[RIGHT] == HEAT) {
        lcd.write(HEAT_IDX);
      } else if (flow[RIGHT] == COOL) {
        lcd.write(COOL_IDX);
      }
    } else {
      lcd.write(X_IDX);
    }
    lcd.print(F("L: "));
    lcd.print(rc, 1);
    lcd.write(0x7E);
    lcd.print(setDegC[RIGHT], 1);
    lcd.print(" ");
    lcd.write(DEGREE_ICON_IDX);
    lcd.print(F("C "));
  }
  update = false;

  if (abs(last_lc - lc) > 0.5) {
    last_lc = lc;
    update = true;
  }
  if (abs(last_rc - rc) > 0.5) {
    last_rc = rc;
    update = true;
  }
  if (clicked_buttons) {
    update = true;
    if (clicked_buttons & BUTTON_SELECT) {
      lcd.clear();
      selected_menu_idx = 0;
      state = show_set_menu;
    } else {
      state = show_summary;
    }
    if (clicked_buttons & BUTTON_UP) {
      setDegC[LEFT] = setDegC[LEFT] + 0.5;
    }
    if (clicked_buttons & BUTTON_DOWN) {
      setDegC[LEFT] = setDegC[LEFT] - 0.5;
    }
    if (clicked_buttons & BUTTON_RIGHT) {
      setDegC[RIGHT] = setDegC[RIGHT] + 0.5;
    }
    if (clicked_buttons & BUTTON_LEFT) {
      setDegC[RIGHT] = setDegC[RIGHT] - 0.5;
    }
  }
}
