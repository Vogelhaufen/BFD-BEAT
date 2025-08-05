import socket
import select
import time
from datetime import datetime

TUNNELS = {
    'wg0': 9000,
    'wg1': 9001,
}
DEAD_TIMEOUT = 12     # seconds tunnel stays DOWN after failure
DETECTION_THRESHOLD = 1.00  # 1s max allowed heartbeat interval
LOG_STILL_DEAD_INTERVAL = 10  # seconds between repeated "still dead" logs

state = {tunnel: 'UP' for tunnel in TUNNELS}
last_heartbeat = {tunnel: time.time() for tunnel in TUNNELS}
dead_since = {tunnel: None for tunnel in TUNNELS}
last_still_dead_log = {tunnel: 0 for tunnel in TUNNELS}

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def bring_down(tunnel):
    log(f"DEBUG: Tunnel {tunnel} should be brought DOWN (not actually doing it)")

def bring_up(tunnel):
    log(f"DEBUG: Tunnel {tunnel} should be brought UP (not actually doing it)")

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

        for sock in rlist:
            try:
                data, addr = sock.recvfrom(1024)
                tunnel = sockets[sock]
                last_heartbeat[tunnel] = now
                log(f"Heartbeat OK from {addr} on tunnel {tunnel}: {data.decode(errors='ignore').strip()}")
            except Exception as e:
                log(f"Error receiving data: {e}")

        for tunnel in TUNNELS:
            alive = check_heartbeat(tunnel)

            if state[tunnel] == 'UP':
                if not alive:
                    log(f"Tunnel {tunnel} lost heartbeat, should be brought down")
                    bring_down(tunnel)
                    state[tunnel] = 'DOWN'
                    dead_since[tunnel] = now
                    last_still_dead_log[tunnel] = now

            elif state[tunnel] == 'DOWN':
                if dead_since[tunnel] and (now - dead_since[tunnel]) >= DEAD_TIMEOUT:
                    if alive:
                        log(f"Tunnel {tunnel} heartbeat back after cooldown, should be brought up")
                        bring_up(tunnel)
                        state[tunnel] = 'UP'
                        dead_since[tunnel] = None
                        last_still_dead_log[tunnel] = 0
                        last_heartbeat[tunnel] = now
                    else:
                        # Log "still dead" message at most every LOG_STILL_DEAD_INTERVAL seconds
                        if now - last_still_dead_log[tunnel] >= LOG_STILL_DEAD_INTERVAL:
                            log(f"Tunnel {tunnel} still dead after cooldown")
                            last_still_dead_log[tunnel] = now

        time.sleep(0.01)

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        log("Stopping listener")
