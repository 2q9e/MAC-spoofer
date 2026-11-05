# MAC Address Spoofer (`spoofer`)

A robust, production-grade Linux MAC address privacy utility that disguises your device as an authentic PC laptop (Dell, Alienware, HP, Lenovo, ASUS, Acer, Framework, Razer, MSI, LG) by assigning genuine IEEE-registered vendor OUIs (globally administered unicast addresses) and rotating addresses on demand.

## Features

- **Command Prefix**: `spoofer`
- **Commands**:
  - `spoofer run`: Generates a new random authentic PC laptop MAC, configures NetworkManager, re-applies the WLAN connection, and detaches a background daemon.
  - `spoofer stop`: Restores the permanent hardware MAC address, stops the daemon, and reconnects WLAN.
  - `spoofer status`: Displays current MAC, permanent MAC, active connection, disguised model, and daemon health.
  - `spoofer logs`: Displays real-time command execution logs and NetworkManager event history.
- **Authentic PC Laptop Hardware OUIs**:
  - Curated database of 35+ popular laptop models across Dell, Alienware, HP, Lenovo, ASUS, Acer, Framework, Razer, MSI, and LG.
  - Every OUI is verified against the official IEEE OUI registry (`/usr/share/hwdata/oui.txt`).
  - **Strictly NO Apple devices**.
  - Always uses globally administered unicast format (bits 0 and 1 unset), blending into enterprise and public networks as a genuine PC laptop rather than being flagged as a locally administered randomized MAC.
- **Terminal Independence**:
  - Once started, the spoofer detaches into a background daemon (`spoofer_daemon.py`). You can close the terminal at any time without terminating protection.
- **Dynamic Network Persistence & Edge Cases**:
  - **Pre-Connection Protection**: Works even before connecting to any network. The tool configures connection profiles and stands by; as soon as any Wi-Fi network associates, the spoofed MAC is applied.
  - **Network Switching**: The background daemon monitors NetworkManager events via `nmcli monitor` and automatically configures newly added or switched Wi-Fi profiles to ensure the spoofed MAC persists across different networks.
- **Full Transparency & Auditing**:
  - Every executed command, exit code, stdout, and stderr are printed in real-time and recorded in `spoofer.log`.

## Usage

```bash
# Start spoofer and generate a new random authentic laptop MAC
spoofer run

# Check current status and hardware details
spoofer status

# View recent command logs
spoofer logs

# Restore original permanent hardware MAC and stop daemon
spoofer stop
```

## Architecture

- `spoofer.py`: Main CLI entry point.
- `spoofer_daemon.py`: Detached background daemon monitoring NetworkManager events.
- `laptop_database.py`: Verified IEEE OUI database and random MAC generator.
- `network_manager.py`: NetworkManager integration and command runner with full execution logging.
- `state.py`: Atomic state persistence and PID tracking.
- `tests/`: Automated unit and integration test suite.
