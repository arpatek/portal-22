# portal-22

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

SSH key and config generator. Follows the arpatek naming convention. Supports
single-key CLI mode and bulk YAML mode.

---

## Key naming

```
{hostname}.key                      # bare host
{type}.{hostname}.key               # typed
{type}.{platform}.key               # platform-scoped (git keys)
{local-hostname}.key                # global (--global)
```

Keys are written to `~/.ssh/`. Host entries go to `~/.ssh/config.local`.
Global keys are added to `Host *` in `~/.ssh/config`.

---

## Usage

### Single key

```bash
# Global key — local hostname, added to Host * in ~/.ssh/config
./portal_22.py -g

# Git platform key
./portal_22.py -t git -p codeberg

# Admin key to a homelab host
./portal_22.py -t admin -H mikoshi

# Bare host key
./portal_22.py -H gonk-1

# With options
./portal_22.py -t admin -H mikoshi -e rsa -P   # rsa, prompt for passphrase
./portal_22.py -t git -p github -n              # dry-run
```

### Bulk mode

```bash
./portal_22.py -f /path/to/machines.yml
./portal_22.py -f /path/to/machines.yml --dry-run
```

---

## Flags

| Flag | Short | Description |
|---|---|---|
| `--global` | `-g` | Global key using local hostname |
| `--type` | `-t` | `git` `admin` `deploy` `ci` `tunnel` |
| `--platform` | `-p` | Platform scope — requires `-t`, exclusive with `-H` |
| `--host` | `-H` | Destination hostname — exclusive with `-p` |
| `--user` | `-u` | SSH user (default: `git` for type=git, else current user) |
| `--encryption` | `-e` | `ed25519` `rsa` `ecdsa` (default: `ed25519`) |
| `--passphrase` | `-P` | Prompt for passphrase |
| `--yaml` | `-f` | YAML file for bulk mode |
| `--dry-run` | `-n` | Simulate without writing |

---

## YAML schema

```yaml
machines:
  - global: true                    # global key — local hostname
    encryption: ed25519

  - type: git                       # platform key
    platform: codeberg
    user: git

  - host: mikoshi                   # host key with FQDN override
    hostname: mikoshi.home.arpa
    user: arpatek
    type: admin

  - host: gonk-1                    # bare host key
    hostname: gonk-1.home.arpa
    user: sysadmin
```

---

## Platform map

| Platform | Host alias | HostName |
|---|---|---|
| `codeberg` | `codeberg.org` | `codeberg.org` |
| `github` | `github.com` | `github.com` |
| `gitlab` | `gitlab.com` | `gitlab.com` |
| `gitea` | `gitea` | `soulkiller.home.arpa` |

---

## Requirements

- Python 3.9+
- `PyYAML` — `pip install pyyaml`
