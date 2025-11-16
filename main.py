import re
import subprocess


# TODO Connect to Tailscale API / Webhook to listen for host/IP changes


def run_command(command: list[str]) -> str:
    # Returns console output of the given shell command.
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        output_variable = result.stdout
        error_variable = result.stderr
        if error_variable:
            print(f"\nCaptured error:\n{error_variable}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error code {e.returncode}")
        print(f"Error output:\n{e.stderr}")
    except FileNotFoundError:
        print(f'Error: Command "{command[0]}" not found.')
    return output_variable


def main():
    # Get Tailscale peer/client list.
    command = ["tailscale", "status"]
    peers = run_command(command)
    pattern = r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\S+)"
    matches = re.findall(pattern, peers, re.MULTILINE)
    tailscale_dns_records = [f"{ip} {hostname}-ts" for ip, hostname in matches]
    print("Tailscale records:")
    print(tailscale_dns_records)

    # Get PiHole dns.hosts list.
    command = ["docker", "exec", "pihole", "pihole-FTL", "--config", "dns.hosts"]
    pihole_output = run_command(command)
    print("\nRaw PiHole output:")
    print(pihole_output)

    pihole_output_cleaned = pihole_output.strip()
    if pihole_output_cleaned.startswith("["):
        pihole_output_cleaned = pihole_output_cleaned[1:]
    if pihole_output_cleaned.endswith("]"):
        pihole_output_cleaned = pihole_output_cleaned[:-1]

    # Split by comma to get individual entries
    pihole_hosts = [
        entry.strip() for entry in pihole_output_cleaned.split(",") if entry.strip()
    ]

    print("\nParsed PiHole hosts:")
    for host in pihole_hosts:
        print(f"  {host}")

    # Parse lists.
    ts_ip_to_hostname = {}
    ts_hostname_to_ip = {}

    for entry in tailscale_dns_records:
        parts = entry.split()
        if len(parts) == 2:
            ip, hostname = parts
            ts_ip_to_hostname[ip] = hostname
            ts_hostname_to_ip[hostname] = ip

    ph_entries = []
    ph_ips = set()
    ph_hostnames = set()

    for entry in pihole_hosts:
        parts = entry.split()
        if len(parts) == 2:
            ip, hostname = parts
            ph_entries.append([ip, hostname])
            ph_ips.add(ip)
            ph_hostnames.add(hostname)
        else:
            print(f"Warning: Skipping malformed entry: {entry}")

    print(f"\nParsed {len(ph_entries)} PiHole entries")

    # Step 1: Update hostnames in PiHole if the IP is found in Tailscale.
    for entry in ph_entries:
        ip, hostname = entry
        if ip in ts_ip_to_hostname:
            print(
                f"Updating hostname for IP {ip}: {hostname} -> {ts_ip_to_hostname[ip]}"
            )
            entry[1] = ts_ip_to_hostname[ip]

    # Step 2: Update IPs in PiHole if the hostname is found in Tailscale.
    for entry in ph_entries:
        ip, hostname = entry
        if hostname in ts_hostname_to_ip:
            new_ip = ts_hostname_to_ip[hostname]
            if new_ip != ip:
                print(f"Updating IP for hostname {hostname}: {ip} -> {new_ip}")
                entry[0] = new_ip

    # Step 3: Add Tailscale entries if not already in PiHole.
    ph_ips_updated = {entry[0] for entry in ph_entries}
    ph_hostnames_updated = {entry[1] for entry in ph_entries}

    for entry in tailscale_dns_records:
        parts = entry.split()
        if len(parts) == 2:
            ip, hostname = parts
            if ip not in ph_ips_updated and hostname not in ph_hostnames_updated:
                print(f"Adding new entry from Tailscale: {ip} {hostname}")
                ph_entries.append([ip, hostname])

    # Store updated ip-hostname list as a variable called 'hosts'.
    hosts = [f"{ip} {hostname}" for ip, hostname in ph_entries]
    hosts = '", "'.join(hosts)
    hosts = f'"{hosts}"'
    hosts = f"'[{hosts}]'"

    print("\n" + "=" * 60)
    print("Final hosts list:")
    print(hosts)

    # Update PiHole dns.hosts and restart DNS.
    # subprocess.run didn't seem to like variables, so use .check_output
    # https://python-forum.io/thread-36920-post-155973.html#pid155973
    subprocess.check_output(
        "sudo pihole-FTL --config dns.hosts {}".format(hosts), shell=True
    )
    command = ["docker", "exec", "pihole", "pihole", "reloaddns"]
    run_command(command)

    print("\n" + "=" * 60)
    print("The PiHole dns.hosts list is now:")
    command = ["docker", "exec", "pihole", "pihole-FTL", "--config", "dns.hosts"]
    print(run_command(command))


if __name__ == "__main__":
    main()
