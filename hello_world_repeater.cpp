void setup() {
  Serial.begin(9600);
  Serial.setTimeout(10);
}



void loop() {
  while(!Serial.available());
  byte incoming = Serial.read();
  Serial.print((char) incoming);
}

