---
title: Home
layout: home
nav_order: 1
---

# Defacemon

**Defacemon** monitors static website files for defacement. It discovers all resources on a page using a real browser, stores them as a baseline, then periodically re-fetches them and alerts you to anything that was added, removed, or modified.

---

## How it works

1. **Discover** — a headless Chrome browser loads your page and records every same-domain resource (JS, CSS, images, fonts, etc.) via Chrome DevTools Protocol.
2. **Baseline** — each resource is downloaded and stored as a base64-encoded snapshot on disk.
3. **Monitor** — at a configurable interval, all resources are re-downloaded (no browser needed) and compared against the baseline.
4. **Alert** — changes are logged and exposed as Prometheus metrics so you can wire up alerts in Grafana or Alertmanager.

---

## Features

- **Multi-domain server mode** — monitor dozens of domains from a single process
- **Live control** — add, remove, or refresh domains while the server runs via a TCP CLI (no restart needed)
- **Prometheus metrics** — per-domain and per-resource change gauges, ready for scraping
- **Docker-native** — ships with a `docker-compose.yml` that includes a headless Selenium Chrome node
- **Same-domain filtering** — third-party resources (analytics, CDNs) are intentionally ignored
- **Retry-tolerant downloads** — transient HTTP failures are retried before being flagged as defacement

---

## Quick example

```bash
# Terminal 1 — start the server
python defacemon.py serve

# Terminal 2 — add a site to monitor
python defacemon.py add https://example.com

# List all monitored domains
python defacemon.py list
```

{: .tip }
For production use, run with Docker Compose — Chrome is fully isolated inside a Selenium container.

---

[Get started →](installation){: .btn .btn-primary }
[View on GitHub →](https://github.com/mohammdali-davarzani/defacemon){: .btn }
