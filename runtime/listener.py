import socket
import select
import time
import subprocess
from datetime import datetime

# Config
PORTS = {"wg1": 9000, "wg2": 9001}  # each tunnel listens on own port
CLIENT_SUBNET = "192.168.1.0/24"
TABLES = {"wg1": "wg1", "wg2": "wg2"}
RULE_PRIORITY = 1000
GRACE_PERIOD = 3     # seconds without heartbeat to declare dead
COOLDOWN = 120      # seconds dead before recovery allowed
DETECTION_INTERVAL = 0.05

# Tunnel states: { "wg1": {"last_heartbeat": 0, "state": "healthy", "last_down": None}, ... }
tunnels = {
    name: {"last_heartbeat": 0, "state": "healthy", "last_down": None}
    for name in PORTS
}

active_tunnel = "wg1"

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def run_cmd(cmd):
    subprocess.run(cmd, shell=True, check=True)

def set_ip_rule(tunnel):
    try:
        run_cmd(f"ip rule del from {CLIENT_SUBNET} priority {RULE_PRIORITY}")
    except subprocess.CalledProcessError:
        pass  # rule might not exist yet
    run_cmd(f"ip rule add from {CLIENT_SUBNET} table {TABLES[tunnel]} priority {RULE_PRIORITY}")
    log(f"Routing changed: {CLIENT_SUBNET} -> table {TABLES[tunnel]}")

def create_sockets():
    sockets = {}
    for name, port in PORTS.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind(("", port))
        sockets[name] = sock
    return sockets

def main_loop():
    global active_tunnel
    sockets = create_sockets()
    log(f"Listening for heartbeats on ports {PORTS}")

    set_ip_rule(active_tunnel)

    while True:
        rlist, _, _ = select.select(list(sockets.values()), [], [], DETECTION_INTERVAL)

        now = time.time()

        # Process heartbeats
        for name, sock in sockets.items():
            if sock in rlist:
                try:
                    data, addr = sock.recvfrom(1024)
                    # Heartbeat received
                    tunnels[name]["last_heartbeat"] = now
                    if tunnels[name]["state"] == "dead":
                        # Recovered only after cooldown
                        if tunnels[name]["last_down"] and (now - tunnels[name]["last_down"] > COOLDOWN):
                            tunnels[name]["state"] = "healthy"
                            tunnels[name]["last_down"] = None
                            log(f"Tunnel {name} recovered (heartbeat from {addr})")
                    else:
                        log(f"Tunnel {name} heartbeat OK (from {addr}): {data.decode().strip()}")
                except Exception as e:
                    log(f"Error receiving heartbeat on {name}: {e}")

        # Check tunnel health
        for name, info in tunnels.items():
            diff = now - info["last_heartbeat"]
            if diff > GRACE_PERIOD:
                if info["state"] == "healthy":
                    info["state"] = "dead"
                    info["last_down"] = now
                    log(f"Tunnel {name} DOWN (no heartbeat in last {GRACE_PERIOD}s)")

        # Decide active tunnel
        healthy_tunnels = [t for t, v in tunnels.items() if v["state"] == "healthy"]
        if healthy_tunnels:
            # Prefer current active if healthy, else switch
            if active_tunnel not in healthy_tunnels:
                new_tunnel = healthy_tunnels[0]  # just pick first healthy tunnel
                log(f"Switching active tunnel from {active_tunnel} to {new_tunnel}")
                active_tunnel = new_tunnel
                set_ip_rule(active_tunnel)
        else:
            log("No healthy tunnels available!")

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log("Exiting on user interrupt")
