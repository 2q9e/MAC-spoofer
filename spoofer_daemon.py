#!/usr/bin/env python3
"""
spoofer_daemon.py: Background detached daemon for the spoofer MAC privacy tool.
Monitors NetworkManager events, handles network transitions, connection profile updates,
and ensures that the spoofed MAC persists across network switches and reconnects.
"""

import os
import sys
import time
import select
import signal
import subprocess
from datetime import datetime
from typing import Optional

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
from state import load_state, get_daemon_pid, save_daemon_pid, PID_FILE, LOG_FILE
from network_manager import (
    get_wifi_interface,
    get_current_mac,
    get_wifi_connections,
    get_active_wifi_connection,
    log_event,
    execute_command
)

_running = True


def signal_handler(signum, frame):
    """Handles SIGTERM / SIGINT for graceful shutdown."""
    global _running
    log_event(f"Daemon received signal {signum}, initiating graceful shutdown...", echo=False)
    _running = False


def ensure_connections_configured(target_mac: str) -> None:
    """
    Checks all Wi-Fi connection profiles in NetworkManager.
    If any profile does not have cloned-mac-address set to target_mac,
    updates it immediately.
    """
    try:
        conns = get_wifi_connections()
        for conn in conns:
            uuid = conn["uuid"]
            name = conn["name"]
            # Check current cloned-mac-address on this connection
            proc = subprocess.run(
                ["nmcli", "-t", "-f", "802-11-wireless.cloned-mac-address", "connection", "show", uuid],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if proc.returncode == 0:
                current_cloned = proc.stdout.strip()
                # Normalize
                if current_cloned.lower() != target_mac.lower():
                    log_event(
                        f"Daemon detected profile '{name}' ({uuid}) with un-spoofed cloned-mac ('{current_cloned}'). "
                        f"Updating to {target_mac}...",
                        echo=False
                    )
                    execute_command(
                        ["nmcli", "connection", "modify", uuid, "802-11-wireless.cloned-mac-address", target_mac],
                        echo=False
                    )
    except Exception as e:
        log_event(f"Daemon error checking connections: {e}", echo=False)


def monitor_loop():
    """
    Main loop of the daemon:
    Periodically inspects connection state and runs `nmcli monitor` output parser.
    """
    global _running
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    pid = os.getpid()
    save_daemon_pid(pid)
    log_event(f"Spoofer daemon started successfully [PID {pid}]. Detached from terminal.", echo=False)

    # Launch nmcli monitor in a subprocess pipe for instant event notifications
    monitor_proc = None
    try:
        monitor_proc = subprocess.Popen(
            ["nmcli", "monitor"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )
    except Exception as e:
        log_event(f"Daemon warning: could not start nmcli monitor ({e}), falling back to polling", echo=False)

    last_poll_time = 0.0
    poll_interval = 3.0  # seconds

    while _running:
        state = load_state()
        if not state or not state.get("active", False):
            log_event("Daemon detected state inactive or removed. Exiting...", echo=False)
            break

        target_mac = state.get("spoofed_mac")
        iface = state.get("interface") or get_wifi_interface()
        if not target_mac or not iface:
            time.sleep(1)
            continue

        now = time.time()
        # Check periodically or when nmcli monitor outputs a line
        should_check = False

        if monitor_proc and monitor_proc.poll() is None and monitor_proc.stdout:
            # Check if there is data to read from nmcli monitor without blocking forever
            r, _, _ = select.select([monitor_proc.stdout], [], [], 0.5)
            if r:
                line = monitor_proc.stdout.readline()
                if line:
                    log_event(f"Daemon observed NM event: {line.strip()}", echo=False)
                    should_check = True
                else:
                    # EOF reached
                    monitor_proc = None

        if (now - last_poll_time) >= poll_interval:
            should_check = True

        if should_check:
            last_poll_time = now
            # 1. Ensure all connection profiles have target_mac
            ensure_connections_configured(target_mac)

            # 2. Check active connection and device MAC
            active_conn = get_active_wifi_connection(iface)
            curr_mac = get_current_mac(iface)

            if active_conn and curr_mac:
                if curr_mac.lower() != target_mac.lower():
                    log_event(
                        f"Daemon detected active connection '{active_conn['name']}' with MAC={curr_mac} != target={target_mac}. "
                        "Re-activating connection to apply spoofed MAC...",
                        echo=False
                    )
                    execute_command(
                        ["nmcli", "connection", "up", "uuid", active_conn["uuid"]],
                        echo=False
                    )

        if not monitor_proc or monitor_proc.poll() is not None:
            time.sleep(1)

    if monitor_proc and monitor_proc.poll() is None:
        try:
            monitor_proc.terminate()
            monitor_proc.wait(timeout=2)
        except Exception:
            pass

    log_event(f"Spoofer daemon [PID {pid}] terminated cleanly.", echo=False)
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                saved_pid = int(f.read().strip())
            if saved_pid == pid:
                os.remove(PID_FILE)
        except Exception:
            pass


if __name__ == "__main__":
    monitor_loop()
