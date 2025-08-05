#!/bin/bash
# listener.sh - heartbeat listener and failure detection

PORT=9000
TIMEOUT_MS=150
CHECK_INTERVAL=0.05
GRACE_PERIOD=30000  # 30 seconds (changed from 3000)

LOGFILE="/var/log/heartbeat-listener.log"
exec >> "$LOGFILE" 2>&1

now() { date +%s%3N; }
log() { echo "$(date '+%F %T') [listener] $*"; }

last=0
heartbeat_received=0
start_time=$(now)
link_down=0

log "Starting heartbeat listener on UDP port $PORT"

nc -ulp $PORT |
while IFS= read -r _; do
  last=$(now)
  heartbeat_received=1
done &
listener_pid=$!
trap "kill $listener_pid" EXIT

while true; do
  sleep $CHECK_INTERVAL
  current=$(now)

  if (( heartbeat_received == 0 )); then
    if (( current - start_time > GRACE_PERIOD )); then
      log "failure: no heartbeat received during startup grace period"
    fi
    continue
  fi

  diff=$(( current - last ))
  if (( diff > TIMEOUT_MS )); then
    if (( link_down == 0 )); then
      log "failure: heartbeat timeout (no packet for ${diff} ms)"
      link_down=1
    fi
    last=$current
  else
    if (( link_down == 1 )); then
      log "recovery: heartbeat resumed"
      link_down=0
    fi
  fi
done
