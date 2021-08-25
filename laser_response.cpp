#include <SPI.h>

#define SS 10  // This seems to be defined in pins_arduino.h 

#define WRDAC (0b0011) // Table 9 on page 23
#define WRCTR (0b00000100) // Table 11 on page 24, 25
#define WRRST (0x0F) // Table 26 on page 33

#define TWO_COMPLEMENT

// control register RST on page 25, 26
#ifdef TWO_COMPLEMENT
#define CTRRST (0b00010100101) // zero-voltage CLEAR, OVR disabled, B2C complement, ETS disabled, power-up to zeroscale， -3 to +3 range
#else
#define CTRRST (0b00000100101) // zero-voltage CLEAR, OVR disabled, B2C straight, ETS disabled, power-up to zeroscale， -3 to +3 range
#endif

#define CMASK2 ((0b111) << 8)
#define CMASK3 (0xFF)


void write_ctrl_cmd(unsigned int cmd, int slaveSelect) {
  byte byte1 = WRCTR, 
       byte2 = ((cmd & CMASK2) >> 8), 
       byte3 = (cmd & CMASK3);
      
  digitalWrite(slaveSelect, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  SPI.transfer(byte1);
  SPI.transfer(byte2);
  SPI.transfer(byte3);
  SPI.endTransaction();
  digitalWrite(slaveSelect, HIGH);
}


void read_ctrl_reg(byte *ret, int slaveSelect) {
  // See Table 14 & 15 on page 31 for the readback of control register
  digitalWrite(slaveSelect, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  SPI.transfer((byte)0b1100);
  SPI.transfer((byte)0);
  SPI.transfer((byte)0);
  SPI.endTransaction();
  digitalWrite(slaveSelect, HIGH);


  asm volatile("nop");  // this is t_{17}, see Figure 4 on page 8; the current frequency is slow enough for this to work

  digitalWrite(slaveSelect, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  ret[0] = SPI.transfer((byte)0); // this is the "no op" operation, see Table 27 on page 33 
  ret[1] = SPI.transfer((byte)0); 
  ret[2] = SPI.transfer((byte)0);
  SPI.endTransaction();
  digitalWrite(slaveSelect, HIGH);
}


void write_output_value(unsigned int val, int slaveSelect=SS) {
  // input shift register, update DAC register directly, see page 24
  digitalWrite(slaveSelect, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  byte byte1 = WRDAC,
       byte2 = ((0xFF00 & val) >> 8), 
       byte3 = (0xFF & val); 
  SPI.transfer(byte1);
  SPI.transfer(byte2);
  SPI.transfer(byte3);
  SPI.endTransaction();
  digitalWrite(slaveSelect, HIGH);
}


void write_bytes(byte* bytes, int slaveSelect=SS) {
  digitalWrite(slaveSelect, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  SPI.transfer(WRDAC);
  SPI.transfer(bytes[0]);
  SPI.transfer(bytes[1]);
  SPI.endTransaction();
  digitalWrite(slaveSelect, HIGH);
}




void init_DAC(int slaveSelect=SS) {
  byte ctrl_cmd[3]; 
  pinMode(slaveSelect, OUTPUT);  // make SS a real slave
  pinMode(MISO, INPUT); 
  digitalWrite(slaveSelect, HIGH); 
  delay(100); // DAC start-up

  SPI.begin();
  
  write_ctrl_cmd(CTRRST, slaveSelect);  // always good to reset in the first place 
  asm volatile("nop");

  write_output_value((unsigned int)0);  // fix output to 0 for safety's sake 
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10);
  
  init_DAC();
  Serial.println("Arduino setup finished!");
}


void loop() {
  if (Serial.available())
  {
    byte bytes[2];
    Serial.readBytes(bytes, 2);
    write_bytes(bytes);    
  }
}

