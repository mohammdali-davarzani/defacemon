"""CLI entry point: argparse and command dispatch."""

import argparse
import json
import logging
import sys

from defacemon import baseline, config, resources, server, single

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
log = logger.info


def main():
    parser = argparse.ArgumentParser(
        description="Monitor static website files. Server mode: defacemon serve. CLI: defacemon add/list/refresh/remove.",
    )
    parser.add_argument(
        "--control-host",
        default=config.CONTROL_DEFAULT_HOST,
        help="Control server host (default: 127.0.0.1). For CLI commands.",
    )
    parser.add_argument(
        "--control-port",
        type=int,
        default=config.CONTROL_DEFAULT_PORT,
        metavar="PORT",
        help="Control server port (default: %s). For CLI and serve." % config.CONTROL_DEFAULT_PORT,
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # serve
    p_serve = sub.add_parser("serve", help="Run server in foreground; use add/list/refresh/remove from another terminal")
    p_serve.add_argument("--control-host", default=config.CONTROL_DEFAULT_HOST, help="Bind control server to this host")
    p_serve.add_argument("--control-port", type=int, default=config.CONTROL_DEFAULT_PORT, help="Control port")
    p_serve.add_argument("--metrics-port", type=int, default=9192, help="Prometheus metrics HTTP port (0 to disable)")
    p_serve.add_argument("--metrics-host", default="127.0.0.1", help="Bind metrics to this host")
    p_serve.add_argument("--baseline-dir", default=".", help="Directory for baseline files")

    # add
    p_add = sub.add_parser("add", help="Add domain to monitor (server must be running)")
    p_add.add_argument("url", nargs="?", default=None, help="Page URL (e.g. https://example.com)")
    p_add.add_argument("-i", "--interval", type=float, default=60.0, help="Check interval in seconds")

    # list
    sub.add_parser("list", help="List monitored domains")

    # refresh
    p_refresh = sub.add_parser("refresh", help="Re-discover resources and refresh baseline for a domain")
    p_refresh.add_argument("domain", help="Domain (e.g. example.com)")

    # remove
    p_remove = sub.add_parser("remove", help="Stop monitoring a domain")
    p_remove.add_argument("domain", help="Domain (e.g. example.com)")

    # Legacy
    parser.add_argument("legacy_url", nargs="?", default=None, help="(Legacy) Single URL to monitor")
    parser.add_argument("-i", "--interval", type=float, default=60.0, help="Recheck interval (legacy mode)")
    parser.add_argument("-b", "--baseline", default=".defacemon_baseline.json", help="Baseline file (legacy)")
    parser.add_argument("--refresh", action="store_true", help="(Legacy) Refresh baseline and exit")
    parser.add_argument("--metrics-port", type=int, default=None, help="(Legacy) Expose metrics on this port")
    parser.add_argument("--metrics-host", default="0.0.0.0", help="(Legacy) Metrics bind host")

    args = parser.parse_args()

    if args.command == "serve":
        server.run_server(
            control_host=args.control_host,
            control_port=args.control_port,
            metrics_host=args.metrics_host,
            metrics_port=args.metrics_port,
            baseline_dir=args.baseline_dir,
        )
        return

    if args.command == "add":
        url = getattr(args, "url", None) or getattr(args, "legacy_url", None)
        if not url:
            parser.error("add requires URL: defacemon add <url>")
        ok, out = server.cli_send(args.control_host, args.control_port, f"ADD {url} {args.interval}")
        if ok:
            try:
                d = json.loads(out)
                print("OK domain:", d.get("domain", out))
            except json.JSONDecodeError:
                print("OK", out)
        else:
            print("ERR", out, file=sys.stderr)
            sys.exit(1)
        return

    if args.command == "list":
        ok, out = server.cli_send(args.control_host, args.control_port, "LIST")
        if not ok:
            print("ERR", out, file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(out)
            if not data:
                print("(no domains)")
            else:
                for d in data:
                    print(d["domain"], d["main_url"], "interval=%s" % d["interval_sec"], "resources=%s" % d["resource_count"])
        except json.JSONDecodeError:
            print(out)
        return

    if args.command == "refresh":
        ok, out = server.cli_send(args.control_host, args.control_port, f"REFRESH {args.domain}")
        if ok:
            try:
                d = json.loads(out)
                print("OK refreshed", d.get("domain", out))
            except json.JSONDecodeError:
                print("OK", out)
        else:
            print("ERR", out, file=sys.stderr)
            sys.exit(1)
        return

    if args.command == "remove":
        ok, out = server.cli_send(args.control_host, args.control_port, f"REMOVE {args.domain}")
        if not ok:
            print("ERR", out, file=sys.stderr)
            sys.exit(1)
        try:
            d = json.loads(out)
            print("OK removed", d.get("domain", out))
        except json.JSONDecodeError:
            print("OK", out)
        return

    # Legacy: single URL without subcommand
    if not args.legacy_url:
        parser.print_help()
        parser.error("Use: defacemon serve | add <url> | list | refresh <domain> | remove <domain>  OR  defacemon <url> (legacy)")
    if args.refresh:
        log("Refreshing baseline for %s", args.legacy_url)
        encoded = resources.get_resources(args.legacy_url)
        if encoded:
            baseline.save_baseline(args.baseline, encoded, args.legacy_url)
        return
    single.run_monitor(
        args.legacy_url,
        args.interval,
        args.baseline,
        metrics_host=args.metrics_host,
        metrics_port=args.metrics_port,
    )
