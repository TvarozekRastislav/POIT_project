from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect  
from simple_pid import PID
import configparser as ConfigParser
import time
import serial
import re
import MySQLdb 
import json 

app = Flask(__name__)

async_mode = None
thread = None

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread_lock = Lock()
ser = serial.Serial("/dev/ttyS2", 115200)
ser.boundrate = 115200
recived_data = 0

config = ConfigParser.ConfigParser()
config.read('config.cfg')
myhost = config.get('mysqlDB', 'host')
myuser = config.get('mysqlDB', 'user')
mypasswd = config.get('mysqlDB', 'passwd')
mydb = config.get('mysqlDB', 'db')

def decode_message(message):
    if(message): 
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
    return -1
    
def save_json(data_list):

    with open("data.json", 'r') as f:
        data = json.load(f)
    if data:
        id = max(data, key=lambda item:item['id'])
        struc = {
            "id": id['id']+1,
            "data_s":{
                "data": data_list
            }
        }    
    else:
        struc = {
            "id": 1,
            "data_s":{
                "data": data_list
            }
        }    
   
    data.append(struc)

    with open("data.json", 'w') as f:
        f.write(json.dumps(data, indent=4))

def get_data_db(cursor, row_id):
    try:
        cursor.execute("select popis from light_intense where id = %s", (row_id))
        return cursor.fetchone()
    except:
        print("NOT EXISTING MODEL ID")
        return 0

def get_data_file(row_id):
    with open('data.json', 'r') as f:
        data = json.load(f)
    for item in data:
        print(item)
        if item['id'] == int(row_id):
            print("JSON")
            print(item)
            return item
    return 0

def background_thread(args):
    counter = 0
    pwm_req = -1
    pwm_prev = 0
    dataList = []
    save = 0
    prev_id = -1
    prev_id_file = -1
    u = -1
    db = MySQLdb.connect(host=myhost,user=myuser,passwd=mypasswd,db=mydb)          

    while True:
        
        recived_data = ser.readline()
        arudino_message = decode_message(recived_data)
        
        if arudino_message == -1 or arudino_message > 255:
            continue

        if u == -1:
            u = arudino_message - (arudino_message/2)

        if args:

            if args.get('pwm_req') != None:
                pwm_req = dict(args).get('pwm_req')
                print("PWM_REQ: " + pwm_req)
                pwm_req = int(pwm_req)

                # regulation
                if pwm_req != pwm_prev:
                    print("PWM_PREV: " + str(pwm_prev))
                    pid = PID(0.1, 0.3, 0.25, setpoint=pwm_req, output_limits=(1,255), starting_output=u)
                    pwm_prev = pwm_req 

                u = pid(arudino_message)
                print("AKCNY ZASAH")
                print(u)
                ser.write(str.encode(str(int(u))))

                
            if not (pwm_req-15 < arudino_message and pwm_req+15 > arudino_message) :
                pwm_prev = pwm_req 
            
            if args.get("save") == 1 :
                save = 1
                dataDict = {
                    "t": time.time(),
                    "x": counter,
                    "y": arudino_message,
                    "u": u
                }

                dataList.append(dataDict)
                socketio.emit(
                    'sensor_data',
                    {
                        'data':arudino_message,
                        'count': counter,
                        'time': time.time()
                    },
                    namespace = '/prod'
                )
                counter = counter + 1 

               
            if save == 1 and args.get("save") == 0:
                save = 0 
                json_object = json.dumps(dataList, indent=4)
                print(str(dataList).replace("'", "\""))

                cursor = db.cursor()
                cursor.execute("insert into light_intense (popis) values (%s)", [json_object])
                db.commit()

                save_json(dataList)

                dataList = []

            if args.get("sql_id") is not None and prev_id != args.get("sql_id"): 
                prev_id = args.get("sql_id") 
                row_vals = get_data_db(db.cursor(), args.get("sql_id"))

                if row_vals != 0:
                    socketio.emit(
                        'sql_data',
                        {
                            'data': row_vals
                        },
                        namespace = '/prod'
                    )

            if args.get("file_id") is not None and prev_id_file != args.get("file_id"): 
                prev_id_file = args.get("file_id") 
                row_vals = get_data_file(args.get("file_id"))

                if row_vals != 0:
                    socketio.emit(
                        'json_data',
                        {
                            'data': row_vals
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
    print("ODPOJIŤ")
    ser.write(9998)
    disconnect()

@socketio.on('pwm_req', namespace='/prod')
def pwm_req(message):
    session['pwm_req'] = message['value']
    print(session['pwm_req'])
    print("REGULACIA")

@socketio.on('sql_id', namespace='/prod')
def pwm_req(message):
    session['sql_id'] = message['value']
    print("SQL_ID")

@socketio.on('file_id', namespace='/prod')
def pwm_req(message):
    session['file_id'] = message['value']
    print("FILE_ID")

@socketio.on('save', namespace='/prod')
def pwm_req(message):
    session['save'] = message['value']
    print("SAVING")

@socketio.on('reset', namespace='/prod')
def pwm_req():
    ser.write(str.encode(str(9999)))
    print("RESET")

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)