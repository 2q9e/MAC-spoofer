"""
State management for spoofer tool.
Stores runtime state, original permanent MAC, spoofed MAC, daemon PID, and timestamps.
"""

import json
import os
from typing import Optional, Dict, Any

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
STATE_FILE = os.path.join(PROJECT_DIR, ".spoofer_state.json")
PID_FILE = os.path.join(PROJECT_DIR, ".spoofer_daemon.pid")
LOG_FILE = os.path.join(PROJECT_DIR, "spoofer.log")


def load_state() -> Optional[Dict[str, Any]]:
    """Loads state from STATE_FILE if it exists and is valid."""
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_state(state: Dict[str, Any]) -> None:
    """Saves state atomically to STATE_FILE."""
    tmp_path = STATE_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_path, STATE_FILE)


def clear_state() -> None:
    """Removes the STATE_FILE and PID_FILE if they exist."""
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
        except OSError:
            pass
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass


def save_daemon_pid(pid: int) -> None:
    """Saves daemon PID to PID_FILE."""
    with open(PID_FILE, "w", encoding="utf-8") as f:
        f.write(str(pid))


def get_daemon_pid() -> Optional[int]:
    """Reads daemon PID from PID_FILE if present and running."""
    if not os.path.exists(PID_FILE):
        return None
    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
        # Check if process is still running
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        return None
