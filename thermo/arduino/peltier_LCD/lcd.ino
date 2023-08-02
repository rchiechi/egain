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

  uint8_t buttons = lcd1.readButtons();
  clicked_buttons = (last_buttons ^ buttons) & (~buttons);
  last_buttons = buttons;
}

// start screen which prompts the user to press select to start
void start_screen() {
  lcd.setCursor(0, 0);
  lcd.write(0x7E);
  lcd.print(F(" PRESS SELECT "));
  lcd.write(0x7F);
  lcd.setCursor(0, 1);
  lcd.print("    *SELECT*");
  // switches to the next screen
  if (clicked_buttons & BUTTON_SELECT) {
    state = left_or_right;
    delay(200);
    lcd.clear();
  }
}

// user chooses to use either the left or right peltier
void left_or_right() {
  static int top_pointer = 0;
  static int bottom_pointer = 0;
  lcd.setCursor(0, 0);
  lcd.print("    LEFT ");
  // points to the top option if user has selected it
  if (top_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("    RIGHT ");
  // points to the bottom option if user has selected it
  if (bottom_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 0);
    lcd.print(" ");
  }
  // sees what option user has selected to point at
  if (clicked_buttons & BUTTON_UP) {
    top_pointer = 1;
    bottom_pointer = 0;
  }
  if (clicked_buttons & BUTTON_DOWN) {
    bottom_pointer = 1;
    top_pointer = 0;
  }
  // switches screen based on what the user has selected
  if(top_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    state = on_offL;
    delay(300);
    lcd.clear();
  }
  if(bottom_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    state = on_offR;
    delay(300);
    lcd.clear();
  }

}

// user decides to switch the left side on or off
void on_offL() {
  static int top_pointer = 0;
  static int bottom_pointer = 0;
  lcd.setCursor(0, 0);
  lcd.print("     ON ");
  // points to the top option if user has selected it
  if (top_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     OFF ");
  // points to the bottom option if user has selected it
  if (bottom_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(8, 0);
    lcd.print(" ");
  }
  // sees what option user has selected to point at
  if (clicked_buttons & BUTTON_UP) {
    top_pointer = 1;
    bottom_pointer = 0;
  }
  if (clicked_buttons & BUTTON_DOWN) {
    bottom_pointer = 1;
    top_pointer = 0;
  }
  // switches screen based on what the user has selected
  if(top_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    peltier_on[LEFT] = true;
    state = L_heat_or_cool;
    delay(300);
    lcd.clear(); 
  }
  if(bottom_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    peltier_on[LEFT] = false;
    state = home_and_summary;
    delay(300);
    lcd.clear();
  }
  // goes to previous screen if user selects the left button
  if (clicked_buttons & BUTTON_LEFT) {
    state = left_or_right;
    delay(300);
    lcd.clear(); 
  }

 }



// user decides to switch the right side on or off
void on_offR() {
  static int top_pointer = 0;
  static int bottom_pointer = 0;
  lcd.setCursor(0, 0);
  lcd.print("     ON ");
  // points to the top option if user has selected it
  if (top_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     OFF ");
  // points to the bottom option if user has selected it
  if (bottom_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(8, 0);
    lcd.print(" ");
  }
  // sees what option user has selected to point at
  if (clicked_buttons & BUTTON_UP) {
    top_pointer = 1;
    bottom_pointer = 0;
  }
  if (clicked_buttons & BUTTON_DOWN) {
    bottom_pointer = 1;
    top_pointer = 0;
  }
  // switches screen based on what the user has selected
  if(top_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    peltier_on[RIGHT] = true;
    state = R_heat_or_cool;
    delay(300);
    lcd.clear(); 
  }
  if(bottom_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    peltier_on[RIGHT] = false;
    state = home_and_summary;
    delay(300);
    lcd.clear();
  }
  // goes to previous screen if user selects the left button
  if (clicked_buttons & BUTTON_LEFT) {
    state = left_or_right;
    delay(300);
    lcd.clear(); 
  }
}

// user decides to switch the left side to heat or cool
void L_heat_or_cool() {
  static int top_pointer = 0;
  static int bottom_pointer = 0;
  lcd.setCursor(0, 0);
  lcd.print("     HEAT ");
  // points to the top option if user has selected it
  if (top_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     COOL ");
  // points to the bottom option if user has selected it
  if (bottom_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 0);
    lcd.print(" ");
  }
  // sees what option user has selected to point at
  if (clicked_buttons & BUTTON_UP) {
    top_pointer = 1;
    bottom_pointer = 0;
  }
  if (clicked_buttons & BUTTON_DOWN) {
    bottom_pointer = 1;
    top_pointer = 0;
  }
  // switches screen based on what the user has selected
  if(top_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    flow[LEFT] = HEAT;
    state = set_LEFT_temp;
    delay(300);
    lcd.clear();
  }
  if(bottom_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    flow[LEFT] = COOL;
    state = set_LEFT_temp;
    delay(300);
    lcd.clear();
  }
  // goes to previous screen if user selects the left button
  if (clicked_buttons & BUTTON_LEFT) {
    state = on_offL;
    delay(300);
    lcd.clear(); 
  }
}

// user decides to switch the right side to heat or cool
void R_heat_or_cool() {
  static int top_pointer = 0;
  static int bottom_pointer = 0;
  lcd.setCursor(0, 0);
  lcd.print("     HEAT ");
  // points to the top option if user has selected it
  if (top_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     COOL ");
  // points to the bottom option if user has selected it
  if (bottom_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 0);
    lcd.print(" ");
  }
  // sees what option user has selected to point at
  if (clicked_buttons & BUTTON_UP) {
    top_pointer = 1;
    bottom_pointer = 0;
  }
  if (clicked_buttons & BUTTON_DOWN) {
    bottom_pointer = 1;
    top_pointer = 0;
  }
  // switches screen based on what the user has selected
  if(top_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    flow[RIGHT] = HEAT;
    state = set_RIGHT_temp;
    delay(300);
    lcd.clear();
  }
  if(bottom_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    flow[RIGHT] = COOL;
    state = set_RIGHT_temp;
    delay(300);
    lcd.clear();
  }
  // goes to previous screen if user selects the left button
  if (clicked_buttons & BUTTON_LEFT) {
    state = on_offR;
    delay(300);
    lcd.clear(); 
  }
}

// user sets the left temperature
void set_LEFT_temp() {
  // sets up screen
  lcd.setCursor(0, 0);
  lcd.print("LEFT: ");
  lcd.print(currentDegC[0]);
  lcd.setCursor(0, 1);
  lcd.print("  ");
  lcd.write(0x7E);
  lcd.print(setDegC[0]);
  // goes to previous screen if user selects the left button
  if (clicked_buttons & BUTTON_LEFT) {
    state = L_heat_or_cool;
    delay(300);
    lcd.clear(); 
  }
  // increases temperature
  if (clicked_buttons & BUTTON_UP) {
    /*while (digitalRead(button1Pin) == LOW) {
      int count = 0;
    }*/
    setDegC[0] += 0.5; // time when lift down and back up function needed
    state = set_LEFT_temp;
    lcd.clear(); 
  }
  // decreases temperature
  if (clicked_buttons & BUTTON_DOWN) {
    /*while (digitalRead(button4Pin) == LOW) {
      
    }*/
    setDegC[0] -= 0.5; // time when lift down and back up function needed
    state = set_LEFT_temp;
    lcd.clear(); 
  }
  // switches screen based on what the user has selected
  if (clicked_buttons & BUTTON_SELECT) {
    state = home_and_summary;
    delay(300);
    lcd.clear(); 
  }
}
// user sets the right temperature
void set_RIGHT_temp() {
  // sets up screen
  lcd.setCursor(0, 0);
  lcd.print("RIGHT:");
  lcd.print(currentDegC[1]);
  lcd.setCursor(0, 1);
  lcd.print("  ");
  lcd.write(0x7E);
  lcd.print(setDegC[1]);
  // goes to previous screen if user selects the left button
  if (clicked_buttons & BUTTON_LEFT) {
    state = R_heat_or_cool;
    delay(300);
    lcd.clear(); 
  }
  // increases temperature
  if (clicked_buttons & BUTTON_UP) {
    /*while (digitalRead(button1Pin) == LOW) {
      int count = 0;
    }*/
    setDegC[1] += 0.5; // time when lift down and back up function needed
    state = set_RIGHT_temp;
    lcd.clear(); 
  }
  // decreases temperature
  if (clicked_buttons & BUTTON_DOWN) {
    /*while (digitalRead(button4Pin) == LOW) {
      int count = 0;
    }*/
    setDegC[1] -= 0.5; // time when lift down and back up function needed
    state = set_RIGHT_temp;
    lcd.clear(); 
  }
  // switches screen based on what the user has selected
  if (clicked_buttons & BUTTON_SELECT) {
    state = home_and_summary;
    delay(300);
    lcd.clear(); 
  }
}

// user has a choice to go to the home screen or summary screen
void home_and_summary() {
  static int top_pointer = 0;
  static int bottom_pointer = 0;
  lcd.setCursor(0, 0);
  lcd.print("    HOME ");
  // points to the top option if user has selected it
  if (top_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(12, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("    SUMMARY ");
  // points to the bottom option if user has selected it
  if (bottom_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 0);
    lcd.print(" ");
  }
  // sees what option user has selected to point at
  if (clicked_buttons & BUTTON_UP) {
    top_pointer = 1;
    bottom_pointer = 0;
  }
  if (clicked_buttons & BUTTON_DOWN) {
    bottom_pointer = 1;
    top_pointer = 0;
  }
  // switches screen based on what the user has selected
  if(top_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    state = left_or_right;
    delay(300);
    lcd.clear(); 
  }
  if(bottom_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    state = show_summary;
    delay(300);
    lcd.clear();
  }
}

// user has a choice to go to the summary screen or finish screen
void summary_and_finish() {
  static int top_pointer = 0;
  static int bottom_pointer = 0;
  lcd.setCursor(0, 0);
  lcd.print("    SUMMARY ");
  // points to the top option if user has selected it
  if (top_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(11, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("    FINISH ");
  // points to the bottom option if user has selected it
  if (bottom_pointer == 1) {
    lcd.write(0x7F);
    lcd.setCursor(12, 0);
    lcd.print(" ");
  }
  // sees what option user has selected to point at
  if (clicked_buttons & BUTTON_UP) {
    top_pointer = 1;
    bottom_pointer = 0;
  }
  if (clicked_buttons & BUTTON_DOWN) {
    bottom_pointer = 1;
    top_pointer = 0;
  }
  // switches screen based on what the user has selected
  if(top_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    state = show_summary;
    delay(300);
    lcd.clear();
  }
  if(bottom_pointer == 1 && (clicked_buttons & BUTTON_SELECT)) {
    state = start_screen;
    delay(300);
    lcd.clear();
  }

}

// screen that displays the summary of temperatures for each peltier
void my_summary() {
  if (peltier_on[LEFT] == true) {
    lcd.setCursor(0, 0);
    lcd.print("L:");
    lcd.print(currentDegC[0]);
    lcd.write(0x7E);
    lcd.print(setDegC[0]);
    lcd.print("(");
    if (flow[LEFT] == HEAT) {
      lcd.print("H");
    }
    if (flow[LEFT] == COOL) {
      lcd.print("C");
    }
    lcd.print(")");
  }
  if (peltier_on[LEFT] != true) {
    lcd.setCursor(0, 0);
    lcd.print("L:");
    lcd.print(" OFF");
  }
  if (peltier_on[RIGHT] == true) {
    lcd.setCursor(0, 1);
    lcd.print("R:");
    lcd.print(currentDegC[1]);
    lcd.write(0x7E);
    lcd.print(setDegC[1]);
    lcd.print("(");
    if (flow[RIGHT] == HEAT) {
      lcd.print("H");
    }
    if (flow[RIGHT] == COOL) {
      lcd.print("C");
    }
    lcd.print(")");
  }
  if (peltier_on[RIGHT] != true) {
    lcd.setCursor(0, 1);
    lcd.print("R:");
    lcd.print(" OFF");
  }
  // switches screen based on what the user has selected
  if (clicked_buttons & BUTTON_SELECT) {
    state = summary_and_finish;
    delay(300);
    lcd.clear();
  }
}

//! Initial state, draw the splash screen.
/*void begin_splash_screen() {
  lcd.clear();
  //lcd.setBacklight(ON);
  lcd.print(F("PELTIER CONTROLS"));
  state = animate_splash_screen;
}

//! Animate the splash screen.
/*!
  Blink the text "PRESS SELECT" and wait for the user to press the select button.

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
}*/

void show_summary() {
  static double last_lc = 0;
  static double last_rc = 0;

  // Read the temperature as Celsius:
  double lc = avgTC[LEFT].getAverage();
  double rc = avgTC[RIGHT].getAverage();

  if (update) {
    //lcd.setBacklight(ON);
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
    lcd.print(F(" "));
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
    lcd.print(F(" "));
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
  if (clicked_buttons & BUTTON_SELECT) {
    state = summary_and_finish;
    delay(300);
    lcd.clear();
  }
  /*if (clicked_buttons) {
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
  }*/
}
