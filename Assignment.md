# Assignment: Nodes Interaction with MQTT

## I. Overview

The examples provided show separate code for the publisher and the subscriber. In this assignment, you will combine both roles into a single node that can both publish and subscribe.

## II. The Task

Integrate the codes of 'picoA.py' and 'picoB.py'.

### Functional Requirements

Node A <-> Node B
1. Node A shall publish a control message to a predefined MQTT topic (e.g., csc2106/nodeB/led/cmd) based on button presses (e.g. GP21).
2. Node B shall subscribe to the control topic and listen for incoming control messages.
3. Node B shall toggle its onboard LED state (ON ↔ OFF), upon receiving a valid control message,
4. Node B shall publish a control message to a predefined MQTT topic (e.g., csc2106/nodeA/led/cmd) based on button presses (e.g. GP21).
5. Node A shall subscribe to the control topic and listen for incoming control messages.
6. Node A shall toggle its onboard LED state (ON ↔ OFF), upon receiving a valid control message,

## II. Submission & Demo

You must demonstrate your working code to the instructor and submit it to the LMS dropbox. (You may perform the demonstration in pairs.)

### The Demo Steps:

1. Configure two Pico as Node A and Node B and connect both to the same MQTT broker.
2. Implement button press on Node A to publish a message that toggles Node B’s LED.
3. Verify Node B toggles its LED.
4. Implement button press on Node B to publish a message that toggles Node A’s LED.
5. Verify Node A toggles its LED.
