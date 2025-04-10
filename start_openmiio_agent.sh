#!/bin/sh

# Path to openmiio_agent binary
AGENT_BIN="/data/openmiio_agent/openmiio_agent_mips"
KEYS_FILE="/data/openmiio_agent/keys.json"

# Optional: Mi Cloud credentials (if needed)
MI_USER="username@mail.com"
MI_PASS="passwd"

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
