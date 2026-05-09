---
title: Installation
nav_order: 2
---

# Installation

## Requirements

- Python 3.10+
- Chrome or Chromium (only needed for local/non-Docker mode)

---

## Option 1 — Docker (recommended)

Docker Compose bundles defacemon and a headless Selenium Chrome node together. No local Python or Chrome install required.

```bash
git clone https://github.com/mohammdali-davarzani/defacemon.git
cd defacemon
docker compose up -d --build
```

The server starts automatically. Use the CLI from your host machine to control it:

```bash
python defacemon.py --control-host 127.0.0.1 add https://example.com
python defacemon.py list
```

Or run the CLI inside the container network:

```bash
docker compose run --rm defacemon python defacemon.py add https://example.com
```

{: .note }
Baselines are stored in a named Docker volume (`defacemon-data`) and survive container restarts.

---

## Option 2 — Local (virtualenv)

```bash
git clone https://github.com/mohammdali-davarzani/defacemon.git
cd defacemon
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

You need Chrome or Chromium installed on your system. For headless operation, set the environment variable:

```bash
export DEFACEMON_HEADLESS=1
```

---

## Verifying the install

```bash
python defacemon.py --help
```

You should see the list of available subcommands: `serve`, `add`, `list`, `refresh`, `remove`.
