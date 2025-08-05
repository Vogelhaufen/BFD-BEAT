#!/usr/bin/env python3
import socket
import os
import json
import subprocess
from datetime import datetime

SOCK_PATH = '/tmp/tunnel_status.sock'

# Map tunnel interface to their gateway IP and rule priority
TUNNEL_CONFIG = {
    'wg0': {'gateway': '10.0.0.1', 'priority': 100},
    'wg1': {'gateway': '10.0.1.1', 'priority': 200},
}

# Track current state of tunnels to avoid redundant commands
tunnel_states = {tunnel: None for tunnel in TUNNEL_CONFIG.keys()}

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def run_cmd(cmd):
    """Run shell command, log errors."""
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log(f"Executed: {' '.join(cmd)}")
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {' '.join(cmd)}")
        log(f"stderr: {e.stderr.decode().strip()}")

def add_route_and_rule(tunnel):
    cfg = TUNNEL_CONFIG[tunnel]
    gateway = cfg['gateway']
    priority = cfg['priority']
    iface = tunnel

    log(f"Adding route and rule for {tunnel}")
    # Add default route via gateway on the tunnel interface
    run_cmd(['ip', 'route', 'add', 'default', 'via', gateway, 'dev', iface, 'metric', str(priority)])
    # Add IP rule to prefer this route table priority
    run_cmd(['ip', 'rule', 'add', 'priority', str(priority), 'table', 'main'])

def del_route_and_rule(tunnel):
    cfg = TUNNEL_CONFIG[tunnel]
    gateway = cfg['gateway']
    priority = cfg['priority']
    iface = tunnel

    log(f"Removing route and rule for {tunnel}")
    # Delete default route via gateway on the tunnel interface
    run_cmd(['ip', 'route', 'del', 'default', 'via', gateway, 'dev', iface, 'metric', str(priority)])
    # Delete IP rule
    run_cmd(['ip', 'rule', 'del', 'priority', str(priority), 'table', 'main'])

def apply_tunnel_state(tunnel, state):
    current_state = tunnel_states.get(tunnel)
    if current_state == state:
        # No change
        return
    tunnel_states[tunnel] = state

    if state == 'up':
        add_route_and_rule(tunnel)
        log(f"Tunnel {tunnel} set UP")
    elif state == 'down':
        del_route_and_rule(tunnel)
        log(f"Tunnel {tunnel} set DOWN")

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
                if tunnel in TUNNEL_CONFIG:
                    apply_tunnel_state(tunnel, state)
                else:
                    log(f"Unknown tunnel '{tunnel}' in status message")
            except Exception as e:
                log(f"Failed to process status message: {e}")

    finally:
        server.close()
        if os.path.exists(SOCK_PATH):
            os.remove(SOCK_PATH)

if __name__ == '__main__':
    main()
