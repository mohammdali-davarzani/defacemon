"""TCP control server and CLI client: line-based protocol (ADD/REFRESH/LIST/REMOVE)."""

import json
import logging
import socket
import threading

from defacemon.core import MonitorCore
from defacemon import metrics

logger = logging.getLogger(__name__)
log = logger.info


def _handle_control_command(core, line):
    """Parse one line command, call core, return response line (OK\t... or ERR\t...)."""
    line = (line or "").strip()
    if not line:
        return "ERR\tempty command"
    parts = line.split()
    cmd = parts[0].upper()
    if cmd == "ADD":
        if len(parts) < 2:
            return "ERR\tADD requires URL"
        url = parts[1].strip()
        interval = 60.0
        if len(parts) >= 3:
            try:
                interval = float(parts[2])
            except ValueError:
                pass
        domain, err = core.add_domain(url, interval_sec=interval)
        if err:
            return "ERR\t" + err
        return "OK\t" + json.dumps({"domain": domain})
    if cmd == "REFRESH":
        if len(parts) < 2:
            return "ERR\tREFRESH requires domain"
        domain = parts[1].strip()
        ok, err = core.refresh_domain(domain)
        if not ok:
            return "ERR\t" + (err or "failed")
        return "OK\t" + json.dumps({"domain": domain})
    if cmd == "LIST":
        data = core.list_domains()
        return "OK\t" + json.dumps(data)
    if cmd == "REMOVE":
        if len(parts) < 2:
            return "ERR\tREMOVE requires domain"
        domain = parts[1].strip()
        if core.remove_domain(domain):
            return "OK\t" + json.dumps({"domain": domain})
        return "ERR\tDomain not found"
    return "ERR\tunknown command: " + cmd


def _control_connection(core, conn):
    """Handle one client connection: read lines, send responses."""
    try:
        with conn:
            buf = b""
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf or b"\r" in buf:
                    line, _, buf = buf.partition(b"\n")
                    line = line.replace(b"\r", b"").decode("utf-8", errors="replace")
                    if not line.strip():
                        continue
                    resp = _handle_control_command(core, line)
                    conn.sendall((resp + "\n").encode("utf-8"))
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        logger.debug("Control connection closed: %s", e)


def _run_control_server(core, host, port):
    """Run TCP control server (blocking)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(8)
    log("Control server listening on %s:%s (use defacemon add/list/refresh/remove)", host, port)
    while True:
        conn, _ = sock.accept()
        threading.Thread(target=_control_connection, args=(core, conn), daemon=True).start()


def run_server(control_host="127.0.0.1", control_port=9191, metrics_host="127.0.0.1", metrics_port=9192, baseline_dir="."):
    """Run in foreground: TCP control server + optional HTTP metrics. Use CLI to add/refresh domains."""
    core = MonitorCore(baseline_dir=baseline_dir)
    if metrics_port is not None and metrics_port != 0:
        metrics.start_metrics_server(host=metrics_host, port=metrics_port)
    _run_control_server(core, control_host, control_port)


def cli_send(host, port, command_line):
    """Send one command to the control server; return (success, response_body or error message)."""
    try:
        # ADD can take 60+ s (browser discovery); use long timeout so CLI doesn't drop before response
        with socket.create_connection((host, port), timeout=120) as sock:
            sock.sendall((command_line.strip() + "\n").encode("utf-8"))
            buf = b""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                buf += data
                if b"\n" in buf:
                    line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace").rstrip()
                    if line.startswith("OK\t"):
                        return True, line[3:].strip()
                    if line.startswith("ERR\t"):
                        return False, line[4:].strip()
                    return False, line or "empty response"
            return False, buf.decode("utf-8", errors="replace").strip() or "empty response (connection closed)"
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return False, f"Cannot connect to defacemon server at {host}:{port}. Is it running? ({e})"
