const int ledPwm = 5;
const int sensor = A0;


void setup() {
  Serial.begin(115200);

  pinMode(ledPwm, OUTPUT);
  analogWrite(ledPwm, 0);      
  
}

int readSensor(){
  return analogRead(sensor);
}

int sendData(int sensorValuePwm){
  int bytesSent = 0;
  char strBuf[50];

  Serial.println("--------SENT DATA ------");
  sprintf(strBuf, "sent_arduino_sensor=%d", sensorValuePwm);
  bytesSent = Serial.write(strBuf);
  Serial.println("------------------------");


  if(bytesSent == 0 ){
    Serial.println("ERROR: sensor values not sent");
  }else{
    Serial.print("INFO: sent serial data: ");
    Serial.println(sensorValuePwm);
  }

  return bytesSent;
}

int readData(){
  int bytesRecieved = 0;

  if(Serial.available() > 0){

    char strBuf[50];

    Serial.println("--------READ DATA ------");
      Serial.print("INFO: recieved serial data: ");
      Serial.println(bytesRecieved);
    Serial.println("------------------------");

  }
  return bytesRecieved;
}

void loop() {

  int sensorValuePwm = map(readSensor(), 0, 1024, 0, 255);
  
  sendData(sensorValuePwm);
  
  int dataRecieved = readData();

  if(dataRecieved != 0){
    analogWrite(ledPwm, dataRecieved);      
  }else if(dataRecieved == -1){
    exit(0);
  } 

  delay(200);

}
