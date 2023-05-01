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

  Serial.println("--------SENT DATA ------");
  sprintf(strBuf, "sent_arduino_sensor=%d", sensorValuePwm);
  bytesSent = Serial.write(strBuf);
  Serial.println("");
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
    analogWrite(ledPwm1, dataRecieved);     
    analogWrite(ledPwm2, dataRecieved);      
    analogWrite(ledPwm3, dataRecieved);      
 
  }else if(dataRecieved == -1){
    exit(0);
  } 

  delay(200);

}
