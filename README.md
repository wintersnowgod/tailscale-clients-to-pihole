# Tailscale to PiHole

## Automatic DNS host-ip syncronization

### What it does

1. Pulls the current Tailscale status list
2. Pulls the current PiHole dns.hosts list
3. Updates Tailscale device hostnames in PiHole if the Tailscale IP is unchanged
4. Updates Tailscale device IPs in Pihole if the Tailscale hostname is unchanged
5. Adds new Tailcale device IP-hostnames to PiHole

#### TODO

Build a listener for changes to Tailscale client hostname/IP.

> Or simply https://discourse.pi-hole.net/t/how-to-show-tailscale-hostnames-in-pihole/80603
