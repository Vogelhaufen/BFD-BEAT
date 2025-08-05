#!/usr/bin/env python3
import socket
import os
import json
from datetime import datetime

SOCK_PATH = '/tmp/tunnel_status.sock'

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def apply_tunnel_state(tunnel, state):
    # Placeholder for applying ip rule/route changes as root
    if state == 'up':
        log(f"Controller: Tunnel {tunnel} is UP. (Apply routing rules here)")
    else:
        log(f"Controller: Tunnel {tunnel} is DOWN. (Apply routing rules here)")

def main():
    if os.path.exists(SOCK_PATH):
        os.remove(SOCK_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(SOCK_PATH)

    log("Controller started, waiting for tunnel status updates")

    try:
        while True:
            data, _ = server.recvfrom(1024)
            try:
                status = json.loads(data.decode())
                tunnel = status['tunnel']
                state = status['state']
                timestamp = status['timestamp']
                log(f"Received status: Tunnel {tunnel} is {state}")
                apply_tunnel_state(tunnel, state)
            except Exception as e:
                log(f"Failed to process status message: {e}")

    finally:
        server.close()
        if os.path.exists(SOCK_PATH):
            os.remove(SOCK_PATH)

if __name__ == '__main__':
    main()
