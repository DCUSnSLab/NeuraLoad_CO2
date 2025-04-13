#include <SoftwareSerial.h>

SoftwareSerial mySerial(13, 11);
unsigned char Send_data[4] = {0x11, 0x01, 0x01, 0xED};
unsigned char Receive_Buff[8];
unsigned char recv_cnt = 0;
unsigned int PPM_Value;

void Send_CMD(void) {
  unsigned int i;
  for (i = 0; i < 4; i++) {
    mySerial.write(Send_data[i]);
    delay(1);
  }
}

unsigned char Checksum_cal(void) {
  unsigned char count, SUM = 0;
  for (count = 0; count < 7; count++) {
    SUM += Receive_Buff[count];
  }
  return 256 - SUM;
}

void setup() {
  pinMode(13, INPUT);
  pinMode(11, OUTPUT);
  Serial.begin(9600);
  while (!Serial);
  mySerial.begin(9600);
  while (!mySerial);
}

void loop() {
  Serial.print("Sending...");
  Send_CMD();
  while (1) {
    if (mySerial.available()) {
      Receive_Buff[recv_cnt++] = mySerial.read();
      if (recv_cnt == 8) {
        recv_cnt = 0;
        break;
      }
    }
  }
  
  if (Checksum_cal() == Receive_Buff[7]) {
    PPM_Value = Receive_Buff[3] << 8 | Receive_Buff[4];
    Serial.write("  PPM : ");
    Serial.println(PPM_Value);
  }
  else {
    Serial.write("CHECKSUM Error");
  }
  delay(1000);
}