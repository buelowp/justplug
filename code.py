import wifi
import time
import ssl
import socketpool
import sys
import json
import board
import digitalio
import pwmio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from secrets import secrets

ssid = secrets["ssid"]

print("Connecting to", ssid)

wifi.radio.connect(ssid, secrets["password"])

print("Connected to", ssid)
print("IP:", wifi.radio.ipv4_address)

led1 = pwmio.PWMOut(board.D11, frequency=5000, duty_cycle=0)
led2 = pwmio.PWMOut(board.D12, frequency=5000, duty_cycle=0)
led3 = pwmio.PWMOut(board.A0, frequency=5000, duty_cycle=0)
led4 = pwmio.PWMOut(board.A1, frequency=5000, duty_cycle=0)
led5 = pwmio.PWMOut(board.D9, frequency=5000, duty_cycle=0)
led6 = pwmio.PWMOut(board.D10, frequency=5000, duty_cycle=0)
led7 = pwmio.PWMOut(board.A2, frequency=5000, duty_cycle=0)
led8 = pwmio.PWMOut(board.A3, frequency=5000, duty_cycle=0)

leds = { 1 : led1, 2 : led2, 3 : led3, 4 : led4 , 5 : led5, 6 : led6, 7 : led7, 8 : led8 }

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = True
ledstate = True

def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

### Code ###
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    print("Connected to MQTT Broker!")
    print("Flags: {0} RC: {1}".format(flags, rc))
    mqtt_client.subscribe("justplug/#")

def disconnect(mqtt_client, userdata, rc):
    print("Disconnected from MQTT Broker!")

def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))

# Topic justplug/{on|off}
# { "pins" : [ 1, 2, 3...] }
# Topic justplug/dim
# { "pins" : [ { pinnum, "percent" : percent dim 0-65535 as an integer }, ... ] }
def message(client, topic, message):
    print("Message on topic {0}".format(topic))

    try:
        content = json.loads(message)
    except Exception as e:
        print("JSON exception: " + str(e))
        return

    if topic == "justplug/on":
        for pin in content['pins']:
            print("Setting pin {0} to on".format(pin))
            if pin > 0 and pin < 9:
                try:
                    leds[pin].duty_cycle = 65535
                except Exception as e:
                    print("LED ON Array exception {0}".format(str(e)))

    if topic == "justplug/off":
        for pin in content['pins']:
            print("Setting pin {0} to off".format(pin))
            if pin > 0 and pin < 9:
                try:
                    leds[pin].duty_cycle = 0
                except Exception as e:
                    print("LED OFF Array exception {0}".format(str(e)))

    if topic == "justplug/dim":
        for pin in content['pins']:
            dc = int(translate(pin["pct"], 0, 100, 0, 65535))
            print("Setting PWM translated from {0} to {1}".format(pin["pct"], dc))
            if pin["pin"] > 0 and pin["pin"] < 9:
                try:
                    leds[pin["pin"]].duty_cycle = dc
                except Exception as e:
                    print("Unable to set PWM value of {0}: {1}".format(dc, str(e)))

pool = socketpool.SocketPool(wifi.radio)
mqtt_client = MQTT.MQTT(
    broker=secrets["broker"],
    port=secrets["port"],
    socket_pool=pool,
)

mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_message = message

print("Attempting to connect to %s" % mqtt_client.broker)
try:
    mqtt_client.connect()
except Exception as e:
    print("Exception: " + str(e))
    sys.exit()

while True:
    if mqtt_client.is_connected():
        mqtt_client.loop()
    else:
        mqtt_client.reconnect()

    if ledstate == True:
        led.value = False
        ledstate = False
    else:
        led.value = True
        ledstate = True

    time.sleep(.1)