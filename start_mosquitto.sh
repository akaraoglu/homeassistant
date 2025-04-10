#!/bin/sh

# Path to Mosquitto binary and config
MOSQUITTO_BIN="/bin/mosquitto"
MOSQUITTO_CONF="/data/mosquitto/mosquitto.conf"
LOGFILE="/data/mosquitto/mosquitto.log"

# Run Mosquitto in the background
echo "Starting Mosquitto..."
$MOSQUITTO_BIN -c $MOSQUITTO_CONF >> $LOGFILE 2>&1 &
echo "Mosquitto started with PID $!"
