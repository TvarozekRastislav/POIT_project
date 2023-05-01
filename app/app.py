from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect  
import time
import serial
import re

app = Flask(__name__)

async_mode = None
thread = None

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread_lock = Lock()
ser = serial.Serial("/dev/ttyS2", 115200)
ser.boundrate = 115200
recived_data = 0

def decode_message(message):
    string = message.decode('utf-8')
    number = re.findall(r'\d+', string)
    print("ARDUINO MESSAGE:")
    try:
        print(number[0])
        number = number[0]
        if int(number) > 255 :
            return -1
        else:
            return int(number)
    except:
        print("NOTHING CAME")
        return -1
    

def background_thread(args):

    counter = 0
    reg = 125
    reg_fin = 0
    pwm_req = 0
    pwm_prev = 0
    reg_counter = 0
    while True:
        
        recived_data = ser.readline()
        arudino_message = decode_message(recived_data)
        if arudino_message == -1 or arudino_message > 255:
            continue

        if args:
            pwm_req = dict(args).get('pwm_req')
            print("PWM_REQ: " + pwm_req)
            #print("PWM_PREV: " + pwm_prev)
            pwm_req = int(pwm_req)

            if pwm_req != pwm_prev:
                print("PWM_PREV: " + str(pwm_prev))
                reg_fin = 0
                reg_counter = 0
                reg = 125
                pwm_prev = pwm_req 
            if not (pwm_req-10 < arudino_message and pwm_req+10 > arudino_message) :
               
                if pwm_req > arudino_message:
                    print("PRIDAVAM")
                    reg = reg + reg / 2
                    if reg > 255:
                        reg = 255
                    ser.write(str.encode(str(int(reg))))
                else:
                    print("UBERAM")
                    reg = reg - reg /2 
                    if reg < 1:
                        reg = 1
                    ser.write(str.encode(str(int(reg))))
                
                if(reg_counter > 15):
                    reg_fin = 1
                reg_counter = reg_counter + 1

                print("REG:" + str(reg))
                #time.sleep(1)
                #recived_data = ser.readline()
                #arudino_message = decode_message(recived_data)

            else:
                print("REGULATION IS FINISHED")
                reg_fin = 1
                pwm_prev = pwm_req 
            
            
        socketio.emit(
            'sensor_data',
            {
                'data':arudino_message,
                'count': counter
            },
            namespace = '/prod'
        )
        counter = counter + 1 

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('connected', namespace='/prod')
def connect(message):
    global thread
    print(message['data'])
    print('CONNECTED FROM SERVER')

    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
    
@socketio.on('disconnect_request', namespace='/prod')
def disconnect_request():
    ser.write(9998)
    disconnect()

@socketio.on('pwm_req', namespace='/prod')
def pwm_req(message):
    session['pwm_req'] = message['value']
    print("PRISLI DATA")
    print(session['pwm_req'])


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)