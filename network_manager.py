"""
NetworkManager interaction and system networking helpers for spoofer.
Handles device detection, MAC queries, connection profile updates, reconnection,
and detailed command logging.
"""

import os
import re
import shlex
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, NamedTuple

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(PROJECT_DIR, "spoofer.log")

from colors import (
    c, strip_ansi, BOLD, DIM, RESET,
    BRIGHT_GREEN, BRIGHT_RED, BRIGHT_YELLOW, BRIGHT_CYAN, BRIGHT_MAGENTA, BRIGHT_BLUE, WHITE,
    badge_cmd, badge_ok, badge_err, badge_warn, badge_info, badge_wifi
)


class CommandResult(NamedTuple):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    success: bool


def log_event(message: str, echo: bool = True, badge: str = "") -> None:
    """Logs an event timestamped to LOG_FILE and optionally stdout with ANSI colors."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_badge = strip_ansi(badge)
    clean_msg = strip_ansi(message)
    file_prefix = f"[{timestamp}] " + (f"{clean_badge} " if clean_badge else "")
    file_line = f"{file_prefix}{clean_msg}"

    if echo:
        term_time = f"{DIM}[{timestamp}]{RESET}"
        term_badge = f"{badge} " if badge else ""
        print(f"{term_time} {term_badge}{message}")

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(file_line + "\n")
    except OSError:
        pass


def execute_command(cmd: List[str] | str, echo: bool = True) -> CommandResult:
    """
    Executes a shell command, logs the exact command line, exit code,
    stdout, and stderr, and returns CommandResult.
    """
    if isinstance(cmd, list):
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
        use_shell = False
        args = cmd
    else:
        cmd_str = cmd
        use_shell = True
        args = cmd

    log_event(f"➜ {c(cmd_str, BOLD, BRIGHT_YELLOW)}", echo=echo, badge=badge_cmd("RUN"))
    try:
        proc = subprocess.run(
            args,
            shell=use_shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        res = CommandResult(
            command=cmd_str,
            exit_code=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            success=(proc.returncode == 0)
        )
    except subprocess.TimeoutExpired as e:
        log_event(f"{c('Command timed out after 30s:', BOLD, BRIGHT_RED)} {cmd_str}", echo=echo, badge=badge_err("TIMEOUT"))
        res = CommandResult(
            command=cmd_str,
            exit_code=-1,
            stdout="",
            stderr=f"Timed out after 30 seconds: {e}",
            success=False
        )
    except Exception as e:
        log_event(f"{c('Execution error:', BOLD, BRIGHT_RED)} {e}", echo=echo, badge=badge_err("ERROR"))
        res = CommandResult(
            command=cmd_str,
            exit_code=-1,
            stdout="",
            stderr=str(e),
            success=False
        )

    if res.stdout:
        indented = "\n".join("      " + line for line in res.stdout.splitlines())
        log_event(f"{DIM}Output:{RESET}\n{c(indented, WHITE)}", echo=echo)
    if res.stderr:
        indented_err = "\n".join("      " + line for line in res.stderr.splitlines())
        log_event(f"{BRIGHT_RED}Error:{RESET}\n{c(indented_err, BRIGHT_RED)}", echo=echo)

    if res.success:
        log_event(f"Command succeeded with exit code {c('0', BOLD, BRIGHT_GREEN)}", echo=echo, badge=badge_ok("EXIT 0"))
    else:
        log_event(f"Command failed with exit code {c(str(res.exit_code), BOLD, BRIGHT_RED)}", echo=echo, badge=badge_err(f"EXIT {res.exit_code}"))

    return res


def get_wifi_interface() -> Optional[str]:
    """
    Detects the active Wi-Fi interface on the system.
    Tries nmcli device status first, then falls back to sysfs / ip link.
    """
    # Try nmcli
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE", "device"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if ":" in line:
                    dev, dtype = line.split(":", 1)
                    if dtype.strip() in ("wifi", "802-11-wireless"):
                        return dev.strip()
    except Exception:
        pass

    # Fallback to sysfs
    net_dir = "/sys/class/net"
    if os.path.isdir(net_dir):
        for iface in os.listdir(net_dir):
            if os.path.isdir(os.path.join(net_dir, iface, "wireless")) or iface.startswith(("wl", "wlan")):
                return iface

    # Fallback to ip link
    try:
        proc = subprocess.run(
            ["ip", "-o", "link"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                m = re.search(r"^\d+:\s+([a-zA-Z0-9_-]+):", line)
                if m:
                    iface = m.group(1)
                    if iface.startswith(("wl", "wlan")):
                        return iface
    except Exception:
        pass

    return None


def get_permanent_mac(iface: str) -> Optional[str]:
    """
    Retrieves the burned-in permanent hardware MAC address for the given interface.
    Checks `ip link show dev <iface>`, sysfs `perm_address`, or `nmcli device show`.
    """
    # 1. Check ip link show dev <iface>
    try:
        proc = subprocess.run(
            ["ip", "link", "show", "dev", iface],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            m = re.search(r"permaddr\s+([0-9a-fA-F:]{17})", proc.stdout)
            if m:
                return m.group(1).lower()
    except Exception:
        pass

    # 2. Check sysfs perm_address
    sys_perm = f"/sys/class/net/{iface}/perm_address"
    if os.path.isfile(sys_perm):
        try:
            with open(sys_perm, "r", encoding="utf-8") as f:
                mac = f.read().strip()
                if len(mac) == 17:
                    return mac.lower()
        except OSError:
            pass

    # 3. Check ethtool -P
    try:
        proc = subprocess.run(
            ["ethtool", "-P", iface],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            m = re.search(r"Permanent address:\s+([0-9a-fA-F:]{17})", proc.stdout)
            if m:
                return m.group(1).lower()
    except Exception:
        pass

    # 4. Fallback: get current MAC as baseline
    return get_current_mac(iface)


def get_current_mac(iface: str) -> Optional[str]:
    """Retrieves the current operational MAC address of the interface."""
    sys_addr = f"/sys/class/net/{iface}/address"
    if os.path.isfile(sys_addr):
        try:
            with open(sys_addr, "r", encoding="utf-8") as f:
                mac = f.read().strip()
                if len(mac) == 17:
                    return mac.lower()
        except OSError:
            pass

    try:
        proc = subprocess.run(
            ["ip", "link", "show", "dev", iface],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            m = re.search(r"link/ether\s+([0-9a-fA-F:]{17})", proc.stdout)
            if m:
                return m.group(1).lower()
    except Exception:
        pass

    return None


def get_wifi_connections() -> List[Dict[str, str]]:
    """
    Returns a list of all Wi-Fi connection profiles in NetworkManager.
    Each item: {"uuid": str, "name": str, "type": str}
    """
    conns = []
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "UUID,TYPE,NAME", "connection", "show"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                parts = line.split(":")
                if len(parts) >= 3:
                    uuid, ctype, name = parts[0], parts[1], ":".join(parts[2:])
                    if ctype in ("802-11-wireless", "wifi"):
                        conns.append({"uuid": uuid, "type": ctype, "name": name})
    except Exception:
        pass
    return conns


def get_active_wifi_connection(iface: str) -> Optional[Dict[str, str]]:
    """
    Returns details of the currently active Wi-Fi connection on iface, if any.
    Returns {"uuid": str, "name": str} or None.
    """
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,TYPE,UUID,NAME", "connection", "show", "--active"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                parts = line.split(":")
                if len(parts) >= 4:
                    dev, ctype, uuid, name = parts[0], parts[1], parts[2], ":".join(parts[3:])
                    if dev == iface and ctype in ("802-11-wireless", "wifi"):
                        return {"uuid": uuid, "name": name}
    except Exception:
        pass
    return None


def apply_spoofed_mac_to_connections(mac: str, echo: bool = True) -> bool:
    """
    Configures `802-11-wireless.cloned-mac-address` = mac on all known Wi-Fi connections.
    Logs each command executed.
    """
    wifi_conns = get_wifi_connections()
    if not wifi_conns:
        log_event(c("No existing Wi-Fi connection profiles found.", BRIGHT_YELLOW), echo=echo, badge=badge_warn("PROFILES"))
        return True

    all_success = True
    for conn in wifi_conns:
        uuid = conn["uuid"]
        name = conn["name"]
        cmd = ["nmcli", "connection", "modify", uuid, "802-11-wireless.cloned-mac-address", mac]
        res = execute_command(cmd, echo=echo)
        if not res.success:
            all_success = False
            log_event(f"Failed to set cloned-mac on connection '{c(name, BOLD, WHITE)}' ({uuid})", echo=echo, badge=badge_err("FAIL"))
        else:
            log_event(f"Configured cloned-mac={c(mac, BOLD, BRIGHT_GREEN)} on '{c(name, BOLD, WHITE)}'", echo=echo, badge=badge_ok("CONFIG"))

    return all_success


def restore_connections_mac(echo: bool = True) -> bool:
    """
    Resets `802-11-wireless.cloned-mac-address` back to empty (default hardware MAC)
    on all known Wi-Fi connections.
    """
    wifi_conns = get_wifi_connections()
    if not wifi_conns:
        log_event(c("No Wi-Fi connections to restore.", BRIGHT_YELLOW), echo=echo, badge=badge_warn("PROFILES"))
        return True

    all_success = True
    for conn in wifi_conns:
        uuid = conn["uuid"]
        name = conn["name"]
        cmd = ["nmcli", "connection", "modify", uuid, "802-11-wireless.cloned-mac-address", ""]
        res = execute_command(cmd, echo=echo)
        if not res.success:
            all_success = False
            log_event(f"Failed to reset cloned-mac on connection '{c(name, BOLD, WHITE)}' ({uuid})", echo=echo, badge=badge_err("FAIL"))
        else:
            log_event(f"Reset cloned-mac setting on connection '{c(name, BOLD, WHITE)}'", echo=echo, badge=badge_ok("RESTORE"))

    return all_success


def redo_wlan_connection(iface: str, echo: bool = True) -> bool:
    """
    Redoes the device connection with WLAN so that the cloned-mac setting takes effect immediately.
    If a Wi-Fi connection is active, brings it up again via `nmcli connection up uuid <uuid>`.
    If no connection is active, attempts `nmcli device connect <iface>`.
    """
    active_conn = get_active_wifi_connection(iface)
    if active_conn:
        uuid = active_conn["uuid"]
        name = active_conn["name"]
        log_event(f"Active connection detected: '{c(name, BOLD, BRIGHT_CYAN)}' ({uuid}). Re-applying connection...", echo=echo, badge=badge_wifi("WLAN"))
        cmd = ["nmcli", "connection", "up", "uuid", uuid]
        res = execute_command(cmd, echo=echo)
        return res.success
    else:
        log_event(f"No active connection on {c(iface, BOLD, WHITE)}. Attempting device connect...", echo=echo, badge=badge_wifi("WLAN"))
        cmd = ["nmcli", "device", "connect", iface]
        res = execute_command(cmd, echo=echo)
        return True
