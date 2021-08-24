#include <SPI.h>

#define SS 10
#define LED 13
#define WRDAC (0b0011) // Table 9 on page 23
#define WRCTR (0b00000100) // Table 11 on page 24, 25
#define WRRST (0x0F) // Table 26 on page 33

#define TWO_COMPLEMENT
#define DEBUG
#undef DEBUG 
// control register RST on page 25, 26
#ifdef TWO_COMPLEMENT
#define CTRRST (0b00010100101) // zero-voltage CLEAR, OVR disabled, B2C complement, ETS disabled, power-up to zeroscale， -3 to +3 range
#else
#define CTRRST (0b00000100101) // zero-voltage CLEAR, OVR disabled, B2C straight, ETS disabled, power-up to zeroscale， -3 to +3 range
#endif

#define CMASK2 ((0b111) << 8)
#define CMASK3 (0xFF)


#ifdef DEBUG
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

void print_ctrl_cmd(byte* cmd) {
  Serial.print("Control command just read is:");
  print_byte(cmd[0], ' ');
  print_byte(cmd[1], ' ');
  print_byte(cmd[2], ' ');
  Serial.print('\n');
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
#endif // DEBUG 

void write_reset_cmd(int slaveSelect) {
  // This function is for full software reset *ONLY*
  byte byte1 = WRRST; 
  
  digitalWrite(slaveSelect, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  SPI.transfer(byte1);
  SPI.transfer((byte)0);
  SPI.transfer((byte)0);
  SPI.endTransaction();
  digitalWrite(slaveSelect, HIGH);
}


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


void init_DAC(int slaveSelect=SS) {
  byte ctrl_cmd[3]; 
  pinMode(slaveSelect, OUTPUT);  // make SS a real slave
  pinMode(MISO, INPUT); 
  digitalWrite(slaveSelect, HIGH); 
  delay(100); // DAC start-up

  SPI.begin();
  
  write_ctrl_cmd(CTRRST, slaveSelect);  // always good to reset in the first place 
  asm volatile("nop");
  delay(100);
  #ifdef DEBUG
  read_ctrl_reg(ctrl_cmd, slaveSelect);
  print_ctrl_cmd(ctrl_cmd);
  #endif 
}


void write_output_value(unsigned int val, int slaveSelect) {
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

  #ifdef DEBUG
  print_byte(byte1);
  print_byte(byte2);
  print_byte(byte3);
  #endif // DEBUG
}


void write_voltage(unsigned int voltage, int slaveSelect=SS) {
  write_output_value(voltage, slaveSelect);
  
  #ifdef DEBUG
  byte ctrl_cmd[3];
  read_ctrl_reg(ctrl_cmd, slaveSelect);
  print_ctrl_cmd(ctrl_cmd);
  #endif
}

void write_bytes(byte* bytes, int slaveSelect) {
  digitalWrite(slaveSelect, LOW); 
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE2));
  SPI.transfer(WRDAC);
  SPI.transfer(bytes[0]);
  SPI.transfer(bytes[1]);
  SPI.endTransaction();
  digitalWrite(slaveSelect, HIGH);
}

void write_voltage_bytes(byte* bytes, int slaveSelect=SS) {
  write_bytes(bytes, slaveSelect); 
  #ifdef DEBUG
  byte ctrl_cmd[3];
  read_ctrl_reg(ctrl_cmd, slaveSelect);
  print_ctrl_cmd(ctrl_cmd);
  #endif
}

#ifdef DEBUG
void write_single_voltage(unsigned int voltage, int slaveSelect=SS) {
  Serial.println(count_ones(voltage));
  while(1) 
    write_output_value(voltage, slaveSelect);
}
#endif // DEBUG


#ifndef TWO_COMPLEMENT
unsigned int voltage = 0; 
#else
int voltage = 0;
#endif // TWO_COMPLEMENT

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10);
  voltage = 0;
  init_DAC();
  Serial.println("Arduino setup finished!");
}


void loop() {
  Serial.print('a');
  
  byte bytes[2];
  Serial.readBytes(bytes, 2);
  
  voltage = ((bytes[0] << 8) | bytes[1]);
  
  #ifdef DEBUG
  Serial.print("Voltage read: ");
    #ifdef TWO_COMPLEMENT
    Serial.print(voltage / 65536. * 6);
    #else
    Serial.print(voltage / 65536. * 6. - 3.);
    #endif // TWO_COMPLEMENT
  Serial.println(" V");
  write_voltage_bytes(bytes); 
  Serial.println("Write finished!");
  Serial.flush();
  #else
  write_voltage_bytes(bytes);
  #endif // DEBUG
  
  delayMicroseconds(5000);
}

