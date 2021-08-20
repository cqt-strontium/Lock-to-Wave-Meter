#include <SPI.h>

#define SS 10
#define LED 13
#define WRDAC (0b0011) // Table 9 on page 23
#define WRCTR (0b00000100) // Table 11 on page 24, 25
#define WRRST (0x0F) // Table 26 on page 33



// control register RST on page 25, 26
#define CTRRST (0b0000000000) // zero-voltage CLEAR, OVR disabled, B2C straight, ETS disabled, power-up to zeroscale， -10 to +10 range
#define CTRRST05 (0b0000000011) // others being the same, 0 to +5 range
#define CMASK2 ((0b111) << 8)
#define CMASK3 (0xFF)


void print_byte(byte b, char end='\n') {
  // print a byte in binary representation, terminating with newline by default
  int cnt = 0; 
  byte bb = b;
  while(b >>= 1)
    ++cnt; 
  while((++cnt) < 8)
      Serial.print('0');
  Serial.print(bb, 2);
  Serial.print(end);
}

void write_reset_cmd() {
  // This function is for full software reset *ONLY*
  // SPI.beginTransaction should be called outside this function
  byte byte1 = WRRST; 
  SPI.transfer(byte1);
  SPI.transfer((byte)0);
  SPI.transfer((byte)0);
}


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
  digitalWrite(SS, HIGH); 

  delay(100); // DAC start-up

  SPI.begin();
  digitalWrite(SS, LOW);
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  // write_reset_cmd();
  // SPI.endTransaction();
  // delay(5);
  // SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
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
  // print_byte(byte1);
  // print_byte(byte2);
  // print_byte(byte3);
}

int count_ones(unsigned int val) {
  // *DEBUG* use only. 
  // Count ones in a certain 24-bit command. This correspond to the DC output of MOSI which can be measure with a multimeter. 
  byte byte1 = WRDAC,
       byte2 = ((0xFF00 & val) >> 8), 
       byte3 = (0xFF & val); 
  int ret = 0;
  while(byte1)
  {
    ret += (byte1 & 1);
    byte1 >>= 1;
  }
  while(byte2)
  {
    ret += (byte2 & 1);
    byte2 >>= 1;
  }
  while(byte3)
  {
    ret += (byte3 & 1);
    byte3 >>= 1;
  }
  return ret; 
}


void write_voltage(unsigned int voltage, int slaveSelect=SS) {
  digitalWrite(SS, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  write_output_value(voltage);
  SPI.endTransaction();
  digitalWrite(SS, HIGH);
}

void write_single_voltage(unsigned int voltage, int slaveSelect=SS) {
  digitalWrite(SS, LOW); 
  Serial.println(count_ones(voltage));
  while(1) {    
    SPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE2));
    write_output_value(voltage);
    SPI.endTransaction();
  }
}


unsigned int voltage = 0; 

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(1);
  voltage = 0;
  init_DAC();
  Serial.println("Arduino setup finished!");
}


void loop() {
  if(Serial.available())
  {
    byte incoming = Serial.read();
    if(incoming == '#') {
      Serial.print("Voltage read: ");
      Serial.print(voltage / 65536. * 20 - 10.);
      // Uncomment if output range is 0-5V
      // Serial.print(voltage / 65536. * 5);
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
}

