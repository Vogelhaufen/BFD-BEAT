#!/bin/bash
# sender.sh - heartbeat sender

REMOTE=10.0.0.2   # Change to server IP
PORT=9000
INTERVAL_MS=50    # Heartbeat interval in milliseconds

LOGFILE="/var/log/heartbeat-sender.log"
#exec >> "$LOGFILE" 2>&1

echo "$(date '+%F %T') [sender] Starting heartbeat sender to $REMOTE:$PORT"

while true; do
  printf . | nc -u -w1 "$REMOTE" $PORT
  sleep $(awk "BEGIN{print $INTERVAL_MS/1000}")
done
