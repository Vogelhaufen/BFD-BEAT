BFD-BEAT

A simple Cisco® BFD-like heartbeat client/server to monitor my WireGuard setup with Starlink®.

Use Case:
My ISP only provides CGNAT. CGNAT is known to b0rk VPNs. I tunnel VPNs through IPv6 to an IPv4 endpoint/VPS, terminating my VPNs. This script performs health checks to enable ultra-fast failover, keeping my ipv4 VPN connections stable and uninterrupted.


# Heartbeat Scripts Setup with systemd

This guide shows how to deploy lightweight UDP heartbeat sender and listener scripts as systemd services on Linux, with logging and failure detection.

---

## 1. Copy Scripts

Place the scripts `sender.sh` and `listener.sh` in `/usr/local/bin/` and make them executable:

```bash
sudo cp sender.sh listener.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/sender.sh /usr/local/bin/listener.sh

2. Create systemd Service Files

Create the following files under /etc/systemd/system/:
heartbeat-sender.service

[Unit]
Description=Heartbeat Sender Service
After=network.target

[Service]
ExecStart=/usr/local/bin/sender.sh
Restart=always
RestartSec=5
User=nobody
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target

heartbeat-listener.service

[Unit]
Description=Heartbeat Listener Service
After=network.target

[Service]
ExecStart=/usr/local/bin/listener.sh
Restart=always
RestartSec=5
User=nobody
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target

3. Setup Logging

Create log files and set permissions for user nobody:

sudo touch /var/log/heartbeat-sender.log /var/log/heartbeat-listener.log
sudo chown nobody:nogroup /var/log/heartbeat-*.log
sudo chmod 644 /var/log/heartbeat-*.log

4. Enable and Start Services

Reload systemd, enable services at boot, and start them now:

sudo systemctl daemon-reload
sudo systemctl enable heartbeat-sender
sudo systemctl enable heartbeat-listener

sudo systemctl start heartbeat-sender
sudo systemctl start heartbeat-listener

5. View Logs

To monitor the log output in real-time:

tail -f /var/log/heartbeat-sender.log
tail -f /var/log/heartbeat-listener.log

Notes

    Adjust REMOTE IP in sender.sh to point to the listener server.

    Modify service User= field if you want to run under a different user.

    The scripts require nc (netcat) and GNU date with millisecond precision.
