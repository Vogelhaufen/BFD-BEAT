# BFD-BEAT

A simple Cisco® BFD-like heartbeat client/server to monitor my WireGuard setup with Starlink®.

Use Case:
My ISP only provides CGNAT. CGNAT is known to b0rk VPNs. I tunnel VPNs through IPv6 to an IPv4 endpoint/VPS, terminating my VPNs. This script performs health checks to enable ultra-fast failover, keeping my ipv4 VPN connections stable and uninterrupted.

Listener is split into 2 files for security reasons. NET SOCKET<>executing sys commands


flowchart TD
    A[Your Local Network<br>IPv4 private LAN<br>192.168.x.x/24]
    B[WireGuard Tunnel<br>IPv4 encapsulated inside IPv6<br>over native IPv6 /56]
    C[VPS on Internet<br>Native IPv6 /64 & Public IPv4]
    D[Public IPv4 Internet]

    A -->|Encapsulated IPv4 inside IPv6| B
    B --> C
    C --> D

    subgraph ISP
        direction TB
        CGNAT_IPv4[CGNAT IPv4 (no native IPv4)]
        Native_IPv6[Native IPv6 /56]
    end

    CGNAT_IPv4 -->|IPv4 blocked| A
    Native_IPv6 -->|IPv6 for tunnel| B

    classDef isp fill:#f9f,stroke:#333,stroke-width:2px;
    class ISP isp
