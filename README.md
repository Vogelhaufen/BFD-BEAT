# BFD-BEAT

A simple Cisco® BFD-like heartbeat client/server to monitor my WireGuard setup with Starlink®.

Use Case:
My ISP only provides CGNAT. CGNAT is known to b0rk VPNs. I tunnel VPNs through IPv6 to an IPv4 endpoint/VPS, terminating my VPNs. This script performs health checks to enable ultra-fast failover, keeping my ipv4 VPN connections stable and uninterrupted.

Listener is split into 2 files for security reasons. NET SOCKET<>executing sys commands
