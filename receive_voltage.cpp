#include <SPI.h>

#define SS 10

#define WRDAC (0b0011) // Table 9 on page 23
#define WRCTR (0b00000100) // Table 11 on page 24, 25


// zero-voltage CLEAR, OVR disabled, B2C straight, ETS disabled, power-up to zeroscale
#define CTRRST (0b0000000000) // control register RST on page 25, 26
#define CMASK2 ((0b111) << 8)
#define CMASK3 (0xFF)


void write_ctrl_cmd(int cmd) {
  // SPI.beginTransaction should be called outside this function
  byte byte1 = WRCTR, 
       byte2 = ((cmd & CMASK2) >> 8), 
       byte3 = (cmd & CMASK3);
  SPI.transfer(byte1);
  SPI.transfer(byte2);
  SPI.transfer(byte3);
}


void init_DAC(int slaveSelect=SS) {
  pinMode(SS, OUTPUT);  // make SS a real slave
  pinMode(13, OUTPUT);
  
  SPI.begin();

  digitalWrite(SS, LOW);
  SPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE1));
  write_ctrl_cmd(CTRRST);  // always good to reset in the first place 
  SPI.endTransaction();
  digitalWrite(SS, HIGH);
}


void write_output_value(unsigned int val) {
  // input shift register, update DAC register directly, see page 24
  byte byte1 = WRDAC,
       byte2 = ((0xFF00 & val) >> 8), 
       byte3 = (0xFF & val); 
  SPI.transfer(byte1);
  SPI.transfer(byte2);
  SPI.transfer(byte3);
}


void write_voltage(unsigned int voltage, int slaveSelect=SS) {
  digitalWrite(SS, LOW); 
  SPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE1));
  write_output_value(voltage);
  SPI.endTransaction();
  digitalWrite(SS, HIGH);
}

void write_single_voltage(unsigned int voltage, int slaveSelect=SS) {
  digitalWrite(SS, LOW); 
  SPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE1));
  while(1) write_output_value(voltage);
}


unsigned int voltage; 

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(1);
  voltage = 0;
  init_DAC();
  Serial.println("Arduino setup finished!");
}


void loop() {
  while(!Serial.available());
  byte incoming = Serial.read();
  if(incoming == '#') {
    Serial.print("Voltage read: ");
    Serial.print(voltage / 65636. * 20 - 10.);  // print the actually voltage we want, confirm correctness. 
    Serial.println(" V");
    write_voltage(voltage); 
    Serial.println("Write finished!");
    Serial.flush();
    voltage = 0; 
  }
  else if (incoming >= '0' && incoming <= '9'){
    voltage *= 10; 
    voltage += incoming - '0';
  }
}

