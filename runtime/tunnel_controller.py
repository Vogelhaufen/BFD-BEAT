#!/usr/bin/env python3
import socket
import os
import json
import subprocess
from datetime import datetime

SOCK_PATH = '/tmp/tunnel_status.sock'

# Tunnel info - adjust IP gateways and routing table numbers as needed
TUNNELS = {
    'wg0': {'table': '100', 'gateway': '10.0.0.1', 'priority': 100},
    'wg1': {'table': '101', 'gateway': '10.1.0.1', 'priority': 200},
}

def log(msg):
    print(f"[{datetime.now()}] {msg}")

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log(f"Executed: {cmd}")
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {cmd} ; stderr: {e.stderr.decode().strip()}")

# Track current tunnel states globally to make decisions
current_states = {t: 'down' for t in TUNNELS}

def setup_ip_rules():
    # Add ip rules and route tables once, ignore if already present
    for tunnel, info in TUNNELS.items():
        # Add route table default route
        run_cmd(f"ip route add default via {info['gateway']} dev {tunnel} table {info['table']} || true")
        # Add ip rule to lookup table based on fwmark
        run_cmd(f"ip rule add fwmark {info['priority']} lookup {info['table']} || true")

def flush_ip_rules():
    # Remove all rules and routes added (for cleanup, optional)
    for tunnel, info in TUNNELS.items():
        run_cmd(f"ip route del default via {info['gateway']} dev {tunnel} table {info['table']} || true")
        run_cmd(f"_
