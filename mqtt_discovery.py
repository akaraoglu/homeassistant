import json
import paho.mqtt.client as mqtt
import binascii
import time

# Optional: BLE bind keys for known devices (MAC → key)
bind_keys = {
    "xxxxx": bytes.fromhex("xxxxx"),
    "xxxxx": bytes.fromhex("xxxxx"),
    "xxxxx": bytes.fromhex("xxxxx"),
    "xxxxx": bytes.fromhex("xxxxx"),
    # Add more here if needed
}

# Parse BLE edata based on eid
def parse_edata(eid, edata_hex):
    edata = bytes.fromhex(edata_hex)
    if eid == 4100:  # temperature
        if len(edata) >= 2:
            val = int.from_bytes(edata[:2], "little", signed=True)
            return {"temperature": val / 10}
    elif eid == 4102:  # humidity
        if len(edata) >= 2:
            val = int.from_bytes(edata[:2], "little")
            return {"humidity": val / 10}
    elif eid == 4106:  # battery
        if len(edata) >= 1:
            return {"battery": edata[0]}
    else:
        return {"eid": eid, "raw": edata_hex}
    return {}

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")
    client.subscribe("miio/report")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get("method") == "_async.ble_event":
            dev = payload["params"]["dev"]
            mac = dev["mac"]
            pdid = dev["pdid"]
            evt = payload["params"]["evt"]

            for entry in evt:
                eid = entry.get("eid")
                edata = entry.get("edata")
                parsed = parse_edata(eid, edata)
                if not parsed:
                    continue

                for key, value in parsed.items():
                    device_id = mac.replace(":", "").lower()
                    unique_id = f"{device_id}_{key}"
                    state_topic = f"homeassistant/sensor/{unique_id}/state"
                    config_topic = f"homeassistant/sensor/{unique_id}/config"

                    # MQTT discovery config
                    sensor_config = {
                        "name": f"{key.capitalize()} {mac[-5:].replace(':', '')}",
                        "uniq_id": unique_id,
                        "stat_t": state_topic,
                        "dev_cla": {
                            "temperature": "temperature",
                            "humidity": "humidity",
                            "battery": "battery"
                        }.get(key),
                        "unit_of_meas": {
                            "temperature": "°C",
                            "humidity": "%",
                            "battery": "%"
                        }.get(key),
                        "device": {
                            "identifiers": [device_id],
                            "name": f"BLE Sensor {mac[-5:].replace(':', '')}",
                            "manufacturer": "Xiaomi",
                            "model": f"PDID {pdid}"
                        }
                    }

                    # Publish discovery config (retain = true)
                    client.publish(config_topic, json.dumps(sensor_config), retain=True)
                    time.sleep(1)  # Give HA time to process discovery
                    # Publish sensor value
                    client.publish(state_topic, value, retain=True)
                    print(f"Published {key}: {value} to {state_topic}")

    except Exception as e:
        print(f"Failed to parse message: {e}")

# Connect to local broker
mqtt_host = "192.168.1.26"
mqtt_port = 1883

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_host, mqtt_port, 60)
client.loop_forever()
