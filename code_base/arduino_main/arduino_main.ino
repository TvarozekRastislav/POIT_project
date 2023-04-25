const int ledPwm = 5;
const int sensor = A0;

int sensorValue = 0;

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

  Serial.write("ard_intensity:\n");
  bytesSent = Serial.write("sensorValuePwm");
  if(bytesSent == 0 ){
    Serial.println("ERROR: sensor values not sent");
  }else{
    Serial.print("INFO: sent serial data: ")
    Serial.println(sensorValuePwm);
  }

  return bytesSent;
}

voud readData(){
  int bytesRecieved = 0;

  if(Serial.available() > 0){
    bytesRecieved = Serial.read();
    Serial.print("INFO: recieved serial data: ");
    Serial.println(bytesRecieved);
  }
  return bytesRecieved;
}

void loop() {

  sensorValuePwm = map(readSensor(), 0, 1024, 0, 255);
  
  sendData(sensorValuePwm);
  
  int dataRecieved = readData();

  if(dataRecieved != 0){
    analogWrite(ledPwm, dataRecieved);      
  }
  
  delay(200);
}
