"""Monitor core: multi-domain monitoring with per-domain check loops and baselines."""

import logging
import threading
from pathlib import Path
from urllib.parse import urlparse

from defacemon import baseline, metrics, resources

logger = logging.getLogger(__name__)
log = logger.info


class MonitorCore:
    """Background core: multiple domains, each with its own check loop and baseline."""

    def __init__(self, baseline_dir="."):
        self.baseline_dir = Path(baseline_dir)
        self._lock = threading.Lock()
        self._domains = {}  # domain -> { main_url, interval_sec, baseline_path, baseline, urls, stop_event, thread }

    def _domain_loop(self, domain):
        state = self._domains.get(domain)
        if not state:
            return
        while not state["stop_event"].is_set():
            if state["stop_event"].wait(timeout=state["interval_sec"]):
                break
            with self._lock:
                if domain not in self._domains:
                    break
                urls = list(state["baseline"].keys())
                baseline_snapshot = dict(state["baseline"])
            current = baseline.recheck_encoded(urls)
            if baseline.detect_changes(baseline_snapshot, current):
                added, removed, changed = baseline.get_changed_urls(baseline_snapshot, current)
                changed_set = set(added) | set(removed) | set(changed)
                all_urls = urls + [u for u in added if u not in baseline_snapshot]
                metrics.update_metrics(domain, changed_set, all_urls)
                logger.warning(
                    "[%s] Change detected: added=%s removed=%s changed=%s",
                    domain, len(added), len(removed), len(changed),
                )
            else:
                metrics.update_metrics(domain, set(), urls)
                log("[%s] No changes detected.", domain)

    def add_domain(self, main_url, interval_sec=60.0, baseline_path=None):
        """Add a domain to monitor. Creates baseline if missing. Returns (domain, error_message or None)."""
        domain = urlparse(main_url).netloc or main_url
        if not domain:
            return None, "Invalid URL: no host"
        baseline_path = Path(baseline_path) if baseline_path else baseline.baseline_path_for_domain(domain, self.baseline_dir)
        with self._lock:
            if domain in self._domains:
                return domain, "Domain already monitored"
            bl = baseline.load_baseline(baseline_path)
            if bl is None or not bl:
                # Blocking: discover with browser (caller may run in thread)
                log("ADD: opening URL with browser: %s", main_url)
                encoded = resources.get_resources(main_url)
                if not encoded:
                    return None, "No resources found"
                baseline.save_baseline(baseline_path, encoded, main_url)
                bl = {k: v for k, v in encoded.items() if v is not None}
            urls = list(bl.keys())
            stop_event = threading.Event()
            state = {
                "main_url": main_url,
                "interval_sec": interval_sec,
                "baseline_path": baseline_path,
                "baseline": bl,
                "urls": urls,
                "stop_event": stop_event,
                "thread": None,
            }
            self._domains[domain] = state
            metrics.update_metrics(domain, set(), urls)
            thread = threading.Thread(target=self._domain_loop, args=(domain,), daemon=True)
            state["thread"] = thread
            thread.start()
        log("Added domain %s (%d resources, interval %.0fs)", domain, len(urls), interval_sec)
        return domain, None

    def refresh_domain(self, domain):
        """Re-discover resources for domain with browser and update baseline. Returns (ok, error_message)."""
        with self._lock:
            state = self._domains.get(domain)
            if not state:
                return False, "Domain not found"
            main_url = state["main_url"]
            baseline_path = state["baseline_path"]
        encoded = resources.get_resources(main_url)
        if not encoded:
            return False, "No resources found"
        baseline.save_baseline(baseline_path, encoded, main_url)
        with self._lock:
            state = self._domains.get(domain)
            if not state:
                return False, "Domain removed while refreshing"
            state["baseline"] = {k: v for k, v in encoded.items() if v is not None}
            state["urls"] = list(state["baseline"].keys())
        metrics.update_metrics(domain, set(), state["urls"])
        log("Refreshed baseline for %s (%d resources)", domain, len(state["baseline"]))
        return True, None

    def list_domains(self):
        """Return list of { domain, main_url, interval_sec, baseline_path, resource_count }."""
        with self._lock:
            return [
                {
                    "domain": d,
                    "main_url": s["main_url"],
                    "interval_sec": s["interval_sec"],
                    "baseline_path": str(s["baseline_path"]),
                    "resource_count": len(s["baseline"]),
                }
                for d, s in self._domains.items()
            ]

    def remove_domain(self, domain):
        """Stop monitoring a domain. Returns True if it was removed."""
        with self._lock:
            state = self._domains.get(domain)
            if not state:
                return False
            state["stop_event"].set()
            del self._domains[domain]
        metrics.remove_domain_from_metrics(domain)
        log("Removed domain %s", domain)
        return True
