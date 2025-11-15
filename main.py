import re, subprocess


def run_command(command: list[str]) -> str:
    # Returns console output of the given shell command.
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output_variable = result.stdout
        error_variable = result.stderr
        # print(f"Captured output:\n{peers}")
        if error_variable:
            print(f"\nCaptured error:\n{error_variable}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error code {e.returncode}")
        print(f"Error output:\n{e.stderr}")
    except FileNotFoundError:
        print(f'Error: Command "{command[0]}" not found.')
    return output_variable


if __name__ == "__main__":
    # Get Tailscale peer/client list.
    command = ["tailscale", "status"]
    peers = run_command(command)
    pattern = r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\S+)"
    matches = re.findall(pattern, peers, re.MULTILINE)
    matches_ts = [f"{ip} {hostname}-ts" for ip, hostname in matches]
    tailscale_dns_records = '", "'.join(matches_ts)
    tailscale_dns_records = tailscale_dns_records.replace("'", '"')
    tailscale_dns_records = f'["{tailscale_dns_records}"]'
    print(tailscale_dns_records)

    # Get PiHole dns.hosts list.
    command = ["sudo", "pihole-FTL", "--config", "dns.hosts"]
    hosts = run_command(command)
    print(hosts)

    # TODO Update hostnames in PiHole if found in Tailscale.

    # TODO Update IPs in PiHole if found in Tailscale.

    # TODO store updated ip-hostname list as a variable called 'hosts'.

    # Update Pihole dns.hosts and reload DNS.
    command = ["sudo", "pihole-FTL", "--config", "dns.hosts", "'hosts'"]
