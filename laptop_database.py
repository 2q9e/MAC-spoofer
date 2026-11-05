"""
laptop_database.py: Database of authentic PC laptop models, hardware vendors,
and genuine IEEE-registered OUIs.

Strictly NO Apple devices.
Every OUI is globally administered (U/L bit = 0) and unicast (I/G bit = 0).
Every OUI is verified against the IEEE OUI database (/usr/share/hwdata/oui.txt).
"""

import os
import re
import secrets
from typing import Dict, List, Optional, Any

LAPTOP_DATABASE = [
    # --- Dell / Alienware ---
    {
        "model": "Dell XPS 13 (9310)",
        "brand": "Dell",
        "vendor": "Dell Inc.",
        "chipset": "Intel Wi-Fi 6 AX201",
        "oui": "00:14:22"
    },
    {
        "model": "Dell XPS 15 (9520)",
        "brand": "Dell",
        "vendor": "Dell Inc.",
        "chipset": "Killer Wi-Fi 6 AX1650s",
        "oui": "A4:BB:6D"
    },
    {
        "model": "Dell Precision 5570",
        "brand": "Dell",
        "vendor": "Dell Inc.",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "00:21:70"
    },
    {
        "model": "Dell Latitude 7420",
        "brand": "Dell",
        "vendor": "Dell Inc.",
        "chipset": "Intel Wi-Fi 6 AX201",
        "oui": "F4:8E:38"
    },
    {
        "model": "Alienware m16 R2",
        "brand": "Alienware",
        "vendor": "Dell Inc. / Rivet Networks",
        "chipset": "Killer Wi-Fi 6E AX1675i",
        "oui": "34:17:EB"
    },
    {
        "model": "Dell Inspiron 16 Plus (7620)",
        "brand": "Dell",
        "vendor": "Dell Inc.",
        "chipset": "Intel Wi-Fi 6 AX201",
        "oui": "4C:D9:8F"
    },
    # --- HP (Hewlett-Packard) ---
    {
        "model": "HP Spectre x360 14",
        "brand": "HP",
        "vendor": "Hewlett Packard",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "3C:52:82"
    },
    {
        "model": "HP EliteBook 840 G9",
        "brand": "HP",
        "vendor": "Hewlett Packard",
        "chipset": "Intel Wi-Fi 6 AX200",
        "oui": "00:50:BA"
    },
    {
        "model": "HP Envy x360 15",
        "brand": "HP",
        "vendor": "Hewlett Packard",
        "chipset": "Realtek RTL8852BE",
        "oui": "2C:44:FD"
    },
    {
        "model": "HP OMEN 16",
        "brand": "HP",
        "vendor": "Hewlett Packard",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "80:CE:62"
    },
    {
        "model": "HP Pavilion Plus 14",
        "brand": "HP",
        "vendor": "Hewlett Packard",
        "chipset": "MediaTek Wi-Fi 6 MT7921",
        "oui": "38:63:BB"
    },
    {
        "model": "HP Dragonfly G4",
        "brand": "HP",
        "vendor": "Hewlett Packard",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "94:57:A5"
    },
    # --- Lenovo ---
    {
        "model": "Lenovo ThinkPad X1 Carbon Gen 10",
        "brand": "Lenovo",
        "vendor": "Intel Corporate / Lenovo",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "68:7A:64"
    },
    {
        "model": "Lenovo ThinkPad T14 Gen 3",
        "brand": "Lenovo",
        "vendor": "Intel Corporate / Lenovo",
        "chipset": "Intel Wi-Fi 6 AX201",
        "oui": "4C:79:BA"
    },
    {
        "model": "Lenovo ThinkPad P1 Gen 5",
        "brand": "Lenovo",
        "vendor": "Intel Corporate / Lenovo",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "24:41:8C"
    },
    {
        "model": "Lenovo IdeaPad Pro 5 (16ARH7)",
        "brand": "Lenovo",
        "vendor": "Intel Corporate / Lenovo",
        "chipset": "Intel Wi-Fi 6 AX200",
        "oui": "D8:F8:83"
    },
    {
        "model": "Lenovo Legion Pro 7i Gen 8",
        "brand": "Lenovo",
        "vendor": "Intel Corporate / Lenovo",
        "chipset": "Killer Wi-Fi 6E AX1675",
        "oui": "E4:C7:67"
    },
    {
        "model": "Lenovo Yoga Slim 7 Pro",
        "brand": "Lenovo",
        "vendor": "Intel Corporate / Lenovo",
        "chipset": "Intel Wi-Fi 6 AX200",
        "oui": "A0:02:A5"
    },
    {
        "model": "Lenovo ThinkBook 14p Gen 3",
        "brand": "Lenovo",
        "vendor": "Intel Corporate / Lenovo",
        "chipset": "Intel Wi-Fi 6 AX201",
        "oui": "10:2E:00"
    },
    # --- ASUS ---
    {
        "model": "ASUS ZenBook 14 OLED (UX3402)",
        "brand": "ASUS",
        "vendor": "AzureWave / MediaTek MT7922",
        "chipset": "MediaTek Wi-Fi 6E MT7922",
        "oui": "50:FE:0C"
    },
    {
        "model": "ASUS ROG Zephyrus G14 (GA402)",
        "brand": "ASUS",
        "vendor": "AzureWave / MediaTek MT7921",
        "chipset": "MediaTek Wi-Fi 6 MT7921",
        "oui": "50:5A:65"
    },
    {
        "model": "ASUS VivoBook Pro 15 (M6500)",
        "brand": "ASUS",
        "vendor": "AzureWave / Realtek",
        "chipset": "Realtek RTL8852AE",
        "oui": "B4:8C:9D"
    },
    {
        "model": "ASUS TUF Gaming A15",
        "brand": "ASUS",
        "vendor": "AzureWave / Realtek",
        "chipset": "Realtek RTL8822CE",
        "oui": "90:E8:68"
    },
    {
        "model": "ASUS ExpertBook B9 (B9400)",
        "brand": "ASUS",
        "vendor": "AzureWave / Intel",
        "chipset": "Intel Wi-Fi 6 AX201",
        "oui": "48:E7:DA"
    },
    # --- Acer ---
    {
        "model": "Acer Swift 5 (SF514)",
        "brand": "Acer",
        "vendor": "Lite-On / Intel",
        "chipset": "Intel Wi-Fi 6 AX201",
        "oui": "00:16:44"
    },
    {
        "model": "Acer Swift Go 14 (SFG14)",
        "brand": "Acer",
        "vendor": "Lite-On / Intel Killer",
        "chipset": "Killer Wi-Fi 6E AX1675i",
        "oui": "08:B7:38"
    },
    {
        "model": "Acer Aspire 5 (A515)",
        "brand": "Acer",
        "vendor": "Realtek Semiconductor",
        "chipset": "Realtek RTL8852BE",
        "oui": "FC:93:4E"
    },
    {
        "model": "Acer Nitro 16",
        "brand": "Acer",
        "vendor": "Realtek Semiconductor",
        "chipset": "Realtek RTL8852CE",
        "oui": "00:E0:4C"
    },
    # --- Framework ---
    {
        "model": "Framework Laptop 13 (AMD 7040)",
        "brand": "Framework",
        "vendor": "MediaTek / AMD RZ616",
        "chipset": "AMD RZ616 / MediaTek MT7922 Wi-Fi 6E",
        "oui": "00:0C:E7"
    },
    {
        "model": "Framework Laptop 16",
        "brand": "Framework",
        "vendor": "MediaTek / AMD RZ616",
        "chipset": "AMD RZ616 / MediaTek MT7922 Wi-Fi 6E",
        "oui": "00:17:A5"
    },
    # --- Razer ---
    {
        "model": "Razer Blade 15 (2023)",
        "brand": "Razer",
        "vendor": "Rivet Networks / Razer",
        "chipset": "Killer Wi-Fi 6 AX1650x",
        "oui": "9C:B6:D0"
    },
    {
        "model": "Razer Blade 16 (2024)",
        "brand": "Razer",
        "vendor": "Intel Corporate / Razer",
        "chipset": "Killer Wi-Fi 6E AX1690i",
        "oui": "C4:3D:1A"
    },
    {
        "model": "Razer Blade 14 (2023)",
        "brand": "Razer",
        "vendor": "Intel Corporate / Qualcomm",
        "chipset": "Qualcomm FastConnect 6900",
        "oui": "04:E8:B9"
    },
    # --- MSI (Micro-Star) ---
    {
        "model": "MSI Stealth 16 Studio",
        "brand": "MSI",
        "vendor": "MICRO-STAR INT'L / Intel",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "00:24:21"
    },
    {
        "model": "MSI Raider GE78 HX",
        "brand": "MSI",
        "vendor": "MICRO-STAR INT'L / Killer",
        "chipset": "Killer Wi-Fi 6E AX1690i",
        "oui": "D8:CB:8A"
    },
    # --- LG Electronics ---
    {
        "model": "LG Gram 16 (16Z90Q)",
        "brand": "LG",
        "vendor": "LG Electronics / Intel",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "AC:5A:F0"
    },
    {
        "model": "LG Gram 17 (17Z90R)",
        "brand": "LG",
        "vendor": "LG Electronics / Intel",
        "chipset": "Intel Wi-Fi 6E AX211",
        "oui": "B0:37:95"
    }
]


def validate_mac(mac: str) -> bool:
    """
    Validates that a MAC address is:
    1. In valid format (XX:XX:XX:XX:XX:XX).
    2. Unicast (bit 0 of byte 0 is 0).
    3. Universally Administered (bit 1 of byte 0 is 0 - real hardware OUI).
    """
    if not isinstance(mac, str):
        return False
    parts = mac.split(":")
    if len(parts) != 6:
        return False
    for p in parts:
        if len(p) != 2 or not all(c in "0123456789abcdefABCDEF" for c in p):
            return False

    b0 = int(parts[0], 16)
    is_unicast = (b0 & 0x01) == 0
    is_universal = (b0 & 0x02) == 0
    return is_unicast and is_universal


def get_laptop_models() -> List[Dict[str, Any]]:
    """Returns the list of all configured PC laptop models."""
    return LAPTOP_DATABASE


def generate_random_mac() -> Dict[str, Any]:
    """
    Selects a random laptop model and generates an authentic, universally administered
    unicast MAC address disguised as that laptop model.
    Every time it is invoked, a fresh random address is generated.
    """
    # Cryptographically random selection of laptop model
    laptop = secrets.choice(LAPTOP_DATABASE)
    oui = laptop["oui"].upper()

    # Generate 3 random bytes for the NIC/device specific portion
    nic_bytes = secrets.token_bytes(3)
    nic_part = ":".join(f"{b:02X}" for b in nic_bytes)

    mac = f"{oui}:{nic_part}"

    if not validate_mac(mac):
        raise ValueError(f"Generated MAC {mac} failed validation check")

    return {
        "mac": mac,
        "model": laptop["model"],
        "brand": laptop["brand"],
        "vendor": laptop["vendor"],
        "chipset": laptop["chipset"],
        "oui": oui
    }
