"""Baseline storage and change detection."""

import json
import logging
from pathlib import Path

from defacemon import config
from defacemon.resources import download_and_encode

logger = logging.getLogger(__name__)
log = logger.info


def save_baseline(path, encoded_resources, main_url=""):
    """Persist baseline: urls and their encoded content."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "main_url": main_url,
        "urls": list(encoded_resources.keys()),
        "encoded": {k: v for k, v in encoded_resources.items() if v is not None},
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log("Baseline saved to %s (%d resources)", path, len(data["encoded"]))


def load_baseline(path):
    """Load baseline from file. Returns dict url -> base64 or None if missing/invalid."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("encoded") or {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not load baseline from %s: %s", path, e)
        return None


def baseline_path_for_domain(domain, base_dir="."):
    """Default baseline file path for a domain (under base_dir/domains-baseline/)."""
    safe = (domain or "default").replace(".", "_").replace(":", "_")
    return Path(base_dir) / config.BASELINE_SUBDIR / f".defacemon_baseline_{safe}.json"


def detect_changes(old, new):
    """Return True if encoded content or set of URLs changed. Ignores None values."""
    old_keys = {k for k, v in old.items() if v is not None}
    new_keys = {k for k, v in new.items() if v is not None}
    if old_keys != new_keys:
        return True
    for url in old_keys:
        if old.get(url) != new.get(url):
            return True
    return False


def get_changed_urls(old, new):
    """Return list of URLs that were added, removed, or have different content."""
    old_keys = {k for k, v in old.items() if v is not None}
    new_keys = {k for k, v in new.items() if v is not None}
    added = new_keys - old_keys
    removed = old_keys - new_keys
    changed = [u for u in old_keys & new_keys if old[u] != new[u]]
    return list(added), list(removed), changed


def recheck_encoded(urls):
    """Re-download and base64-encode the given URLs (no browser)."""
    return {url: download_and_encode(url) for url in urls}
