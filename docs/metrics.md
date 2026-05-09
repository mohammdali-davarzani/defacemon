---
title: Metrics
nav_order: 5
---

# Prometheus Metrics

When the server runs with a metrics port (default `9192`), Prometheus can scrape the `/metrics` endpoint.

```
GET http://<host>:9192/metrics
```

---

## Available metrics

### `defacemon_domain_changed`

**Type:** Gauge

`1` if any resource on the domain changed during the last check cycle, `0` otherwise.

```
defacemon_domain_changed{domain="example.com"} 0
defacemon_domain_changed{domain="another-site.org"} 1
```

---

### `defacemon_resource_changed`

**Type:** Gauge

`1` if this specific resource changed (added, removed, or content modified) during the last check, `0` otherwise.

```
defacemon_resource_changed{domain="example.com",resource="https://example.com/app.js"} 0
defacemon_resource_changed{domain="example.com",resource="https://example.com/style.css"} 1
```

---

## Prometheus scrape config

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: defacemon
    static_configs:
      - targets: ["localhost:9192"]
```

---

## Example Grafana alert

To get alerted when any monitored domain is defaced:

```yaml
# Alertmanager rule
- alert: WebsiteDefaced
  expr: defacemon_domain_changed == 1
  for: 0m
  labels:
    severity: critical
  annotations:
    summary: "Defacement detected on {{ $labels.domain }}"
```

---

## Disabling metrics

Pass `--metrics-port 0` to `serve` to disable the metrics HTTP server entirely:

```bash
python defacemon.py serve --metrics-port 0
```
