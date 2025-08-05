#!/usr/bin/env python3
import socket
import time
import json
import select
from datetime import datetime

UDP_PORT = 9000
GRACE_PERIOD = 0.05  # 50 ms detection time
COOLDOWN = 120       # 2 minutes cooldown for tunnel recovery
SOCK_PATH = '/tmp/tunnel_status.sock'

tunnels = {
    'wg0': {'last_heartbeat': 0, 'state': 'down', 'cooldown_until': 0},
    'wg1': {'last_heartbeat': 0, 'state': 'down', 'cooldown_until': 0},
}

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def send_status(sock, tunnel, state):
    status = {'tunnel': tunnel, 'state': state, 'timestamp': time.time()}
    try:
        sock.sendto(json.dumps(status).encode(), SOCK_PATH)
    except Exception as e:
        log(f"Failed to send status: {e}")

def main():
    # UDP socket for heartbeats
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('', UDP_PORT))
    udp_sock.setblocking(False)

    # Unix datagram socket for sending status updates
    unix_sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    log(f"Listening for heartbeats on UDP port {UDP_PORT}")

    while True:
        now = time.time()

        # Wait up to 50ms for heartbeat data
        rlist, _, _ = select.select([udp_sock], [], [], GRACE_PERIOD)

        if rlist:
            data, addr = udp_sock.recvfrom(1024)
            msg = data.decode().strip()
            # Expecting msg like "wg0:beat" or "wg1:beat"
            if ':' in msg:
                tunnel, beat = msg.split(':', 1)
                if tunnel in tunnels and beat == "beat":
                    tunnels[tunnel]['last_heartbeat'] = now
                    # If tunnel was down or cooldown expired, mark up
                    if tunnels[tunnel]['state'] != 'up' and now > tunnels[tunnel]['cooldown_until']:
                        tunnels[tunnel]['state'] = 'up'
                        send_status(unix_sock, tunnel, 'up')
                        log(f"Tunnel {tunnel} is UP (heartbeat received)")
        else:
            # No heartbeat received, check if tunnel should be down
            for tunnel, info in tunnels.items():
                diff = now - info['last_heartbeat']
                if info['state'] == 'up' and diff > GRACE_PERIOD:
                    # Mark tunnel down, start cooldown
                    info['state'] = 'down'
                    info['cooldown_until'] = now + COOLDOWN
                    send_status(unix_sock, tunnel, 'down')
                    log(f"Tunnel {tunnel} is DOWN (no heartbeat for {diff:.3f}s)")

        time.sleep(0.01)  # small sleep to prevent CPU hogging

if __name__ == '__main__':
    main()
