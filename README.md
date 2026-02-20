# Defacemon

Monitor static website files: take a baseline (discover and encode resources), then recheck at intervals and report changes. Supports multiple domains when run as a server, with a TCP-based CLI (like redis-cli) to add, refresh, or remove domains while the server is running.

## Requirements

- Python 3.10+
- Chrome or Chromium (for Selenium)
- `requests`, `selenium` (see `requirements.txt`)

## Install

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Docker (production)

Build and run with Docker Compose (Chromium runs headless inside the container):

```bash
docker compose up -d --build
```

- **Control (CLI):** `localhost:9191`
- **Metrics:** `http://localhost:9192/metrics`
- **Baselines:** stored in a named volume (persists across restarts)

Use the CLI from your host:

```bash
python defacemon.py --control-host 127.0.0.1 add https://example.com
python defacemon.py list
```

Or run the CLI inside the same network with `docker compose run --rm defacemon python defacemon.py add https://example.com` (use service name as host if needed). Set `DEFACEMON_HEADLESS=1` in the container so Chrome runs headless (already set in `docker-compose.yml`).

## Quick start

**Terminal 1 – start the server:**

```bash
python defacemon.py serve
# or: python -m defacemon serve
```

**Terminal 2 – add a domain and list:**

```bash
python defacemon.py add https://example.com
python defacemon.py add https://example.com -i 120
python defacemon.py list
python defacemon.py refresh example.com
python defacemon.py remove example.com
```

## Commands

| Command | Description |
|--------|-------------|
| `serve` | Run server in foreground (TCP control + optional Prometheus metrics). |
| `add <url>` | Add a domain to monitor. Creates baseline via browser if missing. `-i SEC` sets check interval (default 60). |
| `list` | List monitored domains (domain, URL, interval, resource count). |
| `refresh <domain>` | Re-discover resources with browser and overwrite baseline for that domain. |
| `remove <domain>` | Stop monitoring a domain. |

**Legacy single-domain mode (no server):**

```bash
python defacemon.py https://example.com
python defacemon.py https://example.com --refresh   # refresh baseline and exit
```

## Server options

- `--control-host` – Bind address for control server (default: `127.0.0.1`). Use `0.0.0.0` to accept remote CLI.
- `--control-port` – Control port (default: `9191`).
- `--metrics-port` – Prometheus HTTP port (default: `9192`). Use `0` to disable.
- `--metrics-host` – Bind address for metrics (default: `127.0.0.1`).
- `--baseline-dir` – Directory for baseline JSON files (default: current dir).

## Metrics (Prometheus)

When the server runs with a metrics port, Prometheus can scrape:

- **URL:** `http://<host>:9192/metrics`
- **`defacemon_domain_changed{domain="..."}`** – `1` if the domain had any change on last check, `0` otherwise.
- **`defacemon_resource_changed{domain="...", resource="..."}`** – `1` if that resource changed (added/removed/content), `0` otherwise.

## Remote CLI

To run the CLI on another machine:

1. Start the server with `--control-host 0.0.0.0` (and open port 9191 in the firewall).
2. Run CLI with `--control-host <server_ip>`:

   ```bash
   python defacemon.py --control-host 192.168.1.10 --control-port 9191 list
   python defacemon.py --control-host 192.168.1.10 add https://example.com
   ```

## Project structure (modular)

```
defacemon/
├── __init__.py
├── __main__.py          # python -m defacemon
├── config.py            # Constants (control host/port)
├── resources.py         # Browser discovery, same-domain filter, download_and_encode
├── baseline.py          # Save/load baselines, change detection, recheck_encoded
├── metrics.py           # Prometheus state and /metrics HTTP server
├── core.py              # MonitorCore (add/refresh/list/remove, per-domain loops)
├── server.py            # TCP control server and cli_send client
├── single.py            # Legacy single-URL monitor loop
└── cli.py               # Argparse and command dispatch
defacemon.py             # Entry point (calls defacemon.cli.main)
```

## Baseline files

All domain baselines are stored in a **`domains-baseline`** subdirectory under `--baseline-dir`. For example with `--baseline-dir .` you get `./domains-baseline/.defacemon_baseline_<domain>.json` (e.g. `example.com` → `domains-baseline/.defacemon_baseline_example_com.json`). Structure:

```json
{
  "main_url": "https://example.com",
  "urls": ["https://example.com/script.js", ...],
  "encoded": { "https://example.com/script.js": "base64...", ... }
}
```

Only resources on the same host as the page URL are monitored; third-party domains (e.g. analytics, CDNs) are ignored.

## License

Use and modify as you like.
