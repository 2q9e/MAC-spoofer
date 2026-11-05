#!/usr/bin/env python3
"""
spoofer.py: Main CLI utility for MAC address privacy & spoofing.
Commands:
  spoofer run     - Generates a random authentic laptop MAC, applies it, reconnects WLAN,
                    and detaches a background daemon from the terminal.
  spoofer stop    - Restores the permanent hardware MAC, stops background daemon,
                    and reconnects WLAN.
  spoofer status  - Displays current MAC, permanent MAC, spoofing state, and daemon health.
  spoofer logs    - Displays recent log entries.
"""

import os
import sys
import time
import signal
import subprocess
from datetime import datetime
from typing import Optional

# Ensure project directory is in sys.path
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from laptop_database import generate_random_mac, validate_mac
from colors import (
    c, strip_ansi, BOLD, DIM, RESET,
    BRIGHT_GREEN, BRIGHT_RED, BRIGHT_YELLOW, BRIGHT_CYAN, BRIGHT_MAGENTA, BRIGHT_BLUE, BRIGHT_WHITE, WHITE,
    badge_cmd, badge_ok, badge_err, badge_warn, badge_info, badge_wifi, badge_laptop,
    badge_active, badge_inactive, format_card, CYAN, GREEN, YELLOW, RED
)
from state import (
    load_state,
    save_state,
    clear_state,
    get_daemon_pid,
    save_daemon_pid,
    STATE_FILE,
    PID_FILE,
    LOG_FILE,
)
from network_manager import (
    get_wifi_interface,
    get_permanent_mac,
    get_current_mac,
    get_active_wifi_connection,
    apply_spoofed_mac_to_connections,
    restore_connections_mac,
    redo_wlan_connection,
    log_event,
    execute_command,
)


def print_banner(title: str, border_color: str = CYAN):
    width = 72
    clean_title = strip_ansi(title)
    padding = max(0, width - 4 - len(clean_title))
    print(f"\n{border_color}┌{'─' * (width - 2)}┐{RESET}")
    print(f"{border_color}│{RESET}  {BOLD}{title}{RESET}{' ' * padding}{border_color}│{RESET}")
    print(f"{border_color}└{'─' * (width - 2)}┘{RESET}\n")


def cmd_run():
    print_banner("Starting MAC Address Spoofer")
    log_event("Command 'spoofer run' invoked.")

    # 1. Check if already running
    existing_state = load_state()
    existing_pid = get_daemon_pid()
    if existing_state and existing_state.get("active", False) and existing_pid:
        log_event(
            f"Spoofer is already active! Spoofed MAC: {existing_state.get('spoofed_mac')} "
            f"({existing_state.get('laptop_model')}) [Daemon PID: {existing_pid}]."
        )
        print("\nTip: Run 'spoofer stop' first if you want to generate a new MAC or restore your original.")
        return 0

    # 2. Discover Wi-Fi Interface
    iface = get_wifi_interface()
    if not iface:
        log_event("ERROR: No wireless network interface found on this system.")
        return 1

    log_event(f"Detected Wi-Fi interface: {iface}")

    # 3. Discover Permanent Hardware MAC (for safe restoration)
    # If a previous state recorded the permanent MAC, preserve it so repeated runs never overwrite it
    if existing_state and existing_state.get("permanent_mac"):
        perm_mac = existing_state["permanent_mac"]
    else:
        perm_mac = get_permanent_mac(iface)

    curr_mac = get_current_mac(iface)
    log_event(f"Current Interface MAC: {curr_mac}")
    log_event(f"Permanent Hardware MAC: {perm_mac} (saved for restoration)")

    # 4. Generate Random Laptop MAC (authentic OUI, globally administered)
    generated = generate_random_mac()
    spoofed_mac = generated["mac"]
    laptop_model = generated["model"]
    laptop_brand = generated["brand"]
    laptop_vendor = generated["vendor"]
    laptop_chipset = generated["chipset"]
    oui = generated["oui"]

    profile_card = format_card(
        f"{badge_laptop('PROFILE')} AUTHENTIC LAPTOP DISGUISE GENERATED",
        [
            ("Laptop Model", c(laptop_model, BOLD, BRIGHT_CYAN)),
            ("Hardware Vendor", c(laptop_vendor, BOLD, WHITE)),
            ("Wi-Fi Chipset", c(laptop_chipset, BRIGHT_YELLOW)),
            ("Authentic OUI", f"{c(oui, BOLD, BRIGHT_MAGENTA)} {DIM}(IEEE Registered, Globally Administered){RESET}"),
            ("New Spoofed MAC", c(spoofed_mac, BOLD, BRIGHT_GREEN)),
        ],
        border_color=BRIGHT_CYAN
    )
    print("\n" + profile_card + "\n")

    log_event(
        f"Selected Laptop Model: '{laptop_model}' | Vendor: '{laptop_vendor}' | "
        f"Chipset: '{laptop_chipset}' | Spoofed MAC: {spoofed_mac}",
        echo=False,
        badge=badge_laptop("SPOOF")
    )

    # 5. Save State
    state_data = {
        "active": True,
        "interface": iface,
        "permanent_mac": perm_mac,
        "spoofed_mac": spoofed_mac,
        "laptop_model": laptop_model,
        "brand": laptop_brand,
        "vendor": laptop_vendor,
        "chipset": laptop_chipset,
        "oui": oui,
        "started_at": datetime.now().isoformat(),
        "daemon_pid": None,
    }
    save_state(state_data)
    log_event(f"Saved active state to {c(STATE_FILE, DIM)}", echo=True, badge=badge_ok("STATE"))

    # 6. Apply Spoofed MAC to Connection Profiles
    log_event("Configuring NetworkManager connection profiles with spoofed MAC...", echo=True, badge=badge_cmd("SETUP"))
    apply_spoofed_mac_to_connections(spoofed_mac, echo=True)

    # 7. Redo WLAN Connection
    log_event(f"Re-applying WLAN connection on interface '{c(iface, BOLD, WHITE)}'...", echo=True, badge=badge_wifi("APPLY"))
    redo_wlan_connection(iface, echo=True)

    # 8. Detach Background Daemon (detaches completely from terminal)
    log_event("Launching detached background daemon...", echo=True, badge=badge_info("DAEMON"))
    daemon_script = os.path.join(PROJECT_DIR, "spoofer_daemon.py")

    with open(LOG_FILE, "a", encoding="utf-8") as log_out:
        daemon_proc = subprocess.Popen(
            [sys.executable, daemon_script],
            stdout=log_out,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,  # Detached from terminal (new session & process group)
            close_fds=True,
        )

    daemon_pid = daemon_proc.pid
    save_daemon_pid(daemon_pid)
    state_data["daemon_pid"] = daemon_pid
    save_state(state_data)
    log_event(f"Daemon process detached in background [{c('PID ' + str(daemon_pid), BOLD, BRIGHT_GREEN)}].", echo=True, badge=badge_ok("DETACH"))

    # Give a brief moment for interface update check
    time.sleep(2)
    after_mac = get_current_mac(iface)
    active_conn = get_active_wifi_connection(iface)
    conn_str = c(active_conn['name'], BOLD, BRIGHT_GREEN) if active_conn else c("Pre-configured (Disconnected)", DIM, BRIGHT_YELLOW)

    success_card = format_card(
        f"{badge_ok('READY')} SPOOFER RUNNING SUCCESSFULLY (DETACHED)",
        [
            ("Wi-Fi Interface", c(iface, BOLD, WHITE)),
            ("Operational MAC", c(after_mac or spoofed_mac, BOLD, BRIGHT_GREEN)),
            ("Disguised Model", c(laptop_model, BOLD, BRIGHT_CYAN)),
            ("Active Network", conn_str),
            ("Daemon Process", f"{badge_active('RUNNING')} {c('PID ' + str(daemon_pid), BOLD, BRIGHT_WHITE)} {DIM}(Independent of terminal){RESET}"),
        ],
        border_color=BRIGHT_GREEN
    )
    print("\n" + success_card + "\n")

    print(f" {c('✔', BOLD, BRIGHT_GREEN)} You may safely close this terminal.")
    print(f" {c('ℹ', BOLD, BRIGHT_CYAN)} The spoofer daemon will persist the spoofed MAC across network switches.")
    print(f" {c('➜', BOLD, BRIGHT_YELLOW)} To restore your original hardware MAC at any time, run: {c('spoofer stop', BOLD, WHITE)}\n")

    return 0


def cmd_stop():
    print_banner("Stopping MAC Address Spoofer", border_color=YELLOW)
    log_event("Command 'spoofer stop' invoked.", badge=badge_cmd("STOP"))

    state = load_state()
    daemon_pid = get_daemon_pid()
    iface = (state.get("interface") if state else None) or get_wifi_interface()
    perm_mac = (state.get("permanent_mac") if state else None) or (get_permanent_mac(iface) if iface else None)

    # 1. Stop background daemon
    if daemon_pid:
        log_event(f"Terminating background daemon process [{c('PID ' + str(daemon_pid), BOLD, BRIGHT_YELLOW)}]...", badge=badge_info("STOP"))
        try:
            os.kill(daemon_pid, signal.SIGTERM)
            for _ in range(15):
                time.sleep(0.2)
                try:
                    os.kill(daemon_pid, 0)
                except OSError:
                    break
            else:
                log_event(f"Daemon [{c('PID ' + str(daemon_pid), BOLD, BRIGHT_RED)}] did not exit gracefully, sending SIGKILL...", badge=badge_warn("KILL"))
                try:
                    os.kill(daemon_pid, signal.SIGKILL)
                except OSError:
                    pass
            log_event(f"Daemon process [{c('PID ' + str(daemon_pid), BOLD, BRIGHT_GREEN)}] terminated cleanly.", badge=badge_ok("DAEMON"))
        except OSError as e:
            log_event(f"Note: Daemon process {daemon_pid} was not running: {e}", badge=badge_warn("DAEMON"))

    # 2. Reset connection profiles in NetworkManager
    log_event("Restoring original MAC address settings in NetworkManager connection profiles...", badge=badge_cmd("RESET"))
    restore_connections_mac(echo=True)

    # 3. Redo WLAN Connection
    if iface:
        log_event(f"Re-applying WLAN connection on interface '{c(iface, BOLD, WHITE)}' to restore hardware MAC...", badge=badge_wifi("RESTORE"))
        redo_wlan_connection(iface, echo=True)

    # 4. Clear state & PID file
    clear_state()
    log_event("Cleared spoofer state and PID files.", badge=badge_ok("CLEANUP"))

    # 5. Check restored MAC
    time.sleep(2)
    curr_mac = get_current_mac(iface) if iface else None

    stop_card = format_card(
        f"{badge_ok('STOPPED')} ORIGINAL HARDWARE MAC RESTORED",
        [
            ("Wi-Fi Interface", c(iface or 'wld0', BOLD, WHITE)),
            ("Restored MAC", c(curr_mac or perm_mac or 'Unknown', BOLD, BRIGHT_GREEN)),
            ("Permanent Hardware", c(perm_mac or 'Unknown', BOLD, WHITE)),
            ("Daemon Process", badge_inactive("STOPPED")),
        ],
        border_color=YELLOW
    )
    print("\n" + stop_card + "\n")
    print(f" {c('✔', BOLD, BRIGHT_GREEN)} Original hardware MAC address is active and spoofer daemon is stopped.\n")

    return 0


def cmd_status():
    state = load_state()
    daemon_pid = get_daemon_pid()
    iface = (state.get("interface") if state else None) or get_wifi_interface()
    curr_mac = get_current_mac(iface) if iface else "Unknown"
    perm_mac = (state.get("permanent_mac") if state else None) or (get_permanent_mac(iface) if iface else "Unknown")
    active_conn = get_active_wifi_connection(iface) if iface else None

    is_active = state and state.get("active", False) and daemon_pid

    border_color = BRIGHT_GREEN if is_active else BRIGHT_CYAN
    status_badge = badge_active("RUNNING (ACTIVE)") if is_active else badge_inactive("STOPPED (INACTIVE)")
    conn_str = c(active_conn['name'], BOLD, BRIGHT_GREEN) if active_conn else c("None (Disconnected)", DIM, YELLOW)

    rows = [
        ("Spoofer Status", status_badge),
        ("Wi-Fi Interface", c(iface or 'None', BOLD, WHITE)),
        ("Current MAC", c(curr_mac, BOLD, BRIGHT_GREEN if is_active else WHITE)),
        ("Permanent MAC", c(perm_mac, DIM, WHITE)),
        ("Active Network", conn_str),
    ]

    if is_active:
        rows.extend([
            ("Disguised Model", c(state.get('laptop_model', 'Unknown'), BOLD, BRIGHT_CYAN)),
            ("Hardware Vendor", c(state.get('vendor', 'Unknown'), WHITE)),
            ("Wi-Fi Chipset", c(state.get('chipset', 'Unknown'), BRIGHT_YELLOW)),
            ("OUI Prefix", c(state.get('oui', 'Unknown'), BOLD, BRIGHT_MAGENTA)),
            ("Started At", c(state.get('started_at', 'Unknown'), DIM)),
            ("Daemon Process", f"{badge_active('RUNNING')} {c('PID ' + str(daemon_pid), BOLD, BRIGHT_WHITE)}"),
        ])
    else:
        rows.append(("Daemon Process", badge_inactive("INACTIVE")))

    card = format_card(
        f"MAC ADDRESS SPOOFER STATUS",
        rows,
        border_color=border_color
    )
    print("\n" + card + "\n")
    return 0


def cmd_logs(lines: int = 40):
    print_banner(f"Spoofer Logs (Last {lines} Lines)", border_color=BRIGHT_MAGENTA)
    if not os.path.exists(LOG_FILE):
        print(f"No log file found at {c(LOG_FILE, DIM)}")
        return 0

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                stripped = line.rstrip()
                # Syntax-highlight log lines based on pattern
                if "RUNNING COMMAND:" in stripped or "➜" in stripped:
                    print(f" {c('⚙', BOLD, BRIGHT_MAGENTA)} {c(stripped, BOLD, BRIGHT_YELLOW)}")
                elif "EXIT CODE: 0" in stripped or "Command succeeded" in stripped or "[✔" in stripped:
                    print(f" {c('✔', BOLD, BRIGHT_GREEN)} {c(stripped, BRIGHT_GREEN)}")
                elif "EXIT CODE:" in stripped or "Command failed" in stripped or "ERROR" in stripped or "[✖" in stripped:
                    print(f" {c('✖', BOLD, BRIGHT_RED)} {c(stripped, BOLD, BRIGHT_RED)}")
                elif "STDOUT:" in stripped or "Output:" in stripped:
                    print(f" {c('│', DIM)} {c(stripped, DIM)}")
                elif stripped.startswith("      "):
                    print(f"   {c(stripped, WHITE)}")
                elif "Selected Laptop Model:" in stripped or "PROFILE" in stripped:
                    print(f" {c('💻', BOLD, BRIGHT_CYAN)} {c(stripped, BRIGHT_CYAN)}")
                elif "Daemon" in stripped:
                    print(f" {c('●', BOLD, BRIGHT_BLUE)} {c(stripped, BRIGHT_BLUE)}")
                elif "Re-applying WLAN" in stripped or "Active connection" in stripped:
                    print(f" {c('📡', BOLD, BRIGHT_CYAN)} {c(stripped, BRIGHT_CYAN)}")
                else:
                    print(f" {c('•', DIM)} {stripped}")
    except Exception as e:
        print(f"{badge_err('ERROR')} Error reading log file: {e}")
    print()
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: spoofer {run|stop|status|logs}")
        print("Commands:")
        print("  spoofer run     - Generate random authentic PC laptop MAC and activate")
        print("  spoofer stop    - Restore original hardware MAC and stop daemon")
        print("  spoofer status  - View current MAC and spoofer state")
        print("  spoofer logs    - View recent logs and executed commands")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd in ("--help", "-h", "help"):
        print("Usage: spoofer {run|stop|status|logs}")
        print("Commands:")
        print("  spoofer run     - Generate random authentic PC laptop MAC and activate")
        print("  spoofer stop    - Restore original hardware MAC and stop daemon")
        print("  spoofer status  - View current MAC and spoofer state")
        print("  spoofer logs    - View recent logs and executed commands")
        sys.exit(0)
    elif cmd in ("run", "start"):
        sys.exit(cmd_run())
    elif cmd == "stop":
        sys.exit(cmd_stop())
    elif cmd == "status":
        sys.exit(cmd_status())
    elif cmd in ("logs", "log"):
        lines = 40
        if len(sys.argv) >= 3 and sys.argv[2].isdigit():
            lines = int(sys.argv[2])
        sys.exit(cmd_logs(lines))
    else:
        print(f"Unknown command: '{cmd}'. Supported: run, stop, status, logs")
        sys.exit(1)


if __name__ == "__main__":
    main()
