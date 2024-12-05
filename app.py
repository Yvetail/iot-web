import paho.mqtt.client as paho
from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def on_connect(client, userdata, flags, rc):
    print('CONNACK received with code %d.' % (rc))

client = paho.Client()
client.on_connect = on_connect
client.connect('broker.mqttdashboard.com', 1883)


if __name__ == '__main__':
    app.run(debug=True)
