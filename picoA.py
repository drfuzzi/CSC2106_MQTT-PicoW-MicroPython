import network, time
from umqtt.simple import MQTTClient
from machine import Pin

# ==== EDIT THESE ====
SSID = "SSID"
PASSWORD = "password"
BROKER = "10.122.12.25"
CLIENT_ID = b"PicoA"
# ====================

BUTTON_PIN_21 = 21  # GP21 -> button to GND
BUTTON_PIN_22 = 22  # GP22 -> button to GND
CMD_TOPIC     = b"stm/led/cmd"
HELLO_TOPIC     = b"stm/led/hello"
STATUS_TOPIC  = b"stm/devA/status"

# Initialize both button pins
btn21 = Pin(BUTTON_PIN_21, Pin.IN, Pin.PULL_UP)
btn22 = Pin(BUTTON_PIN_22, Pin.IN, Pin.PULL_UP)

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.2)
    print("WiFi:", wlan.ifconfig())

def make_client():
    # keepalive ensures broker notices disconnection; LWT tells others you're offline
    c = MQTTClient(CLIENT_ID, BROKER, keepalive=30)
    c.set_last_will(STATUS_TOPIC, b"offline", retain=True, qos=1)
    c.connect()
    # Advertise we're online (retained so late subscribers see it)
    c.publish(STATUS_TOPIC, b"online", retain=True, qos=1)
    print("MQTT connected & status=online")
    return c

# Function to handle publishing and reconnection logic
def publish_toggle(client):
    try:
        client.publish(CMD_TOPIC, b"TOGGLE", qos=1)
        return client # return the same client if successful
    except Exception as e:
        # try to re-connect once
        print("Publish failed, reconnecting...", e)
        try:
            client.disconnect()
        except:
            pass
        return make_client() # return a new client

# Function to handle publishing and reconnection logic
def publish_hello(client):
    try:
        client.publish(HELLO_TOPIC, b"HELLO", qos=1)
        return client # return the same client if successful
    except Exception as e:
        # try to re-connect once
        print("Publish failed, reconnecting...", e)
        try:
            client.disconnect()
        except:
            pass
        return make_client() # return a new client

def main():
    wifi_connect()
    client = make_client()

    # simple edge detect without debouncing
    last21 = btn21.value()
    last22 = btn22.value()
    
    # Removed: last_change, DEBOUNCE_MS

    while True:
        # Check Button 21 (GP21)
        v21 = btn21.value()
        if v21 != last21:
            last21 = v21
            if v21 == 0:  # pressed
                print("Button 21 pressed -> publish TOGGLE")
                client = publish_toggle(client) # Update client if re-connection occurred

        # Check Button 22 (GP22)
        v22 = btn22.value()
        if v22 != last22:
            last22 = v22
            if v22 == 0:  # pressed
                print("Button 22 pressed -> publish HELLO")
                client = publish_hello(client) # Update client if re-connection occurred

        # let the broker know we're alive (keepalive pings happen under the hood)
        time.sleep(0.02)

main()
