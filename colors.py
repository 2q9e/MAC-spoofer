"""
colors.py: Terminal styling and color utilities for spoofer.
Provides ANSI colors, formatting badges, banners, and ANSI stripping for clean log files.
"""

import re
import sys

# ANSI Escape Sequences
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Standard Colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright Colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# Backgrounds
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"

ANSI_REGEX = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    """Removes ANSI color/formatting escape codes from text."""
    return ANSI_REGEX.sub("", text)


def supports_color() -> bool:
    """Checks if stdout supports color."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def c(text: str, *styles: str) -> str:
    """Applies styles to text if supported, then resets."""
    prefix = "".join(styles)
    return f"{prefix}{text}{RESET}"


# Status Badges
def badge_ok(text: str = "OK") -> str:
    return f"{BOLD}{BRIGHT_GREEN}[✔ {text}]{RESET}"


def badge_err(text: str = "ERROR") -> str:
    return f"{BOLD}{BRIGHT_RED}[✖ {text}]{RESET}"


def badge_warn(text: str = "WARN") -> str:
    return f"{BOLD}{BRIGHT_YELLOW}[⚠ {text}]{RESET}"


def badge_info(text: str = "INFO") -> str:
    return f"{BOLD}{BRIGHT_CYAN}[ℹ {text}]{RESET}"


def badge_cmd(text: str = "CMD") -> str:
    return f"{BOLD}{BRIGHT_MAGENTA}[⚙ {text}]{RESET}"


def badge_wifi(text: str = "WIFI") -> str:
    return f"{BOLD}{BRIGHT_BLUE}[📡 {text}]{RESET}"


def badge_laptop(text: str = "LAPTOP") -> str:
    return f"{BOLD}{BRIGHT_CYAN}[💻 {text}]{RESET}"


def badge_active(text: str = "ACTIVE") -> str:
    return f"{BOLD}{GREEN}● {text}{RESET}"


def badge_inactive(text: str = "INACTIVE") -> str:
    return f"{BOLD}{RED}○ {text}{RESET}"


def format_card(title: str, rows: list, border_color: str = CYAN) -> str:
    """
    Renders a neat terminal card with aligned key-value rows.
    rows is a list of (label, value_str) tuples.
    """
    width = 72
    top = f"{border_color}┌{'─' * (width - 2)}┐{RESET}"
    bottom = f"{border_color}└{'─' * (width - 2)}┘{RESET}"

    clean_title = strip_ansi(title)
    padding = max(0, width - 4 - len(clean_title))
    header = f"{border_color}│{RESET} {BOLD}{title}{RESET}{' ' * padding} {border_color}│{RESET}"
    divider = f"{border_color}├{'─' * (width - 2)}┤{RESET}"

    lines = [top, header, divider]
    for label, val in rows:
        label_styled = f"{BOLD}{WHITE}{label:<19}{RESET}"
        content = f"{label_styled}: {val}"
        clean_content = strip_ansi(content)
        content_pad = max(0, width - 4 - len(clean_content))
        lines.append(f"{border_color}│{RESET}  {content}{' ' * content_pad} {border_color}│{RESET}")

    lines.append(bottom)
    return "\n".join(lines)
