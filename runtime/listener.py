#!/usr/bin/env python3
import socket
import select
import time
import subprocess
from datetime import datetime

# Config
TUNNELS = {
    'wg0': 9000,
    'wg1': 9001,
}
DEAD_TIMEOUT = 120     # seconds tunnel stays DOWN after failure
DETECTION_THRESHOLD = 0.05  # 50 ms max allowed heartbeat interval

# State variables
state = {tunnel: 'UP' for tunnel in TUNNELS}
last_heartbeat = {tunnel: time.time() for tunnel in TUNNELS}
dead_since = {tunnel: None for tunnel in TUNNELS}

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def bring_down(tunnel):
    log(f"Bringing DOWN tunnel {tunnel}")
    subprocess.run(['wg-quick', 'down', tunnel], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    state[tunnel] = 'DOWN'
    dead_since[tunnel] = time.time()

def bring_up(tunnel):
    log(f"Bringing UP tunnel {tunnel}")
    subprocess.run(['wg-quick', 'up', tunnel], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    state[tunnel] = 'UP'
    dead_since[tunnel] = None
    last_heartbeat[tunnel] = time.time()  # Reset heartbeat time on up

def check_heartbeat(tunnel):
    now = time.time()
    diff = now - last_heartbeat[tunnel]
    return diff <= DETECTION_THRESHOLD

def setup_sockets():
    sockets = {}
    for tunnel, port in TUNNELS.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        sockets[sock] = tunnel
        log(f"Listening for heartbeats on UDP port {port} for tunnel {tunnel}")
    return sockets

def main_loop():
    sockets = setup_sockets()
    while True:
        rlist, _, _ = select.select(list(sockets.keys()), [], [], 0.01)  # 10 ms timeout

        now = time.time()

        # Handle incoming heartbeats
        for sock in rlist:
            try:
                data, addr = sock.recvfrom(1024)
                tunnel = sockets[sock]
                last_heartbeat[tunnel] = now
                log(f"Heartbeat OK from {addr} on tunnel {tunnel}: {data.decode(errors='ignore').strip()}")
            except Exception as e:
                log(f"Error receiving data: {e}")

        # Check tunnel states
        for tunnel in TUNNELS:
            alive = check_heartbeat(tunnel)

            if state[tunnel] == 'UP':
                if not alive:
                    log(f"Tunnel {tunnel} lost heartbeat, bringing down")
                    bring_down(tunnel)

            elif state[tunnel] == 'DOWN':
                if dead_since[tunnel] and (now - dead_since[tunnel]) >= DEAD_TIMEOUT:
                    if alive:
                        log(f"Tunnel {tunnel} heartbeat back after cooldown, bringing up")
                        bring_up(tunnel)
                    else:
                        log(f"Tunnel {tunnel} still dead after cooldown")

        time.sleep(0.01)  # Small sleep to avoid busy loop

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        log("Stopping listener")
