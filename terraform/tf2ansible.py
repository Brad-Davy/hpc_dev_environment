import subprocess
import json
from pathlib import Path
import re

public_IPs = subprocess.run(
    ["terraform", "output", "-json", "public_ips"],
    capture_output=True,
    text=True,
    check=True,
)

private_IPs = subprocess.run(
    ["terraform", "output", "-json", "private_ips"],
    capture_output=True,
    text=True,
    check=True,
)

private_ips = json.loads(private_IPs.stdout)
public_ips = json.loads(public_IPs.stdout)
guacamole_ip = public_ips["guacamole"]
lines = []

#############################
## Deal with guacamole server
#############################

if "guacamole" in public_ips:
    lines.append("[guacamole]")
    lines.append(
        f"guacamole ansible_host={public_ips['guacamole']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519\n"
    )

#################################
## Deal with portal/login servers
#################################

if "login" in public_ips:
    lines.append("[login]")
    lines.append(
        f"login ansible_host={public_ips['login']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519 \n"
    )

#############################
## Deal with compute server
#############################

if "compute" in public_ips:
    lines.append("[compute]")
    lines.append(
        f"compute ansible_host={public_ips['compute']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519\n"
    )

#############################
## Deal with storage server
#############################

if "storage" in public_ips:
    lines.append("[storage]")
    lines.append(
        f"storage ansible_host={public_ips['storage']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519\n"
    )

#################################################
## Deal with servers which require shared storage
#################################################

lines.append("[shared_storage]")
lines.append(
    f"compute ansible_host={public_ips['compute']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519"
)
lines.append(
    f"login ansible_host={public_ips['login']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519\n"
)

###############################
## Deal with servers with slurm
###############################

lines.append("[slurm]")
lines.append(
    f"compute ansible_host={public_ips['compute']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519"
)
lines.append(
    f"login ansible_host={public_ips['login']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519\n"
)

##############################################
## Deal with servers with shared user software
##############################################

lines.append("[shared_software]")
lines.append(
    f"login ansible_host={public_ips['login']} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_ed25519\n"
)

inventory = "\n".join(lines)
Path("../ansible/hosts.ini").write_text(inventory)

print("✅ Ansible inventory written to hosts.ini")

with open("../ansible/roles/all/files/hosts.txt", "w") as f:

    for key, value in dict(private_ips).items():
        f.write(f"{value} {key} \n")

print("✅ Hosts file created.")

start_marker = "# --- BEGIN ANSIBLE HOSTS ---"
end_marker = "# --- END ANSIBLE HOSTS ---"

# Read the existing /etc/hosts
with open("/etc/hosts", "r") as f:
    hosts_content = f.read()

# Remove old managed block if present
pattern = re.compile(f"{start_marker}.*?{end_marker}", re.DOTALL)
hosts_content = re.sub(pattern, "", hosts_content).strip()

# Build new block
new_block = [start_marker]
for name, ip in public_ips.items():
    new_block.append(f"{ip} {name}")
new_block.append(end_marker)
new_content = "\n".join([hosts_content, "\n".join(new_block)]) + "\n"

# Write new /etc/hosts
with open("/etc/hosts", "w") as f:
    f.write(new_content)

print("✅ /etc/hosts updated successfully.")
