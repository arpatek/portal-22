# portal-22

```
┌──────────────────────────────────────────────────────────────┐
│                         Portal-22                            │
│         SSH Key & Config Generator from YAML Data            │
│                                                              │
│      Author: Juan Garcia (arpatek)                           │
│      Description: Automates SSH key gen and config insertion │
└──────────────────────────────────────────────────────────────┘
```

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

**portal-22** automates the creation of SSH keys and appends SSH config blocks based
on machine definitions in a YAML file. Supports dry-run previews before making any
changes.

---

### Features

`[YAML-Driven]` Define all machines in a single `data.yml` — hostname, IP, user, scope.  
`[ed25519 Keys]` Generates modern ed25519 keys with structured naming: `key.<scope>.<host>.<user>`.  
`[Dry-Run Mode]` Preview keys and config blocks that would be written before committing.  
`[Idempotent]` Skips key generation if a key already exists at the target path.  

---

### Usage

```bash
./portal_22.py data.yml
./portal_22.py data.yml --dry-run
```

---

### YAML Format

```yaml
machines:
  - hostname: dev-01
    ip: 10.0.0.10
    user: admin
    scope: lab

  - hostname: prod-web
    ip: 10.0.0.20
    user: deploy
    scope: prod
```

---

### Output

Keys are written to `~/.ssh/keys/key.<scope>.<hostname>.<user>` and config blocks
are appended to `~/.ssh/config`:

```
Host dev-01.admin
    HostName 10.0.0.10
    User admin
    IdentityFile ~/.ssh/keys/key.lab.dev-01.admin
```

---

### Requirements

- Python 3.9+
- `PyYAML` (`pip install pyyaml`)
