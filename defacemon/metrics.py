"""Prometheus metrics: state and HTTP /metrics endpoint."""

import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)
log = logger.info

# Per-domain: { domain: { "domain_changed": 0|1, "resource_changed": {url: 0|1} } }
_metrics_lock = threading.Lock()
_metrics = {"domains": {}}


def _prometheus_escape(s):
    """Escape backslash and double-quote for Prometheus label values."""
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


def render_prometheus_metrics():
    """Render current metrics in Prometheus text exposition format (all domains)."""
    with _metrics_lock:
        domains = dict(_metrics["domains"])
    lines = [
        "# HELP defacemon_domain_changed 1 if the domain had any change since last check, 0 otherwise",
        "# TYPE defacemon_domain_changed gauge",
    ]
    for domain, data in sorted(domains.items()):
        lines.append(f'defacemon_domain_changed{{domain="{_prometheus_escape(domain)}"}} {data["domain_changed"]}')
    lines.extend([
        "# HELP defacemon_resource_changed 1 if this resource changed since last check, 0 otherwise",
        "# TYPE defacemon_resource_changed gauge",
    ])
    for domain, data in sorted(domains.items()):
        for url, value in sorted(data["resource_changed"].items()):
            lines.append(f'defacemon_resource_changed{{domain="{_prometheus_escape(domain)}",resource="{_prometheus_escape(url)}"}} {value}')
    return "\n".join(lines) + "\n"


def update_metrics(domain, changed_urls, all_urls):
    """Update metrics state after a check: 0/1 for domain changed, 0/1 per resource."""
    with _metrics_lock:
        _metrics["domains"][domain] = {
            "domain_changed": 1 if changed_urls else 0,
            "resource_changed": {url: (1 if url in changed_urls else 0) for url in all_urls},
        }


def remove_domain_from_metrics(domain):
    """Remove a domain from metrics (e.g. when domain is removed from monitor)."""
    with _metrics_lock:
        _metrics["domains"].pop(domain, None)


def _metrics_only_handler_class():
    class MetricsOnlyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0].rstrip("/") == "/metrics":
                body = render_prometheus_metrics().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            logger.debug(format, *args)

    return MetricsOnlyHandler


def start_metrics_server(host="0.0.0.0", port=9090):
    """Start HTTP server for /metrics only (single-domain mode)."""
    server = HTTPServer((host, port), _metrics_only_handler_class())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log("Metrics server listening on http://%s:%s/metrics", host, port)
    return server
