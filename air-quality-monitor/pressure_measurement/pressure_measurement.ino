#include "SparkFun_SGP30_Arduino_Library.h"
#include <Wire.h>

int fsrPin = 1;
int fsrReading;
SGP30 mySensor;

void setup(void) {
  Serial.begin(9600);
  Wire.begin();
  if (mySensor.begin() == false) {
    Serial.println("No SGP30 detected. Check connections.");
    while (1);}
  mySensor.initAirQuality();
  Serial.println("Setup complete.");
}

void loop(void) {
  fsrReading = analogRead(fsrPin);

  Serial.print("Pressure - ");
  Serial.print(fsrReading);
  Serial.println(";");

  mySensor.measureAirQuality();
  Serial.print("CO2 - ");
  Serial.print(mySensor.CO2);
  Serial.println(";");
  Serial.print("TVOC - ");
  Serial.print(mySensor.TVOC);
  Serial.println(";");
  delay(1000);
}
