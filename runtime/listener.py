import subprocess
import socket
import time
from datetime import datetime

PORT = 9000
GRACE_PERIOD = 3  # seconds

def on_failure():
    cmd = ["echo", "Heartbeat failure detected!"]  # Replace with your real command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing failure command: {e}")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', PORT))
sock.settimeout(1)  # Non-blocking with 1 second timeout

last_heartbeat = time.time()
last_status = "OK"

print(f"[{datetime.now()}] Listening for heartbeats on UDP port {PORT}")

while True:
    try:
        data, addr = sock.recvfrom(1024)
        print(f"[{datetime.now()}] Heartbeat OK (received from {addr}): {data.decode().strip()}")
        last_heartbeat = time.time()
        last_status = "OK"
    except socket.timeout:
        # No data received in the last second
        now = time.time()
        diff = now - last_heartbeat
        if diff > GRACE_PERIOD and last_status != "FAILURE":
            print(f"[{datetime.now()}] FAILURE: No heartbeat in last {GRACE_PERIOD} seconds")
            last_status = "FAILURE"
            on_failure()
