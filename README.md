# Configure Raspberry Pi Pico W as an MQTT Client using MicroPython

## I. Objectives

By the end of this session, participants will be able to set up their Raspberry Pi Pico W (as clients) and Raspberry Pi/Laptop (as broker) to develop a solution using Mosquitto's MQTT. They will also explore MQTT features like QoS, LWT, and retained messages.

## II. Prerequisites and Setup

### A. Hardware & Software

  * Raspberry Pi Pico W board.
  * Micro-USB cable for power and data.
  * Computer with a **[Thonny](https://thonny.org/)** IDE (for MicroPython development).
  * The Pico W must be running the **latest MicroPython firmware**.

### B. Installing MicroPython

1.  If not already done, hold the **BOOTSEL** button while connecting the Pico W to your computer.
2.  The Pico W should appear as a drive named **RPI-RP2**.
3.  Drag and drop the official MicroPython [UF2 file](https://micropython.org/resources/firmware/RPI_PICO_W-20251209-v1.27.0.uf2) onto this drive. The drive will disappear, and the Pico W will reboot running MicroPython.
4.  Open **Thonny** and ensure it is configured to talk to the Pico W.

---

## III. MQTT Setup on MicroPython
MQTT (Message Queue Telemetry Transport) is a lightweight messaging protocol ideal for IoT applications where network bandwidth and processing power are limited. It works on a publish/subscribe model using topics, making it easy to send and receive messages between devices.

### MQTT Components
- **Broker:** Handles all message routing between clients.
- **Client:** A device that can publish, subscribe, or both.
- **Topic:** A hierarchical string that defines where messages are published and from where they are subscribed.
- **QoS (Quality of Service)**
  - **QoS 0** – fire and forget
  - **QoS 1** – at least once (ACK required)
  - **QoS 2** – exactly once (heavy, not used here)
- **Last Will and Testament:** LWT is a message the **broker publishes on behalf of the client** if the client disconnects **unexpectedly** (power loss, crash, Wi-Fi drop).
  - *“Is this device still alive?”*
- **Retained messages:** A retained message is **stored by the broker** and immediately sent to **new subscribers**.
  - *“last known state”*


Example MQTT architecture:

![MQTT Example](https://github.com/drfuzzi/CSC2106_MQTT/assets/108112390/1f809798-135f-4cdc-be7e-0085df0b452f)

---

## Setup Instructions

### 1. Setting Up MQTT Broker (on your laptop or Raspberry Pi)
We will use Mosquitto MQTT broker [version 2](http://www.steves-internet-guide.com/download/6-bit-mosquitto-v2/). After unzipping, update the configuration file (`mosquitto.conf`) to allow network address listening. Note that version 2 mosquitto supports MQTT version 3 and 5.

<!--
![overview](https://github.com/user-attachments/assets/ccd7d55a-ce37-42c3-99f8-d6a004bc2fe9)
Figure 2: Overview of the Lab Excercise
-->

#### Steps:
- Update `mosquitto.conf` as shown in below.
- Start the broker with `mosquitto -c mosquitto.conf -v` in the command prompt. Default port is 1883.

```
listener 1883
allow_anonymous true
```

---

### 2. Install MQTT Library
You need the `umqtt.simple` library for MQTT communication:
1. In Thonny's **Files** view, create a folder named `lib` on the Pico W.

<img width="308" height="85" alt="image" src="https://github.com/user-attachments/assets/0630f00d-4dc0-43b6-893f-7b1bdf3943df" />
<!--
 <img src="/img/Thonny Where to Find Files.png" width=25% height=25%>
<img src="/img/Thonny Seperate Files.png" width=25% height=25%>
<img src="/img/Thonny Create Directory(Folder).png" width=25% height=25%>
-->

3. Inside `lib`, create another folder named `umqtt`.

4. Download `simple.py` from the [MicroPython Library](https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple) and upload it into the `umqtt` folder.

<img src="/img/Thonny File Upload.png" width=25% height=25%>
<img src="/img/Thonny Options.png" width=25% height=25%>
<img src="/img/Thonny Connecting Pico.png" width=45% height=45%>
---

## Example Codes

 <img src="/img/Thonny How to Run Code.png" width=25% height=25%>

### A. Pico A → *Command publisher* (event-driven, button presses)
* **Hardware input**: Reads two buttons on **GP21** and **GP22** (`Pin.IN`, pull-ups). 
* **MQTT behaviour**: Connects, publishes **status online/offline** to `csc2106/devA/status`. 
* **Publishes messages**:

  * On GP21 press: publishes `TOGGLE` to `csc2106/led/cmd` (QoS 1). 
  * On GP22 press: publishes `HELLO` to `csc2106/led/hello` (QoS 1). 
* **No subscriptions**: It does not subscribe or process incoming MQTT messages. 
* **Reconnect logic**: Only attempts reconnect **when a publish fails** (inside `publish_toggle()` / `publish_hello()`). 
* Sets an LWT on: `csc2106/devA/status`
* LWT payload: `"offline"`
* Published **with retain = True**

---
Meaning:
* If Pico A dies suddenly, the broker publishes: `csc2106/devA/status = offline (retained)`
* Any subscriber immediately sees Pico A as offline.

Uses **QoS 1** for:
* Command messages: `csc2106/led/cmd` & `csc2106/led/hello`
* Status messages: `csc2106/devA/status`

Why this makes sense:
* Button presses are **important events**
* Losing a TOGGLE command is bad
* QoS 1 ensures the broker receives it (with ACK)
---

**picoA.py (publisher driven by buttons)**
```python
import network, time
from umqtt.simple import MQTTClient
from machine import Pin

# ==== EDIT THESE ====
SSID = "SSID"
PASSWORD = "SSID-Password"
BROKER = "BROKER-IP"
CLIENT_ID = b"PicoA"
# ====================

BUTTON_PIN_21 = 21  # GP21 -> button to GND
BUTTON_PIN_22 = 22  # GP22 -> button to GND
CMD_TOPIC     = b"csc2106/led/cmd"
HELLO_TOPIC   = b"csc2106/led/hello"
STATUS_TOPIC  = b"csc2106/devA/status"

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
```
### B. Pico B → *Command consumer + actuator* (always listening, reacts to commands)
* **Hardware output**: Drives an LED on **GP20** (`Pin.OUT`). 
* **MQTT behaviour**: Connects, sets a callback, **subscribes** to `stm/led/cmd` (QoS 1), and publishes **status online/offline** to `stm/devB/status`. 
* **Processes incoming messages**:

  * If it receives `TOGGLE` on `stm/led/cmd`, it toggles the LED and publishes an ACK (`ON`/`OFF`) to `stm/led/ack` (QoS 1). 
* **Reconnect logic**: Continuously calls `client.check_msg()`; if any MQTT error occurs, it reconnects. 
* **Note**: `on_msg()` uses the global `client` variable (works here because `client` is defined globally after `make_client()`). 

* Same pattern, but for: `csc2106/devB/status`
* Also publishes `"online"` on successful connect
* LWT publishes `"offline"` on unexpected disconnect

---
Meaning:
* Pico B’s availability is independently tracked.
* This is the **correct IoT heartbeat pattern**.

Uses **QoS 1** for:
* Subscription to: `csc2106/led/cmd`
* ACK publish to: `csc2106/led/ack`
* Status messages: `csc2106/devB/status`

Why this makes sense:
* Device must not miss commands
* ACK must reliably reach observers
* Exactly matches expected behaviour of an actuator
---


**picoB.py (subscriber/actuator that toggles an LED)**
```
import network, time
from umqtt.simple import MQTTClient
from machine import Pin

# ==== EDIT THESE ====
SSID = "SSID"
PASSWORD = "SSID-Password"
BROKER = "BROKER-IP"
CLIENT_ID = b"PicoB"
# ====================

LED_PIN = 20   # GP20 -> LED+ (through resistor) to GND
CMD_TOPIC   = b"csc2106/led/cmd"
ACK_TOPIC   = b"csc2106/led/ack"
STATUS_TOPIC= b"csc2106/devB/status"

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


```

## Advanced MQTT Configuration

### 1. Quality of Service (QoS)
MQTT supports three QoS levels:

QoS 0: At most once (no guarantee of delivery)

QoS 1: At least once (may deliver duplicates)

QoS 2: Exactly once (most reliable, but slowest)

Example with QoS 1:
```
mqtt.subscribe("pico/led", qos=1)
mqtt.publish("pico/led", "on", qos=1)
```

### 2. Last Will & Testament (LWT)

Notifies subscribers if a client disconnects unexpectedly:
```
client = MQTTClient(CLIENT_ID, BROKER, keepalive=60)
client.set_last_will("pico/status", "offline", retain=True)
```

### 3. Retained Messages

Ensures new subscribers immediately receive the last published message:
```
mqtt.publish("pico/led", "on", retain=True)
```

### 4. Persistent Sessions

Keep subscriptions active even when the client disconnects:
```
client = MQTTClient(CLIENT_ID, BROKER, clean_session=False)
```

## Troubleshooting
-------------------------------------------------------------------------
| Issue                        | Solution                               |
| ---------------------------- | -------------------------------------- |
| No messages received         | Check broker IP and topic name         |
| Wi-Fi not connecting         | Verify SSID/password, signal strength  |
| Multiple clients conflicting | Use unique `CLIENT_ID` for each client |
-------------------------------------------------------------------------

<!--
## Lab Assignment

Configure two Pico W devices.
Device A controls Device B's LED via MQTT.
Use retained messages and LWT to improve reliability.
-->

## References
Mosquitto Install Guide (http://www.steves-internet-guide.com/install-mosquitto-broker/)

Mosquitto Client Guide(http://www.steves-internet-guide.com/mosquitto_pub-sub-clients/)

Thingsboard MQTT Integration (https://thingsboard.io/docs/user-guide/integrations/mqtt/)

ThingSpeak MQTT Basics (https://www.mathworks.com/help/thingspeak/mqtt-basics.html)
