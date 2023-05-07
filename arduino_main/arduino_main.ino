const int ledPwm1 = 5;
const int ledPwm2 = 4;
const int ledPwm3 = 0;

const int sensor = A0;

void setup() {
  Serial.begin(115200);

  pinMode(ledPwm1, OUTPUT);
  pinMode(ledPwm2, OUTPUT);
  pinMode(ledPwm3, OUTPUT);

  analogWrite(ledPwm1, 0);   
  analogWrite(ledPwm2, 0);      
  analogWrite(ledPwm3, 0);      
   
}

int readSensor(){
  return analogRead(sensor);
}

int sendData(int sensorValuePwm){
  int bytesSent = 0;
  char strBuf[50];

  sprintf(strBuf, "sent_arduino_sensor=%d\n", sensorValuePwm);
  bytesSent = Serial.write(strBuf);

  return bytesSent;
}

int readData(){

  if(Serial.available() > 0){

    int bytesRecieved = Serial.parseInt();
    //Serial.println(bytesRecieved);
    return bytesRecieved;

  }
  return 0;
}

void loop() {

  int sensorValuePwm = map(readSensor(), 0, 1024, 0, 255);
  
  sendData(sensorValuePwm);
  
  delay(50);

  int dataRecieved = readData();

  if(dataRecieved == 9999){
    analogWrite(ledPwm1, 0);     
    analogWrite(ledPwm2, 0);      
    analogWrite(ledPwm3, 0); 
  }else if(dataRecieved == 9998){
    exit(0);
  }else if(dataRecieved != 0){
    analogWrite(ledPwm1, dataRecieved);     
    analogWrite(ledPwm2, dataRecieved);      
    analogWrite(ledPwm3, dataRecieved);      
  } 

}
