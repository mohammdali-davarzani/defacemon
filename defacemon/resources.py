"""Resource discovery and encoding: browser-based discovery and HTTP download."""

import base64
import logging
import os
import time
from urllib.parse import urlparse

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)
log = logger.info

# Set DEFACEMON_HEADLESS=1 to run Chrome headless (local mode only)
HEADLESS = os.environ.get("DEFACEMON_HEADLESS", "").strip() in ("1", "true", "yes")
# Set SELENIUM_REMOTE_URL to delegate browser to a remote WebDriver node
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL", "").strip()


def _collect_resource_urls(tree):
    """Recursively collect all resource URLs from CDP frame tree."""
    urls = []
    if not tree:
        return urls
    frame_tree = tree.get("frameTree") or tree
    for r in frame_tree.get("resources") or []:
        u = r.get("url") or ""
        if u:
            urls.append(u)
    for child in frame_tree.get("childFrames") or []:
        urls.extend(_collect_resource_urls({"frameTree": child}))
    return urls


def _same_domain(url, main_url):
    """Return True if url has the same host as main_url (ignore third-party domains)."""
    try:
        return urlparse(url).netloc and urlparse(url).netloc == urlparse(main_url).netloc
    except Exception:
        return False


def get_resources(main_url):
    """Discover same-domain resources for main_url via browser, return url -> base64 encoded content."""
    options = webdriver.ChromeOptions()
    options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
    if SELENIUM_REMOTE_URL:
        driver = webdriver.Remote(command_executor=SELENIUM_REMOTE_URL, options=options)
    else:
        if HEADLESS:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            if os.path.isfile("/usr/bin/chromium"):
                options.binary_location = "/usr/bin/chromium"
        driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(90)

    try:
        try:
            driver.get(main_url)
        except TimeoutException:
            # Page load timed out but resources may have partially loaded — continue with what we have.
            logger.warning("Page load timed out for %s, proceeding with partial resource list", main_url)
        time.sleep(7)  # consider using explicit waits

        resources = driver.execute_cdp_cmd("Page.getResourceTree", {})
        all_urls = _collect_resource_urls(resources)
        same_domain_urls = [u for u in all_urls if _same_domain(u, main_url)]
        if len(all_urls) != len(same_domain_urls):
            log("Filtered to same domain only: %d of %d resources", len(same_domain_urls), len(all_urls))

        encoded_resources = {
            url: download_and_encode(url) for url in same_domain_urls
        }

        return encoded_resources
    finally:
        driver.quit()


def download_and_encode(url):
    """Fetch URL and return base64-encoded body, or None on error."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")
    except Exception as e:
        logger.error("Failed to download %s: %s", url, e)
        return None
