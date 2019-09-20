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


import time
import random

# zget("wallet_info")
while True:
    zset(
        "wallet_info",
    {
        "type": "eth",
        "addr": "0xabc",
        "amount": random.randint(1,101)
    })
    time.sleep(3)