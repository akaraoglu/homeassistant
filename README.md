# Xiaomi Gateway Integration with Home Assistant

Warning, this is a rabbit hole process that might suck you in. You may get lost on your way, in your life and walk around the darkness. Know your journey before you start the process. 
This repository provides all the steps and scripts needed to integrate your Xiaomi Gateway with Home Assistant. Using this guide, you can enable Telnet on the gateway, set up a dedicated Mosquitto MQTT broker, run the openmiio_agent to forward sensor data, and use a Python script to enable MQTT discovery in Home Assistant.

NOTE: 

 - The scripts are for only temperature/humidity sensors (miaomiaoce.sensor_ht.t2 - LYWSD03MMC).
 - Xiaomi Gateway used in this process is ZNDMWG02LM.
 - Have not tested this operation with a zigbee device or any other sensor.
 - Lumi Linux is a very strippeed version of linux. Make yourself familiar with `vi`, which I hae use to create and edit the files in the device.
 - The documentation is written with an LLM, so if there is any problems, please ping Altman and Zuck for it.
 - 
 
---

## Table of Contents

- [Overview](#overview)
- [Enabling Telnet on the Xiaomi Gateway](#enabling-telnet-on-the-xiaomi-gateway)
  - [Method B: Using miiocli or Another Command-Line Tool](#method-b-using-miiocli-or-another-command-line-tool)
- [Setting Up a Dedicated Mosquitto Broker](#setting-up-a-dedicated-mosquitto-broker)
- [Running openmiio_agent](#running-openmiio_agent)
  - [Deploy openmiio_agent to XiaomiGateway device](#deploy-openmiio_agent-to-xiaomigateway-device)
- [MQTT Discovery in Home Assistant](#mqtt-discovery-in-home-assistant)
- [License](#license)

---

## Overview

This project demonstrates how to integrate Xiaomi Gateway devices with Home Assistant by:

- Enabling Telnet access on the Xiaomi Gateway.
- Running a separate Mosquitto broker with custom configurations.
- Starting the [openmiio_agent](https://github.com/AlexxIT/openmiio_agent) (v1.2.1) to handle Xiaomi protocols.
- Utilizing a Python script to capture sensor data via MQTT and publish MQTT discovery messages to Home Assistant.

---

## Enabling Telnet on the Xiaomi Gateway

Accessing the underlying system of the Xiaomi Gateway can greatly expand what you can do with it. One recommended way to do this without relying on Home Assistant’s custom components is outlined below.

### Using miiocli or Another Command-Line Tool

If you don’t have Home Assistant set up yet or prefer manual control, follow these instructions:

1. **Install python-miio (miiocli):**

   On your PC (Windows, Linux, or macOS), install the Miio tool:
   
   ```bash
   pip install python-miio
   ```

2. **Confirm Your Gateway’s IP and Token:**

   You will need:
   - **IP:** `192.168.x.y`
   - **Token:** A 32-character hexadecimal string (e.g., `abcdef1234567890abcdef1234567890`)

3. **Send the JSON Payload:**

   Execute the following command to send a raw Miio command that chains a series of shell commands:
   
   ```bash
   miiocli device --ip 192.168.x.y --token abcdef1234567890abcdef1234567890 \
     raw_command set_ip_info \
     '{"ssid":"\"\"","pswd":"123123 ; passwd -d admin ; echo enable > /sys/class/tty/tty/enable; telnetd"}'
   ```

   **Explanation:**
   - The `--ip` and `--token` parameters specify the gateway’s connection details.
   - `raw_command set_ip_info` is the Miio method invoked.
   - The JSON payload for the `pswd` field chains multiple commands:
     - `123123`: The original password placeholder.
     - `passwd -d admin`: Removes the admin password.
     - `echo enable > /sys/class/tty/tty/enable; telnetd`: Enables and starts the Telnet daemon.

4. **Verify Telnet Access:**

   Open a terminal and run:

   ```bash
   telnet 192.168.x.y
   ```

   You should receive a shell prompt. The default username is  `admin` with no password.

---

## Setting Up a Dedicated Mosquitto Broker

First check if mosquitto is installed and where
```sh
which mosquitto
```
Keep the location of the mosquitto. If you need to install it, ask it to an LLM :) 

A dedicated Mosquitto broker allows you to isolate the MQTT messages used for integration. Create a configuration file (`mosquitto.conf`) with the following settings:

```ini
persistence false
log_dest stdout
listener 1884
bind_address 0.0.0.0
```

### Starting Mosquitto

Create a script (e.g., `start_mosquitto.sh`) to launch Mosquitto in the background:

```sh
#!/bin/sh

# Path to Mosquitto binary and config
MOSQUITTO_BIN="/bin/mosquitto"
MOSQUITTO_CONF="/data/mosquitto/mosquitto.conf"
LOGFILE="/data/mosquitto/mosquitto.log"

echo "Starting Mosquitto..."
$MOSQUITTO_BIN -c $MOSQUITTO_CONF >> $LOGFILE 2>&1 &
echo "Mosquitto started with PID $!"
```

Adjust the paths as necessary for your environment.

and run:

```sh
./start_mosquitto.sh
```
---

## Running openmiio_agent

The [openmiio_agent](https://github.com/AlexxIT/openmiio_agent) bridges Xiaomi sensor data to your MQTT broker. 
You can download binary manually from [v1.2.1](https://github.com/AlexxIT/openmiio_agent/releases/tag/v1.2.1).
 - MIPS for Xiaomi Multimode Gateway
 - ARM for Xiaomi Multimode Gateway 2 and Aqara Hub E1

and deploy it on your device.

### Deploy openmiio_agent to XiaomiGateway device

**Use a Simple HTTP (Not HTTPS) Server**  
Most BusyBox `wget`s on Xiaomi firmware support only plain HTTP (not HTTPS). You can host the file locally on your PC and download it via Telnet.

**On Your PC:**

1. Place the `openmiio_agent_mips` binary in a folder, e.g., `C:\temp` or `~/temp`.
2. Start a simple HTTP server in that folder (Python required):

```bash
cd ~/temp
python3 -m http.server 8000
```

On Windows (PowerShell):

```powershell
python -m http.server 8000
```
NOTE: Remember to allow Python through Firewall from:
 - Control Panel\System and Security\Windows Defender Firewall\Allowed applications

**Find Your PC’s IP Address:**

For example: `192.168.1.50`

**Telnet into the Gateway:**

```bash
telnet 192.168.1.x
```

**On the Gateway:**

```bash
cd /data
wget http://192.168.1.50:8000/openmiio_agent_mips -O openmiio_agent
chmod +x openmiio_agent
```

You should see a download message like:

```text
Connecting to 192.168.1.50:8000 (192.168.1.50:8000)
openmiio_agent_mips    100% |************************| ...
```


Now `openmiio_agent` is ready to execute.

### Starting openmiio_agent

Create a start script (e.g., `start_openmiio_agent.sh`):

```sh
#!/bin/sh

# Path to openmiio_agent binary
AGENT_BIN="/data/openmiio_agent/openmiio_agent_mips"
KEYS_FILE="/data/openmiio_agent/keys.json"

# Optional: Mi Cloud credentials (if needed)
MI_USER="xxxxxxxx"
MI_PASS="xxxxxxxx"

echo "Starting openmiio_agent..."

$AGENT_BIN miio cache central mqtt ble z3 \
  --mqtt.discovery_prefix=homeassistant \
  --mqtt.topic_prefix=lumi \
  --mqtt.host=127.0.0.1 \
  --mqtt.server=127.0.0.1 \
  --mqtt.port=1884 \
  --cloud.username=$MI_USER \
  --cloud.password=$MI_PASS \
  --cloud.region=de \
  --zigbee.tty=/dev/ttyS1 \
  --log.level=trace >> /data/openmiio_agent/openmiio.log 2>&1 &

echo "openmiio_agent started with PID $!"
```

and run:

```sh
./start_openmiio_agent.sh
```
This script will initialize the agent to handle multiple communication protocols and push data to the Mosquitto broker.

You can run this script to see if the MQTT is working as expected. You will see a lot of messages as the agent log is set to trace. If you keep looking and wait enough, you will also see '_async.ble_event' messages, which includes updates about the bluetooth devices. 

```sh
mosquitto_sub -t '#' -v
```

---

## MQTT Discovery in Home Assistant

The following Python script listens to MQTT messages published by the openmiio_agent, parses BLE sensor data, and publishes MQTT discovery messages for Home Assistant to auto-configure sensors.

Python Script: mqtt_discovery.py


- **MQTT Connection & Subscription:** The script connects to your MQTT broker and subscribes to the `miio/report` topic.
- **Data Parsing:** Parses BLE event data (temperature, humidity, battery).
- **Publishing Discovery Payloads:** Publishes MQTT discovery messages for Home Assistant auto-configuration.

---

## License

This project is licensed under the [MIT License](LICENSE).
