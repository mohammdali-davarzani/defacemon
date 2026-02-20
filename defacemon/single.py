"""Legacy single-domain monitor: one URL, one baseline, loop in foreground."""

import logging
import time
from pathlib import Path
from urllib.parse import urlparse

from defacemon import baseline, metrics, resources

logger = logging.getLogger(__name__)
log = logger.info


def run_monitor(main_url, interval_sec, baseline_path, metrics_host=None, metrics_port=None):
    """Establish or load baseline, then periodically recheck and report changes."""
    baseline_path = Path(baseline_path)
    bl = baseline.load_baseline(baseline_path)
    domain = urlparse(main_url).netloc or main_url

    if metrics_port is not None:
        metrics.start_metrics_server(host=metrics_host or "0.0.0.0", port=metrics_port)

    if bl is None or not bl:
        log("No baseline found. Discovering all resources with browser...")
        encoded = resources.get_resources(main_url)
        if not encoded:
            logger.error("No resources found. Check URL.")
            return
        baseline.save_baseline(baseline_path, encoded, main_url)
        bl = {k: v for k, v in encoded.items() if v is not None}

    urls = list(bl.keys())
    metrics.update_metrics(domain, set(), urls)
    log("Monitoring %d URLs every %s seconds (baseline: %s)", len(urls), interval_sec, baseline_path)

    while True:
        time.sleep(interval_sec)
        log("Rechecking %d resources...", len(urls))
        current = baseline.recheck_encoded(urls)
        if baseline.detect_changes(bl, current):
            added, removed, changed = baseline.get_changed_urls(bl, current)
            changed_urls = set(added) | set(removed) | set(changed)
            all_urls_for_metrics = urls + [u for u in added if u not in bl]
            metrics.update_metrics(domain, changed_urls, all_urls_for_metrics)
            if added:
                logger.warning("Added URLs: %s", added)
            if removed:
                logger.warning("Removed URLs: %s", removed)
            if changed:
                logger.warning("Content changed: %s", changed)
            logger.warning("Change detected. Update baseline with --refresh to store new state.")
        else:
            metrics.update_metrics(domain, set(), urls)
            log("No changes detected.")
