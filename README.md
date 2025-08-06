# BFD-BEAT

A simple Cisco® BFD-like heartbeat client/server to monitor my WireGuard setup with Starlink®.

Use Case:
My ISP only provides CGNAT. CGNAT is known to b0rk VPNs. I tunnel VPNs through IPv6 to an IPv4 endpoint/VPS, terminating my VPNs. This script performs health checks to enable ultra-fast failover, keeping my ipv4 VPN connections stable and uninterrupted.

Listener is split into 2 files for security reasons:

heartbeat_sender.py: A simple UDP heartbeat sender, configurable host/port/interval, clean handling of keyboard interrupt, and error handling on send.

tunnel_controller.py: A whitelist approach to allowed commands to avoid executing arbitrary commands (critical for root-level operations). Uses subprocess.run() with check=True for proper error detection and no shell injection risk.

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/301d7e2c-10d2-4fd1-8420-33bc35c0b4e8" />
