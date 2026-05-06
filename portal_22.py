#!/usr/bin/env python3
"""
portal_22.py - SSH Key & Config Generator
========================================================================================

Portal-22 automates the creation of SSH keys and appends SSH config blocks based on
machine definitions in a YAML file. Supports dry-run previews for safety before
execution.

Author: Juan Garcia (arpatek)

Dependencies:
-------------
- Python 3.9+
- PyYAML (install via pip)

Sample Usage:
-------------
$ ./portal_22.py data.yml
$ ./portal_22.py data.yml --dry-run
"""

# ──[ Standard Library Imports ]────────────────────────────────────────────────────────
import os
import time
import argparse
import subprocess
from typing import Optional
from io import TextIOWrapper

# ──[ Third-Party Imports ]─────────────────────────────────────────────────────────────
import yaml


# ──[ Constants ]───────────────────────────────────────────────────────────────────────
HEADER_BANNER = """
┌──────────────────────────────────────────────────────────────┐
│                         Portal-22                            │
│         SSH Key & Config Generator from YAML Data            │
│                                                              │
│      Author: Juan Garcia (arpatek)                           │
│      Description: Automates SSH key gen and config insertion │
└──────────────────────────────────────────────────────────────┘
"""


# ──[ YAML Loader ]─────────────────────────────────────────────────────────────────────
def load_yaml(filepath: str) -> list[dict[str, str | None]]:
    """Load the machines list from a YAML file.

    Args:
        filepath (str): Path to the YAML file containing machine definitions.

    Returns:
        list[dict]: List of machine dictionaries, or an empty list on error.
    """
    try:
        with open(filepath, "r", encoding="utf8") as file:
            data = yaml.safe_load(file)
            if not data or "machines" not in data:
                print("[!] No 'machines' key found in YAML file.")
                return []
            return data["machines"]
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"[!] Error loading YAML file: {e}")
        return []


# ──[ Machine Processor ]───────────────────────────────────────────────────────────────
def process_machine(
    machine: dict[str, str | None],
    ssh_conf: Optional[TextIOWrapper] = None,
    dry_run: bool = False,
) -> None:
    """Generate an SSH key and append a config block for a single machine entry.

    If dry_run is True, only prints the actions that would be taken without
    making any changes to the filesystem or SSH config.

    Args:
        machine (dict): Machine definition with keys: hostname, ip, scope, user.
        ssh_conf (TextIOWrapper | None): Open file handle to ~/.ssh/config for
            appending. Ignored in dry-run mode.
        dry_run (bool): When True, simulate actions without writing. Default False.
    """
    hostname: Optional[str] = machine.get("hostname")
    ip:       Optional[str] = machine.get("ip")
    scope:    Optional[str] = machine.get("scope")
    user:     Optional[str] = machine.get("user")

    if not hostname:
        print("No Hostname available for machine entry, skipping...")
        return
    if not ip:
        print(f"No IP available for {hostname}, skipping...")
        return
    if not scope:
        print(f"No Scope available for {hostname}, skipping...")
        return
    if not user:
        print(f"No User available for {hostname}, skipping...")
        return

    keys_dir          = os.path.expanduser("~/.ssh/keys")
    os.makedirs(keys_dir, exist_ok=True)
    key_path          = os.path.join(keys_dir, f"key.{scope}.{hostname}.{user}")
    key_path_expanded = os.path.expanduser(key_path)

    ssh_entry = (
        f"Host {hostname.lower()}.{user}\n"
        f"    HostName {ip}\n"
        f"    User {user}\n"
        f"    IdentityFile {key_path_expanded}\n"
        "\n"
    )

    if dry_run:
        if os.path.exists(key_path_expanded):
            print(f"[SKIP] Key already exists: {key_path_expanded}")
        else:
            print(f"[DRY-RUN] Would generate key: {key_path_expanded}")
        print(f"[DRY-RUN] Would append to SSH config:\n{ssh_entry}")
    else:
        if os.path.exists(key_path_expanded):
            print(f"[SKIP] Key already exists: {key_path_expanded}")
        else:
            cmd = [
                "ssh-keygen",
                "-t", "ed25519",
                "-C", f"{scope}.{hostname}.{user}",
                "-f", key_path_expanded,
                "-N", "",
            ]
            subprocess.call(cmd)
            print(f"Generated key for {hostname} at {key_path_expanded}")

        if ssh_conf:
            ssh_conf.write(ssh_entry)


# ──[ Main ]────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """Parse CLI arguments, load machine definitions, and process each machine."""
    print(HEADER_BANNER)
    time.sleep(2)

    parser = argparse.ArgumentParser(
        description=(
            "Portal-22: Append SSH config blocks and "
            "generate keys from a YAML file"
        )
    )
    parser.add_argument(
        "yaml",
        nargs="?",
        default="data.yml",
        help="Path to the YAML file with machine definitions (default: data.yml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate key and config generation without making changes",
    )
    args = parser.parse_args()

    machines          = load_yaml(args.yaml)
    ssh_config_path   = os.path.expanduser("~/.ssh/config")
    keys_dir          = os.path.expanduser("~/.ssh/keys")
    os.makedirs(keys_dir, exist_ok=True)

    portal_header     = "#### PORTAL-22 GENERATED KEYS ####\n"
    existing_content  = ""
    if os.path.exists(ssh_config_path):
        with open(ssh_config_path, "r", encoding="utf8") as f:
            existing_content = f.read()

    if not args.dry_run:
        with open(ssh_config_path, "a+", encoding="utf8") as ssh_conf:
            if portal_header.strip() not in existing_content:
                ssh_conf.write(portal_header)
            for machine in machines:
                process_machine(machine, ssh_conf=ssh_conf, dry_run=False)
        print(f"SSH config updated at {ssh_config_path}")
    else:
        for machine in machines:
            process_machine(machine, dry_run=True)


# ──[ Entry Point ]─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
