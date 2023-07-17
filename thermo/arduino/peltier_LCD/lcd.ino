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

void screen_1() {
  lcd.setCursor(0, 0);
  lcd.write(0x7E);
  lcd.print(F(" PRESS SELECT "));
  lcd.write(0x7F);
  lcd.setCursor(0, 1);
  lcd.print("    *SELECT*");
  if (digitalRead(button5Pin) == LOW) {
    state = screen_2;
    delay(200);
    lcd.clear();
  }
}

int L2 = 0;
int R2 = 0;

void screen_2() {
  lcd.setCursor(0, 0);
  lcd.print("    LEFT ");
  if (L2 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("    RIGHT ");
  if (R2 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 0);
    lcd.print(" ");
  }
  if (digitalRead(button1Pin) == LOW) {
    L2 = 1;
    R2 = 0;
  }
  if (digitalRead(button4Pin) == LOW) {
    R2 = 1;
    L2 = 0;
  }
  if(L2 == 1 && digitalRead(button5Pin) == LOW) {
    state = on_offL;
    delay(300);
    lcd.clear();
  }
  if(R2 == 1 && digitalRead(button5Pin) == LOW) {
    state = on_offR;
    delay(300);
    lcd.clear();
  }

}

int LLOF = 0;
int RLOF = 0;

void on_offL() {
  lcd.setCursor(0, 0);
  lcd.print("     ON ");
  if (LLOF == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     OFF ");
  if (RLOF == 1) {
    lcd.write(0x7F);
    lcd.setCursor(8, 0);
    lcd.print(" ");
  }
  if (digitalRead(button1Pin) == LOW) {
    LLOF = 1;
    RLOF = 0;
  }
  if (digitalRead(button4Pin) == LOW) {
    RLOF = 1;
    LLOF = 0;
  }
  if(LLOF == 1 && digitalRead(button5Pin) == LOW) {
    peltier_on[0] = true;
    state = screen_3L;
    delay(300);
    lcd.clear(); 
  }
  if(RLOF == 1 && digitalRead(button5Pin) == LOW) {
    peltier_on[0] = false;
    state = screen_5;
    delay(300);
    lcd.clear();
  }
   if (digitalRead(button2Pin) == LOW) {
    state = screen_2;
    delay(300);
    lcd.clear(); 
  }

 }

int LROF = 0;
int RROF = 0;

void on_offR() {
  lcd.setCursor(0, 0);
  lcd.print("     ON ");
  if (LROF == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     OFF ");
  if (RROF == 1) {
    lcd.write(0x7F);
    lcd.setCursor(8, 0);
    lcd.print(" ");
  }
  if (digitalRead(button1Pin) == LOW) {
    LROF = 1;
    RROF = 0;
  }
  if (digitalRead(button4Pin) == LOW) {
    RROF = 1;
    LROF = 0;
  }
  if(LROF == 1 && digitalRead(button5Pin) == LOW) {
    peltier_on[1] = true;
    state = screen_3R;
    delay(300);
    lcd.clear(); 
  }
  if(RROF == 1 && digitalRead(button5Pin) == LOW) {
    peltier_on[1] = false;
    state = screen_5;
    delay(300);
    lcd.clear();
  }
  if (digitalRead(button2Pin) == LOW) {
    state = screen_2;
    delay(300);
    lcd.clear(); 
  }
}

int LL3 = 0;
int RL3 = 0;

void screen_3L() {
  lcd.setCursor(0, 0);
  lcd.print("     HEAT ");
  if (LL3 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     COOL ");
  if (RL3 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 0);
    lcd.print(" ");
  }
  if (digitalRead(button1Pin) == LOW) {
    LL3 = 1;
    RL3 = 0;
  }
  if (digitalRead(button4Pin) == LOW) {
    RL3 = 1;
    LL3 = 0;
  }
  if(LL3 == 1 && digitalRead(button5Pin) == LOW) {
    flow[LEFT] = HEAT;
    state = screen_4L;
    delay(300);
    lcd.clear();
  }
  if(RL3 == 1 && digitalRead(button5Pin) == LOW) {
    flow[LEFT] = COOL;
    state = screen_4L;
    delay(300);
    lcd.clear();
  }
  if (digitalRead(button2Pin) == LOW) {
    state = screen_2;
    delay(300);
    lcd.clear(); 
  }
  if (digitalRead(button2Pin) == LOW) {
    state = on_offL;
    delay(300);
    lcd.clear(); 
  }
}

int LR3 = 0;
int RR3 = 0;

void screen_3R() { 
  lcd.setCursor(0, 0);
  lcd.print("     HEAT ");
  if (LR3 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("     COOL ");
  if (RR3 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(10, 0);
    lcd.print(" ");
  }
  if (digitalRead(button1Pin) == LOW) {
    LR3 = 1;
    RR3 = 0;
  }
  if (digitalRead(button4Pin) == LOW) {
    RR3 = 1;
    LR3 = 0;
  }
  if(LR3 == 1 && digitalRead(button5Pin) == LOW) {
    flow[RIGHT] = HEAT;
    state = screen_4R;
    delay(300);
    lcd.clear();
  }
  if(RR3 == 1 && digitalRead(button5Pin) == LOW) {
    flow[RIGHT] = COOL;
    state = screen_4R;
    delay(300);
    lcd.clear();
  }
  if (digitalRead(button2Pin) == LOW) {
    state = screen_2;
    delay(300);
    lcd.clear(); 
  }
  if (digitalRead(button2Pin) == LOW) {
    state = on_offR;
    delay(300);
    lcd.clear(); 
  }
}

void screen_4L() {
  lcd.setCursor(0, 0);
  lcd.print("LEFT: ");
  double lc = avgTC[LEFT].getAverage();
  lcd.print(lc);
  lcd.setCursor(0, 1);
  lcd.print("  ");
  lcd.write(0x7E);
  lcd.print(setDegC[0]);
  if (digitalRead(button2Pin) == LOW) {
    state = screen_3L;
    delay(300);
    lcd.clear(); 
  }
  if (digitalRead(button1Pin) == LOW) {
    while (digitalRead(button1Pin) == LOW) {
      int count = 0;
    }
    setDegC[0] += 0.5; //time when lift down and back up function needed
    state = screen_4L;
    lcd.clear(); 
  }
  if (digitalRead(button4Pin) == LOW) {
    while (digitalRead(button4Pin) == LOW) {
      
    }
    setDegC[0] -= 0.5; //time when lift down and back up function needed
    state = screen_4L;
    lcd.clear(); 
  }
  if (digitalRead(button5Pin) == LOW) {
    state = screen_5;
    delay(300);
    lcd.clear(); 
  }
}

void screen_4R() {
  lcd.setCursor(0, 0);
  lcd.print("RIGHT:");
  double rc = avgTC[RIGHT].getAverage();
  lcd.print(rc);
  lcd.setCursor(0, 1);
  lcd.print("  ");
  lcd.write(0x7E);
  lcd.print(setDegC[1]);
  if (digitalRead(button2Pin) == LOW) {
    state = screen_3R;
    delay(300);
    lcd.clear(); 
  }
  if (digitalRead(button1Pin) == LOW) {
    while (digitalRead(button1Pin) == LOW) {
      int count = 0;
    }
    setDegC[1] += 0.5; //time when lift down and back up function needed
    state = screen_4R;
    lcd.clear(); 
  }
  if (digitalRead(button4Pin) == LOW) {
    while (digitalRead(button4Pin) == LOW) {
      int count = 0;
    }
    setDegC[1] -= 0.5; //time when lift down and back up function needed
    state = screen_4R;
    lcd.clear(); 
  }
  if (digitalRead(button5Pin) == LOW) {
    state = screen_5;
    delay(300);
    lcd.clear(); 
  }
}

int L5 = 0;
int R5 = 0;

void screen_5() {
  lcd.setCursor(0, 0);
  lcd.print("    HOME ");
  if (L5 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(12, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("    SUMMARY ");
  if (R5 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(9, 0);
    lcd.print(" ");
  }
  if (digitalRead(button1Pin) == LOW) {
    L5 = 1;
    R5 = 0;
  }
  if (digitalRead(button4Pin) == LOW) {
    R5 = 1;
    L5 = 0;
  }
  if(L5 == 1 && digitalRead(button5Pin) == LOW) {
    state = screen_2;
    delay(300);
    lcd.clear(); 
  }
  if(R5 == 1 && digitalRead(button5Pin) == LOW) {
    state = summary;
    delay(300);
    lcd.clear();
  }
}

int L6 = 0;
int R6 = 0;

void screen_6() {
  lcd.setCursor(0, 0);
  lcd.print("    SUMMARY ");
  if (L6 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(11, 1);
    lcd.print(" ");
  }
  lcd.setCursor(0, 1);
  lcd.print("    FINISH ");
  if (R6 == 1) {
    lcd.write(0x7F);
    lcd.setCursor(12, 0);
    lcd.print(" ");
  }
  if (digitalRead(button1Pin) == LOW) {
    L6 = 1;
    R6 = 0;
  }
  if (digitalRead(button4Pin) == LOW) {
    R6 = 1;
    L6 = 0;
  }
  if(L6 == 1 && digitalRead(button5Pin) == LOW) {
    state = summary;
    delay(300);
    lcd.clear();
  }
  if(R6 == 1 && digitalRead(button5Pin) == LOW) {
    state = screen_1;
    delay(300);
    lcd.clear();
  }

}

void my_summary() {
  if (peltier_on[0] == true) {
    lcd.setCursor(0, 0);
    lcd.print("L:");
    lcd.print(currentL);
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
  if (peltier_on[0] != true) {
    lcd.setCursor(0, 0);
    lcd.print("L:");
    lcd.print(" OFF");
  }
  if (peltier_on[1] == true) {
    lcd.setCursor(0, 1);
    lcd.print("R:");
    lcd.print(currentR);
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
  if (peltier_on[1] != true) {
    lcd.setCursor(0, 1);
    lcd.print("R:");
    lcd.print(" OFF");
  }
  if (digitalRead(button5Pin) == LOW) {
    state = screen_6;
    delay(300);
    lcd.clear();
  }
}  

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

void summary() {
  static double last_lc = 0;
  static double last_rc = 0;

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
  if (digitalRead(button5Pin) == LOW) {
    state = screen_6;
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
