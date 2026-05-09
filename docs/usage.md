---
title: Usage
nav_order: 3
has_children: true
---

# Usage

Defacemon has two modes:

| Mode | When to use |
|---|---|
| **Server mode** | Monitor multiple domains continuously. This is the normal production mode. |
| **Legacy mode** | Quick single-domain monitoring from one command (no server needed). |

---

## Server mode

Server mode runs a long-lived process with two listeners:

- **TCP control server** (default `:9191`) — accepts `add`, `list`, `refresh`, `remove` commands from the CLI
- **HTTP metrics server** (default `:9192`) — Prometheus `/metrics` endpoint

```bash
python defacemon.py serve
```

With options:

```bash
python defacemon.py serve \
  --control-host 0.0.0.0 \
  --control-port 9191 \
  --metrics-host 0.0.0.0 \
  --metrics-port 9192 \
  --baseline-dir /data
```

Once the server is running, use the CLI commands below from another terminal (or another machine).

---

## CLI commands

### add

Adds a domain to monitor. The server opens the URL in a browser to discover and baseline all resources — this takes 30–60 seconds. Subsequent rechecks use plain HTTP (much faster).

```bash
python defacemon.py add https://example.com
python defacemon.py add https://example.com -i 120   # check every 120 seconds
```

The default interval is **60 seconds**.

---

### list

Lists all currently monitored domains.

```bash
python defacemon.py list
```

Output columns: `domain`, `main_url`, `interval`, `resource count`.

---

### refresh

Re-runs browser discovery and overwrites the baseline for a domain. Use this after a legitimate site update to reset the known-good state.

```bash
python defacemon.py refresh example.com
```

---

### remove

Stops monitoring a domain and removes it from metrics.

```bash
python defacemon.py remove example.com
```

---

## Remote CLI

To control a server running on another machine, pass `--control-host`:

```bash
python defacemon.py --control-host 192.168.1.10 --control-port 9191 list
python defacemon.py --control-host 192.168.1.10 add https://example.com
```

{: .note }
Start the server with `--control-host 0.0.0.0` to accept connections from other machines, and open port `9191` in your firewall.

---

## Legacy mode (single domain)

Monitors one URL in a loop without running a separate server process:

```bash
python defacemon.py https://example.com
python defacemon.py https://example.com -i 120
python defacemon.py https://example.com --refresh   # refresh baseline only, then exit
```

The baseline is stored as `.defacemon_baseline.json` in the current directory.
