import zmq
import json

port = "5555"

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:%s" % port)

def zset(key, value):
    socket.send_string(
    	"SET "+str(key)+" "+json.dumps(value));
    socket.recv()
    return True
# 'done.'
def zget(key):
    socket.send_string("GET "+key)
    return json.loads(socket.recv())
    

from flask import Flask, render_template, jsonify
app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route('/data/<key>')
def get_data(key):
    return jsonify(zget(key))


if __name__ == '__main__':
    app.run()