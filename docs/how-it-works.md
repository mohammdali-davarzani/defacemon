---
title: How It Works
nav_order: 7
---

# How It Works

## Overview

Defacemon works in two distinct phases for each monitored domain:

```
Phase 1 — Baseline (browser required, runs once)
  Load page in Chrome → wait for JS/resources to finish →
  CDP Page.getResourceTree → filter same-domain URLs →
  download each URL → base64-encode → save to JSON

Phase 2 — Recheck (no browser, runs every interval)
  Re-download each known URL via HTTP →
  base64-encode → compare to baseline →
  log changes + update Prometheus metrics
```

---

## Resource discovery

When a domain is first added (or refreshed), defacemon uses **Chrome DevTools Protocol** to collect the complete resource tree after the page finishes loading:

1. Chrome navigates to the URL with `PageLoadStrategy.none` (returns immediately).
2. defacemon polls `document.readyState` for up to 30 seconds until the page reports `complete`.
3. An extra 5-second sleep allows lazy-loaded or deferred resources to finish.
4. `Page.getResourceTree` returns every resource the browser actually loaded — including dynamically injected scripts.
5. URLs from third-party domains (analytics, CDNs, fonts from other hosts) are **filtered out**. Only resources on the **same host** as the main URL are tracked.

---

## Change detection

On each recheck cycle, defacemon re-downloads every known URL using plain HTTP requests (no browser). It compares the new base64-encoded content against the baseline snapshot in memory:

| Situation | Classification |
|---|---|
| URL present in baseline, content matches | No change |
| URL present in baseline, content differs | **Changed** |
| URL in baseline, download now fails (all retries) | **Removed / defaced** |
| URL not in baseline, now present | **Added** |

A download failure is treated as a potential defacement because it may indicate the resource was removed or replaced with a redirect.

---

## Architecture (server mode)

```
defacemon.py (entry point)
      │
      └─► cli.py (argparse)
              │
    ┌─────────┴──────────┐
    │                    │
  serve               add/list/refresh/remove
    │                    │
  server.py           server.py
  run_server()        cli_send()  ──TCP──► control server
    │
  MonitorCore (core.py)
    ├── _lock (threading.Lock)
    ├── domain A: state + stop_event + Thread(_domain_loop)
    ├── domain B: state + stop_event + Thread(_domain_loop)
    └── ...

_domain_loop()
  └── every interval_sec:
        recheck_encoded(urls)      ← baseline.py → resources.py
        detect_changes(old, new)   ← baseline.py
        update_metrics(...)        ← metrics.py

metrics.py
  ├── _metrics dict (in-memory, protected by _metrics_lock)
  └── HTTPServer thread → GET /metrics → render_prometheus_metrics()
```

Each domain runs its own daemon thread. The `MonitorCore._lock` protects the `_domains` dict; browser discovery for `add` and `refresh` happens **outside** the lock to avoid blocking other domains.

---

## Baseline file location

```
<baseline-dir>/
└── domains-baseline/
    └── .defacemon_baseline_<domain_with_dots_replaced_by_underscores>.json
```

Example: `https://example.com` → `domains-baseline/.defacemon_baseline_example_com.json`
