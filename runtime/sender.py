#!/usr/bin/env python3
import socket
import time
import subprocess
import sys

REMOTE = '10.0.0.2'    # monitoring server IP
PORT = 9000
TUNNEL = 'wg0'         # tunnel/interface name
INTERVAL_MS = 250      # heartbeat interval in milliseconds

def get_interface_ip(ifname):
    """Get IPv4 address assigned to interface"""
    try:
        # Use 'ip' command to get IP
        result = subprocess.run(
            ['ip', '-4', 'addr', 'show', 'dev', ifname],
            capture_output=True, text=True, check=True
        )
        # Parse inet line
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith('inet '):
                # line looks like 'inet 10.0.0.1/24 brd ...'
                ip = line.split()[1].split('/')[0]
                return ip
    except subprocess.CalledProcessError:
        return None

def main():
    src_ip = get_interface_ip(TUNNEL)
    if not src_ip:
        print(f"Error: Could not find IPv4 address for interface {TUNNEL}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting heartbeat sender to {REMOTE}:{PORT} from {TUNNEL} ({src_ip})")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((src_ip, 0))  # bind to source IP, ephemeral port

        while True:
            message = f"{TUNNEL}:beat".encode()
            sock.sendto(message, (REMOTE, PORT))
            time.sleep(INTERVAL_MS / 1000)
    except KeyboardInterrupt:
        print("\nHeartbeat sender stopped by user.")
    finally:
        sock.close()

if __name__ == '__main__':
    main()
