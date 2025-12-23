# Configure Raspberry Pi Pico W as an MQTT Client using MicroPython

---

## I. Objectives

By the end of this session, participants will be able to:

- Set up Raspberry Pi Pico W devices as **MQTT clients**
- Set up a Raspberry Pi or Laptop as an **MQTT broker**
- Develop an MQTT-based solution using **Mosquitto**
- Understand and apply:
  - Quality of Service (QoS)
  - Last Will and Testament (LWT)
  - Retained messages

---

## II. Prerequisites and Setup

### A. Hardware & Software Requirements

- Raspberry Pi Pico W board
- Micro-USB cable (power + data)
- Computer with **[Thonny IDE](https://thonny.org/)** installed
- Raspberry Pi Pico W running the **latest MicroPython firmware**

---

### B. Installing MicroPython on Pico W

1. Hold the **BOOTSEL** button while connecting the Pico W to your computer  
2. The Pico W appears as a drive named **RPI-RP2**
3. Drag and drop the official MicroPython  
   [UF2 firmware file](https://micropython.org/resources/firmware/RPI_PICO_W-20251209-v1.27.0.uf2)
4. The Pico W reboots automatically into MicroPython
5. Open **Thonny** and ensure it is configured to use the Pico W interpreter

---

## III. MQTT Setup on MicroPython

MQTT (Message Queue Telemetry Transport) is a lightweight messaging protocol ideal for IoT applications where bandwidth and processing power are limited. It uses a **publish/subscribe** model built around topics.

---

### MQTT Components

- **Broker**  
  Routes messages between clients

- **Client**  
  A device that can publish, subscribe, or both

- **Topic**  
  A hierarchical string defining message routing

- **Quality of Service (QoS)**
  - QoS 0 – fire and forget
  - QoS 1 – at least once (ACK required)
  - QoS 2 – exactly once (heavy, not used here)

- **Last Will and Testament (LWT)**  
  A message published by the **broker on behalf of a client** if the client disconnects unexpectedly  
  *“Is this device still alive?”*

- **Retained Messages**  
  Stored by the broker and immediately sent to new subscribers  
  *“Last known state”*

---

### Example MQTT Architecture

![MQTT Example](https://github.com/drfuzzi/CSC2106_MQTT/assets/108112390/1f809798-135f-4cdc-be7e-0085df0b452f)

---

## IV. Setup Instructions

### 1. Setting Up the MQTT Broker (Laptop or Raspberry Pi)

We will use **Mosquitto MQTT Broker (version 2)**.  
Mosquitto v2 supports **MQTT v3.x and v5**.

Update the broker configuration to allow network access.

#### Configuration (`mosquitto.conf`)
```conf
listener 1883
allow_anonymous true

#### Start the broker

```bash
mosquitto -c mosquitto.conf -v
```

(Default port: **1883**)

---

### 2. Installing the MQTT Library on Pico W

The Pico W uses `umqtt.simple` for MQTT communication.

#### Steps

1. In Thonny **Files** view, create a folder named `lib`
2. Inside `lib`, create a folder named `umqtt`
3. Download `simple.py` from:
   [https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple](https://github.com/micropython/micropython-lib/tree/master/micropython/umqtt.simple)
4. Upload `simple.py` into the `umqtt` folder

---

## V. Example Codes

### A. Pico A — *Command Publisher* (Event-Driven)

#### Role Overview

* **Input device**
* Publishes commands based on button presses
* Does not subscribe to any topics

#### Hardware

* Button on **GP21**
* Button on **GP22**

#### MQTT Behaviour

* Publishes status to `csc2106/devA/status`
* Publishes commands:

  * `TOGGLE` → `csc2106/led/cmd`
  * `HELLO` → `csc2106/led/hello`
* Uses **QoS 1**
* Uses **LWT**
* Uses **retained status**

#### Retained Messages

* **Topic:** `csc2106/devA/status`
* **Behaviour:**

  * On connect → `"online"` *(retained)*
  * On crash → `"offline"` via LWT *(retained)*
* **Result:**

  * Monitoring clients instantly know Pico A’s state
  * No need to wait for a new publish

#### Quality of Service (QoS)

* **QoS Level:** QoS 1
* **Applied to:**

  * `csc2106/led/cmd`
  * `csc2106/led/hello`
  * `csc2106/devA/status`
* **Rationale:**

  * Button presses are important events
  * Losing a command is unacceptable
  * Broker acknowledgment is required

---

### B. Pico B — *Command Consumer + Actuator*

#### Role Overview

* **Always-on actuator**
* Subscribes to commands
* Controls an LED
* Publishes acknowledgements

#### Hardware

* LED on **GP20**

#### MQTT Behaviour

* Subscribes to `csc2106/led/cmd`
* Publishes ACK to `csc2106/led/ack`
* Publishes status to `csc2106/devB/status`
* Uses **QoS 1**
* Uses **LWT**
* Uses **retained status**

#### Availability Tracking (LWT + Retained Status)

* **Topic:** `csc2106/devB/status`
* **Behaviour:**

  * `"online"` on connect *(retained)*
  * `"offline"` on unexpected disconnect *(LWT, retained)*
* **Meaning:**

  * Pico B’s availability is independently tracked
  * Correct IoT heartbeat pattern

#### Quality of Service (QoS)

* **QoS Level:** QoS 1
* **Applied to:**

  * Subscription: `csc2106/led/cmd`
  * ACK publish: `csc2106/led/ack`
  * Status: `csc2106/devB/status`

#### Retained vs Event Messages

* **Retained:** `csc2106/devB/status`
* **Not retained:** `csc2106/led/ack`

  * ACKs are **events**, not state

---

## VI. Behavioural Differences — Why This Matters

* **State topics** → retained (`status`)
* **Event topics** → not retained (`cmd`, `ack`, `hello`)

| Aspect           | PicoA                | PicoB                     |
| ---------------- | -------------------- | ------------------------- |
| MQTT role        | Publisher            | Subscriber + publisher    |
| LWT              | Yes                  | Yes                       |
| QoS              | Publish QoS 1        | Subscribe + publish QoS 1 |
| Retained         | Status only          | Status only               |
| Message handling | Event-driven         | Continuous                |
| Failure handling | Reconnect on publish | Reconnect on receive      |

---

## VII. Persistent Sessions

To keep subscriptions active across disconnects:

```python
client = MQTTClient(CLIENT_ID, BROKER, clean_session=False)
```

---

## VIII. Troubleshooting

| Issue                | Solution                  |
| -------------------- | ------------------------- |
| No messages received | Check broker IP and topic |
| Wi-Fi not connecting | Verify SSID/password      |
| Client conflicts     | Use unique `CLIENT_ID`    |

---

## IX. References

* Mosquitto Install Guide
  [http://www.steves-internet-guide.com/install-mosquitto-broker/](http://www.steves-internet-guide.com/install-mosquitto-broker/)

* Mosquitto Client Guide
  [http://www.steves-internet-guide.com/mosquitto_pub-sub-clients/](http://www.steves-internet-guide.com/mosquitto_pub-sub-clients/)

* ThingsBoard MQTT Integration
  [https://thingsboard.io/docs/user-guide/integrations/mqtt/](https://thingsboard.io/docs/user-guide/integrations/mqtt/)

* ThingSpeak MQTT Basics
  [https://www.mathworks.com/help/thingspeak/mqtt-basics.html](https://www.mathworks.com/help/thingspeak/mqtt-basics.html)

```

---

If you want next:
- 🔹 tighten wording for students
- 🔹 extract this into **two lab handouts**
- 🔹 add **assessment checkpoints**
- 🔹 add **ACL + security section**

Say which one.
```
