---
title: Configuration
nav_order: 4
---

# Configuration

## Server options

All options are passed to `python defacemon.py serve`:

| Flag | Default | Description |
|---|---|---|
| `--control-host` | `127.0.0.1` | Bind address for the TCP control server. Use `0.0.0.0` to accept remote CLI connections. |
| `--control-port` | `9191` | TCP port for the control server. |
| `--metrics-host` | `127.0.0.1` | Bind address for the Prometheus metrics HTTP server. |
| `--metrics-port` | `9192` | HTTP port for `/metrics`. Set to `0` to disable metrics entirely. |
| `--baseline-dir` | `.` (current dir) | Directory where baseline files are stored. In Docker this is set to `/data`. |

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DEFACEMON_HEADLESS` | unset | Set to `1` to run Chrome in headless mode (local installs only). |
| `SELENIUM_REMOTE_URL` | unset | WebDriver endpoint for a remote Chrome node (e.g. `http://selenium:4444/wd/hub`). When set, `DEFACEMON_HEADLESS` has no effect. |

In the Docker Compose setup, `SELENIUM_REMOTE_URL` is pre-configured to point at the bundled `selenium/standalone-chrome` container.

---

## Baseline files

Baselines are stored under `<baseline-dir>/domains-baseline/` as hidden JSON files:

```
<baseline-dir>/
└── domains-baseline/
    ├── .defacemon_baseline_example_com.json
    └── .defacemon_baseline_another_site_org.json
```

Each file has this structure:

```json
{
  "main_url": "https://example.com",
  "urls": ["https://example.com/app.js", "https://example.com/style.css"],
  "encoded": {
    "https://example.com/app.js": "<base64>",
    "https://example.com/style.css": "<base64>"
  }
}
```

`encoded` contains only resources that were successfully downloaded. Resources that failed all download retries are tracked in `urls` but omitted from `encoded` and treated as defaced/removed on the next check.

{: .warning }
Deleting a baseline file causes the next `add` for that domain to re-run full browser discovery. This is equivalent to running `refresh`.

---

## Check interval

The interval is set per-domain with `-i` (seconds) when running `add`:

```bash
python defacemon.py add https://example.com -i 300   # check every 5 minutes
```

There is no global default you can change in config — it defaults to `60` seconds if not specified.
