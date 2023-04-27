from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect  
import time
import serial

app = Flask(__name__)

async_mode = None
thread = None

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread_lock = Lock()

def decode_message(message):
    string = message.decode('utf-8')
    start_index = string.find(':', string.find(':') + 1) + 2
    end_index = string.find('\r')
    number = string[start_index:end_index]

    return number


def background_thread(args):

    ser = serial.Serial("/dev/ttyS2", 115200)
    ser.boundrate = 115200
    range = [0,0]
    while True:
        
        recived_data = ser.readline()


        arudino_message = decode_message(recived_data)
        print("ARDUINO MESSAGE:")
        print(arudino_message)

        if 'min' in recived_data:
            range[0] = arudino_message
        else if 'max' in recived_data:
            range[1] = arudino_message
        if(range[0] != 0 and range[1] != 0):
            socketio.emit(
                'initial_data',
                {'data': range},
                namespace = '/prod'
            )    
        socketio.emit(
            'sensor_data',
            {
                'data':'X',
                'count': 'Y'
            },
            namespace = '/prod'
        )

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
    ser.write(9999)
    disconnect()

@socketio.on('pwm_req', namespace='/prod')
def pwm_req(message):
    session['pwm_req'] = message.get('value')


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)