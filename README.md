## Zedis Tutorial

Today we'll build a simple dashboard framework. We'll use Zedis+Flask+React since we love the simplicty of Python for a backend and power of React for the front end. 

We want our app to be able to do a few things. 

1. get some information periodically
2. store the most recent values (even if app is off)
3. display the values in a web ui
4. auto update the display every few seconds

Cool, if that works we can add some styling and have a useful app! However we also want to make the building experience as easy as possible.

We want to

1. not write database and migration code (slows down our iterative process)
2. read and write to a data store at the same time (this means we can't use a file)
3. make the app modular (we might want to add a nerural net later! 🤪)
4. write the least code 
5. write code with few bugs (less code less room for bugs)
6. use little CPU resources (I wanna run this all the time and not slow things down)
7. not run another service (like a redis container - then we'd need docker)
8. not worry about performance, want something fast, scalable and super performant


Based on all those statements above - we look to zedis to make this process easy and powerful.

Zedis is a just a tiny protocol and glue between two time tested and well written projects. ZMQ written in C and used by CERN and other mission critical companies/programs, and Sled is a modern key value store written in Rust that is fast, lock free, safe and no nonsense. 

Not every wants to write Rust to get the benifits of Sled, luckily ZMQ acts as a perfect transport layer between Sled and any programming language of your choice. 

This way you can read/write from zedis from practiaclly any language without a zedis specific client library, you just need your favorite languauges' ZMQ client. 

Now that you can communicate with Zedis, you'll need to speak it's languauge. This is very simple is only consists of 5 commands. `GET`, `SET`, `DEL`, `KEYS` and `PRE`. You should be able to decern what these keys do from their names, or refer to the docs for more info.

Cool, we have a system that allows us to leverage the Sled KV with simple commands. We can call it from any language and get guarantees like lock free read writes, parallel transport with ZMQ and the reliability of both systems. 🙌

We can get the latest version of Zedis by cloning the github repo and building it locally. 

The following commands fetch and build zedis, then saves the binary in your executables path so you can run `zedis` from the cli

```
git clone https://github.com/drbh/zedis.git
cd zedis
cargo build --release
sh install.sh
```

now you should be able to run

```
zedis
```

note: this will create a db in any directory it is execute from. 


## Learn how to save and retrive

Now that we have zedis lets do a small test in python to undersand how we'll use this in our app. 

This will open a connection to the zedis datastore

```python
import zmq
import json

port = "5555"

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:%s" % port)
```

now we can send it commands via the `socket` object. We'll set a value. 

```python
socket.send_string("SET mycoolkey this is my first value!");socket.recv()
# 'done.'
```
note: we cant have spaces in the key, but we can have all the spaces we want in the value!


Now to get the data back we'll send a `GET` command for our `mycoolkey`.

```python
socket._string("GET mycoolkey");socket.recv()
```

## Using in out app

Now that we can save and retrive. We can mock up a crypto service (easily add a HTTP request in place of the `random` data in this example)

First thing we need to add our boiler plate (that code we learned about above). Just here we wraped up those get and set calls into functions called `zget` and `zset` respectivly.

```python
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

def zget(key):
    socket.send_string("GET "+key)
    return json.loads(socket.recv())
# continues below
```

Next we'll update that value every 3 seconds

```python
import time
import random

while True:
    zset(
        "wallet_info",
    {
        "type": "eth",
        "addr": "0xabc",
        "amount": random.randint(1,101)
    })
    time.sleep(3)
```

Putting these two scripts together give us the `updater.py` script - that will update our wallet info every 3 seconds indefinalty with a random value. Like noted above this could actually make a HTTP call to get a real crypto wallet's balance.


Next we move on to the server that will distribute this info where we want!

## serving it up 🎾

we need a way for a person or webapp to access the data stored in zedis. Not a problem we'll reuse the boiler plate connection code above. 


```python
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

def zget(key):
    socket.send_string("GET "+key)
    return json.loads(socket.recv())
```

and we'll add a tiny tiny flask server below that boiler plate. This code will start a server on `http://localhost:5000/` and resolve two routes `/` and `/data/<key>`. The first one returns our web page (we havent made yet) and the second one allows us to pass a key in the url, then look up that key in our zedis store with the familar `zget`. We add some json headers and send it back.

```
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
```

Now all we need to do is create `index.hmtl` that make request to the `data` endpoint. Easy enough.

Since we'll likely want to expand the apps functionality in the future we want to use a productive web framework. Since we all ❤️ React, its the obvious choice. This will also save time and headaches later. 

We want a minimal footprint to get our first iterations up, so we'll just load in React from cloudflares cdn (it should be pre compiled for production).

We'll want the app to request data when it's first opened, then request again every second later.

note: A read operation is super fast and only takes nanoseconds to execute and some more microseconds to return, so the 1 second interval has practically no impact on zedis' resource consumption. 

In React terms, we'll want to make a request when the Application component is rendered read the response and update the current state. We'll want to display that state so we add some JSX exposing `this.state.walletInfo`. One way of implementing this is shown below. 

```html
<div id="root"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.2/react.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.2/react-dom.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/6.21.1/babel.min.js"></script>
<style>
    html {
        font-family: 'Source Code Pro', monospace;
    }
</style>
<script type="text/babel">
    class Application extends React.Component {
    constructor(props) {
        super(props);
        this.getWalletInfo()
        this.state = { walletInfo: "", }
        setInterval(function(){
            this.getWalletInfo()
        }.bind(this),1000)
    }

    getWalletInfo() {
        fetch("/data/"+"wallet_info", {
          "method": "GET",
          "headers": {
            "content-type": "application/json"
          }
        })
        .then(response => {
            response.json().then(r =>{
                this.setState({walletInfo: r})
            })
        })
        .catch(err => {
          console.log(err);
        });
    }
    
    render() {
        return (
        <div className="main">
            <div className="top">
                <h3>DASHBOARD START</h3>
            </div>
            <div className="bottom">
                <pre>
                    {
                        this.state.walletInfo != "" &&
                        JSON.stringify(this.state.walletInfo,null,2) 
                    }
                </pre>
            </div>
        </div>);
    }
}
ReactDOM.render(
    <Application />,
    document.getElementById('root')
);
</script>
```

Great! We now have a <60 line html file that will interact with our server and subsuquently read data from zedis. 

Our read time is well under 1 milisecond, and writes not much slower. Our server, updater ad react app are modular and microservice'y. Notice that we have two seperate programs (updater and server) reading and writing to the datastore at the same time! This is not possible with datastores that use locks - where if more than one program tries to access a currenly locked file it crashes. Zedis does not lock, therefore avoids this issue. Zedis does also leverages brokerless communication so it does not need to run any extra services (like Redis or Postgres), zedis acts as a embedded, brokerless datastore.

However, the point is to forget all of those technical feats - and have a developer friendly datastore that has the power of prominate databases but much less overhead and simplier concepts.

End result, we have a ~30 line updater script, a ~35 line server and ~60 line react app that updates a personal dashboard in near real time!

What can you build with zedis? Whens a time zedis was a drop in replacement for you?