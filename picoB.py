import network, time
from umqtt.simple import MQTTClient
from machine import Pin

# ==== EDIT THESE ====
SSID = "SSID"
PASSWORD = "password"
BROKER = "10.122.12.25"
CLIENT_ID = b"PicoB"
# ====================

LED_PIN = 20   # GP20 -> LED+ (through resistor) to GND
CMD_TOPIC   = b"stm/led/cmd"
ACK_TOPIC   = b"stm/led/ack"
STATUS_TOPIC= b"stm/devB/status"

led = Pin(LED_PIN, Pin.OUT, value=0)

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.2)
    print("WiFi:", wlan.ifconfig())

def on_msg(topic, msg):
    if topic == CMD_TOPIC and msg == b"TOGGLE":
        led.value(0 if led.value() else 1)
        state = b"ON" if led.value() else b"OFF"
        print("Toggled LED ->", state)
        try:
            client.publish(ACK_TOPIC, state, qos=1)
        except Exception as e:
            print("Ack publish error:", e)

def make_client():
    c = MQTTClient(CLIENT_ID, BROKER, keepalive=30)
    c.set_last_will(STATUS_TOPIC, b"offline", retain=True, qos=1)
    c.connect()
    c.set_callback(on_msg)
    c.subscribe(CMD_TOPIC, qos=1)
    c.publish(STATUS_TOPIC, b"online", retain=True, qos=1)
    print("MQTT connected, subscribed, status=online")
    return c

wifi_connect()
client = make_client()

while True:
    try:
        client.check_msg()   # non-blocking; calls on_msg when something arrives
    except Exception as e:
        print("MQTT error, reconnecting...", e)
        try:
            client.disconnect()
        except:
            pass
        time.sleep(1)
        client = make_client()
    time.sleep(0.02)

