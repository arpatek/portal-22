#!/usr/bin/env python3
"""
portal_22.py - SSH Key & Config Generator
========================================================================================

Generates SSH keys and writes config entries to ~/.ssh/config.local based on
a consistent naming convention. Supports single-key CLI mode and bulk YAML mode.

Author: Juan Garcia (arpatek)
"""
from __future__ import annotations

__version__ = "1.1.0"

# ──[ Imports ]─────────────────────────────────────────────────────────────────────────
import argparse
import getpass
import socket
import subprocess
import sys
from pathlib import Path

# ──[ Third-Party Imports ]─────────────────────────────────────────────────────────────
import yaml

# ──[ Constants ]───────────────────────────────────────────────────────────────────────
YELLOW = "\033[0;33m"
PURPLE = "\033[0;35m"
GREEN  = "\033[0;32m"
BLUE   = "\033[0;34m"
RED    = "\033[0;31m"
SAGE   = "\033[38;2;121;190;154m"
RESET  = "\033[0m"

VALID_TYPES: tuple[str, ...] = ("git", "admin", "deploy", "ci", "tunnel")
VALID_ENC:   tuple[str, ...] = ("ed25519", "rsa", "ecdsa")

PLATFORM_MAP: dict[str, dict[str, str]] = {
    "codeberg": {"alias": "codeberg.org",        "hostname": "codeberg.org"},
    "github":   {"alias": "github.com",          "hostname": "github.com"},
    "gitlab":   {"alias": "gitlab.com",          "hostname": "gitlab.com"},
    "gitea":    {"alias": "gitea",               "hostname": "soulkiller.home.arpa"},
}

SSH_DIR      = Path.home() / ".ssh"
CONFIG_PATH  = SSH_DIR / "config"
CONFIG_LOCAL = SSH_DIR / "config.local"

SEP_OPEN     = "# ──[ Portal-22 ]" + "─" * 63    # 80 chars
SEP_CLOSE    = "# ──[ /Portal-22 ]" + "─" * 62   # 80 chars
INCLUDE_LINE = "Include ~/.ssh/config.local"

# ──[ Output ]──────────────────────────────────────────────────────────────────────────
def BANNER()   -> str: return f"{YELLOW}[{PURPLE}^{YELLOW}]{RESET}"
def PLUS()     -> str: return f"{YELLOW}[{GREEN}+{YELLOW}]{RESET}"
def COMPLETE() -> str: return f"{YELLOW}[{BLUE}*{YELLOW}]{RESET}"
def FAILED()   -> str: return f"{YELLOW}[{RED}!{YELLOW}]{RESET}"
def LAMBDA()   -> str: return f"{YELLOW}[{SAGE}λ{YELLOW}]{RESET}"

# ──[ Key Naming ]──────────────────────────────────────────────────────────────────────
def build_key_name(
    *,
    global_key: bool,
    key_type:   str | None,
    platform:   str | None,
    host:       str | None,
) -> str:
    if global_key:
        return f"{socket.gethostname()}.key"
    parts = [p for p in (key_type, platform or host) if p]
    return ".".join(parts) + ".key"


def build_comment(
    *,
    global_key: bool,
    platform:   str | None,
    host:       str | None,
    user:       str,
) -> str:
    if global_key:
        return f"{socket.gethostname()}@global"
    if platform:
        return f"{socket.gethostname()}@{platform}"
    return f"{user}@{host}"

# ──[ SSH Config ]──────────────────────────────────────────────────────────────────────
def _host_block(alias: str, hostname: str, user: str, key_path: Path, port: int | None = None) -> str:
    lines = [f"Host {alias}\n", f"  HostName {hostname}\n"]
    if port:
        lines.append(f"  Port {port}\n")
    lines += [f"  User {user}\n", f"  IdentityFile {key_path}\n", f"  IdentitiesOnly yes\n"]
    return "".join(lines)


def _portal_section(content: str, *, compact: bool = False) -> str:
    if compact:
        return f"{SEP_OPEN}\n{content}{SEP_CLOSE}\n"
    return f"\n{SEP_OPEN}\n\n{content}\n{SEP_CLOSE}\n"


def check_include(dry_run: bool = False) -> None:
    existing = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else ""
    if INCLUDE_LINE in existing:
        return

    print(f"{PLUS()} Include line not found in {CONFIG_PATH}.")
    try:
        answer = input("  Add it now? [y/N] ").strip().lower()
    except EOFError:
        answer = "n"

    if answer != "y":
        print(f"{PLUS()} Add this manually to the top of {CONFIG_PATH}:")
        print(f"\n{SEP_OPEN}\n{INCLUDE_LINE}\n{SEP_CLOSE}\n")
        return

    block = f"{SEP_OPEN}\n{INCLUDE_LINE}\n{SEP_CLOSE}\n\n"
    if not dry_run:
        CONFIG_PATH.write_text(block + existing, encoding="utf-8")
    print(f"{COMPLETE()} Include line added to {CONFIG_PATH}")


def write_config_local(
    alias:    str,
    hostname: str,
    user:     str,
    key_path: Path,
    dry_run:  bool = False,
    port:     int | None = None,
) -> None:
    block = _portal_section(_host_block(alias, hostname, user, key_path, port))
    if dry_run:
        print(f"{PLUS()} [dry-run] Would append to {CONFIG_LOCAL}:\n{block}")
        return
    SSH_DIR.mkdir(mode=0o700, exist_ok=True)
    with CONFIG_LOCAL.open("a", encoding="utf-8") as f:
        f.write(block)
    print(f"{COMPLETE()} Config entry written to {CONFIG_LOCAL}")


def write_global_key(key_path: Path, dry_run: bool = False) -> None:
    block = _portal_section(f"Host *\n  IdentityFile {key_path}\n")
    if dry_run:
        print(f"{PLUS()} [dry-run] Would append to {CONFIG_PATH}:\n{block}")
        return
    with CONFIG_PATH.open("a", encoding="utf-8") as f:
        f.write(block)
    print(f"{COMPLETE()} Global key entry written to {CONFIG_PATH}")

# ──[ Key Generation ]──────────────────────────────────────────────────────────────────
def generate_key(
    key_path:   Path,
    comment:    str,
    encryption: str,
    passphrase: bool,
    dry_run:    bool = False,
) -> bool:
    if key_path.exists():
        print(f"{COMPLETE()} Key already exists: {key_path}")
        return True
    if dry_run:
        print(f"{PLUS()} [dry-run] Would generate {encryption} key: {key_path}")
        print(f"{PLUS()} [dry-run] Comment: {comment}")
        return True

    passphrase_val = getpass.getpass("  Passphrase (empty for none): ") if passphrase else ""
    result = subprocess.run(
        ["ssh-keygen", "-t", encryption, "-C", comment, "-f", str(key_path), "-N", passphrase_val],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"{FAILED()} ssh-keygen failed: {result.stderr.strip()}")
        return False

    key_path.chmod(0o600)
    print(f"{COMPLETE()} Generated: {key_path}")
    return True

# ──[ Single Mode ]─────────────────────────────────────────────────────────────────────
def run_single(args: argparse.Namespace) -> None:
    user     = args.user or ("git" if args.type == "git" else getpass.getuser())
    key_name = build_key_name(global_key=args.glob, key_type=args.type, platform=args.platform, host=args.host)
    key_path = SSH_DIR / key_name
    comment  = build_comment(global_key=args.glob, platform=args.platform, host=args.host, user=user)

    SSH_DIR.mkdir(mode=0o700, exist_ok=True)
    if not generate_key(key_path, comment, args.encryption, args.passphrase, args.dry_run):
        return

    if args.glob:
        write_global_key(key_path, args.dry_run)
        print(f"{LAMBDA()} Done.")
        return

    if args.platform:
        entry    = PLATFORM_MAP.get(args.platform)
        alias    = entry["alias"]    if entry else args.platform
        hostname = entry["hostname"] if entry else args.platform
    else:
        alias    = args.host
        hostname = args.host

    write_config_local(alias, hostname, user, key_path, args.dry_run)
    check_include(args.dry_run)
    print(f"{LAMBDA()} Done.")

# ──[ Bulk Mode ]───────────────────────────────────────────────────────────────────────
def load_yaml(filepath: str) -> list[dict]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "machines" not in data:
            print(f"{FAILED()} No 'machines' key in {filepath}")
            return []
        return data["machines"]
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"{FAILED()} Could not load YAML: {e}")
        return []


def _validate_entry(m: dict, idx: int) -> str | None:
    is_global = bool(m.get("global"))
    has_host  = bool(m.get("host"))
    platform  = m.get("platform")
    key_type  = m.get("type")

    if is_global and any([has_host, platform, key_type]):
        return f"entry {idx}: global cannot be combined with host/type/platform"
    if not is_global and not has_host and not platform:
        return f"entry {idx}: host required unless global: true or platform is set"
    if platform and not key_type:
        return f"entry {idx}: platform requires type"
    if platform and has_host:
        return f"entry {idx}: platform and host are mutually exclusive"
    if not is_global and not m.get("user"):
        return f"entry {idx}: user required"
    return None


def run_bulk(path: str, dry_run: bool) -> None:
    machines = load_yaml(path)
    if not machines:
        return

    SSH_DIR.mkdir(mode=0o700, exist_ok=True)
    include_checked = False
    host_blocks: list[str] = []

    for idx, m in enumerate(machines, 1):
        err = _validate_entry(m, idx)
        if err:
            print(f"{FAILED()} Skipping — {err}")
            continue

        is_global  = bool(m.get("global"))
        key_type   = m.get("type")
        platform   = m.get("platform")
        host       = m.get("host")
        user       = m.get("user") or ("git" if key_type == "git" else getpass.getuser())
        encryption = m.get("encryption", "ed25519")
        passphrase = bool(m.get("passphrase", False))
        port       = m.get("port") or None

        key_name = build_key_name(global_key=is_global, key_type=key_type, platform=platform, host=host)
        key_path = SSH_DIR / key_name
        comment  = build_comment(global_key=is_global, platform=platform, host=host, user=user)

        print(f"{BANNER()} [{idx}] {key_name}")
        if not generate_key(key_path, comment, encryption, passphrase, dry_run):
            continue

        if is_global:
            write_global_key(key_path, dry_run)
            continue

        if platform:
            entry    = PLATFORM_MAP.get(platform)
            alias    = entry["alias"]    if entry else platform
            hostname = m.get("hostname") or (entry["hostname"] if entry else platform)
        else:
            alias    = host
            hostname = m.get("hostname") or host

        host_blocks.append(_host_block(alias, hostname, user, key_path, port))

        if not include_checked:
            check_include(dry_run)
            include_checked = True

    if host_blocks:
        section = _portal_section("\n".join(host_blocks))
        if dry_run:
            print(f"{PLUS()} [dry-run] Would append to {CONFIG_LOCAL}:\n{section}")
        else:
            with CONFIG_LOCAL.open("a", encoding="utf-8") as f:
                f.write(section)
            print(f"{COMPLETE()} Config entries written to {CONFIG_LOCAL}")

    print(f"{LAMBDA()} Bulk run complete.")

# ──[ CLI ]─────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="portal-22",
        description="SSH key and config generator — arpatek convention.",
    )
    p.add_argument("-g", "--global",     dest="glob",       action="store_true",
                   help="global key using local hostname; writes to ~/.ssh/config")
    p.add_argument("-t", "--type",       dest="type",       choices=VALID_TYPES,
                   help="key type: git, admin, deploy, ci, tunnel")
    p.add_argument("-p", "--platform",   dest="platform",
                   help="platform scope — requires -t, mutually exclusive with -H")
    p.add_argument("-H", "--host",       dest="host",
                   help="destination hostname — mutually exclusive with -p")
    p.add_argument("-u", "--user",       dest="user",
                   help="SSH user (default: 'git' for type=git, else current user)")
    p.add_argument("-e", "--encryption", dest="encryption", choices=VALID_ENC, default="ed25519",
                   help="key encryption type (default: ed25519)")
    p.add_argument("-P", "--passphrase", dest="passphrase", action="store_true",
                   help="prompt for passphrase during key generation")
    p.add_argument("-f", "--yaml",       dest="yaml",       metavar="PATH",
                   help="YAML file for bulk mode")
    p.add_argument("-n", "--dry-run",    dest="dry_run",    action="store_true",
                   help="simulate without writing")
    p.add_argument("--version",          action="version",  version=f"%(prog)s {__version__}")
    return p


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    single_flags = any([args.glob, args.type, args.platform, args.host, args.user, args.passphrase])

    if not args.yaml and not single_flags:
        parser.print_help()
        sys.exit(0)
    if args.yaml and single_flags:
        parser.error("-f cannot be combined with single-key flags")
    if args.glob and any([args.type, args.platform, args.host]):
        parser.error("--global cannot be combined with -t, -p, or -H")
    if args.platform and args.host:
        parser.error("-p and -H are mutually exclusive")
    if args.platform and not args.type:
        parser.error("-p requires -t")
    if not args.glob and not args.yaml and not args.host and not args.platform:
        parser.error("specify -H, -p with -t, --global, or -f")

# ──[ Main ]────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    validate_args(args, parser)

    if args.yaml:
        run_bulk(args.yaml, args.dry_run)
    else:
        run_single(args)


if __name__ == "__main__":
    main()
