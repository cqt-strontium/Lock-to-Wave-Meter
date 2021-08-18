#include <SPI.h>

#define SS 10
#define WRDAC (0b0011) // Table 9 on page 23
#define WRCTR (0b0100) // Table 9 on page 23
#define CTRRST (0b100000) // control register RESET on page 24
#define CTRGAIN (0b000010) // control register GAIN on page 24

// bit masks for extracting relevant bits from DAC number, so as to form correct command
#define MASK1 ((0b1111)<<12)
#define MASK2 ((0b11111111)<<4)
#define MASK3 (0b1111)

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


void write_ctrl_cmd(int cmd) {
  // SPI.beginTransaction should be called outside this function
  byte byte1 = (WRCTR << 4) | ((cmd & 0b111100) >> 2), 
       byte2 = ((cmd & 0b11) << 6); 
  SPI.transfer(byte1);
  SPI.transfer(byte2);
  SPI.transfer((byte)0);
  
  delay(1000);  // needed for DAC to relax a while
}


void init_DAC(int slaveSelect=SS) {
  pinMode(SS, OUTPUT);  // make SS a real slave
  SPI.begin();

  digitalWrite(SS, LOW);
  SPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE1));
  write_ctrl_cmd(CTRRST);  // always good to reset in the first place 
  delay(1000); // needed for DAC to relax a while
  write_ctrl_cmd(CTRGAIN); // set max output to 0 to 2*V_REF=5
  SPI.endTransaction();
  digitalWrite(SS, HIGH);
}


void write_output_value(unsigned int val) {
  // note AD5863R takes 24 bits, i.e. 3 bytes, per input 
  byte byte1 = (WRDAC << 4) | ((MASK1 & val) >> 12),
       byte2 = (MASK2 & val) >> 4, 
       byte3 = (MASK3 & val) << 4; 
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
  // *DEBUG* use only, with oscilloscope to see the directive
  digitalWrite(SS, LOW); 
  SPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE1));
  while (1) write_output_value(voltage);  // this infinite loop would issue the same directive forever, thus may be easily caught by oscilloscope
}

void setup() {
  Serial.begin(9600);
  
  pinMode(13, OUTPUT);
  pinMode(11, OUTPUT);

  init_DAC();
}


void loop() {
  // this is *insane*: the size of int in Arduino is 2 byte.
  for (unsigned int i = 11427; i < 65535; i+= 5000) {
    print_byte(i);
    Serial.println(5. * i / 65535.);
    write_single_voltage(i);
    // write_voltage(i);
    delay(2000);
  }
}

