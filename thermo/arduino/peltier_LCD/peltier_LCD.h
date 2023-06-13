/*
 * Desiged for an Arduino Uno R3
 * with two Adafruit MAX31855 type K thermocouple amplifiers
*/

// Software SPI digital IO pins for thermocouples
#define DO 11
#define RCS 9
#define CLK 13
#define LCS 10

// Define pins to control peltier relays and MOSFETs
#define RPELTIER 6
#define RPELTIER_RELAY 4
#define LPELTIER 5
#define LPELTIER_RELAY 4     // For future use if two power supplies are needed
#define LPETLIER_POLARITY 7  // For future use for DPDT polarity switch
#define RPLETIER_POLARITY 8  //For future use for DPDT polarity switch

// Constants
#define LEFT 0
#define RIGHT 1
#define COOL LOW   // Defined as pin polarities
#define HEAT HIGH  // Defined as pin polarities
