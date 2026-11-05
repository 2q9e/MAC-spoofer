"""
Unit tests for laptop_database.py.
Verifies all 30+ PC laptop models, OUI validity against IEEE database,
unicast and universally administered properties, randomness, and strict NO Apple compliance.
"""

import unittest
import os
import re
from laptop_database import (
    LAPTOP_DATABASE,
    get_laptop_models,
    generate_random_mac,
    validate_mac,
)

OUI_DB_PATH = "/usr/share/hwdata/oui.txt"


class TestLaptopDatabase(unittest.TestCase):

    def test_database_size(self):
        """Ensure database has at least 30 PC laptop models."""
        models = get_laptop_models()
        self.assertGreaterEqual(len(models), 30, "Database should contain at least 30 laptop models")

    def test_strict_no_apple(self):
        """Ensure strictly NO Apple devices, vendors, or models are present."""
        models = get_laptop_models()
        for item in models:
            for key, val in item.items():
                self.assertNotIn("apple", val.lower(), f"Apple detected in {item}")
                self.assertNotIn("macbook", val.lower(), f"MacBook detected in {item}")

    def test_all_ouis_globally_administered_and_unicast(self):
        """
        Verify that all OUIs are:
        - Unicast (bit 0 of first byte is 0)
        - Universally Administered (bit 1 of first byte is 0)
        - Second hex digit must be one of 0, 4, 8, C
        """
        models = get_laptop_models()
        for item in models:
            oui = item["oui"]
            self.assertEqual(len(oui.split(":")), 3, f"OUI should be 3 bytes: {oui}")
            b0 = int(oui.split(":")[0], 16)
            self.assertEqual(b0 & 0x01, 0, f"OUI {oui} must be unicast (bit 0 == 0)")
            self.assertEqual(b0 & 0x02, 0, f"OUI {oui} must be universally administered (bit 1 == 0)")
            second_digit = oui[1].upper()
            self.assertIn(second_digit, ["0", "4", "8", "C"], f"Second hex digit of {oui} must be 0, 4, 8, or C")

    def test_ouis_exist_in_ieee_database(self):
        """Verify that every OUI prefix exists in the real IEEE OUI database (/usr/share/hwdata/oui.txt)."""
        if not os.path.exists(OUI_DB_PATH):
            self.skipTest(f"{OUI_DB_PATH} not found on this system")

        with open(OUI_DB_PATH, "r", encoding="utf-8", errors="ignore") as f:
            oui_text = f.read()

        models = get_laptop_models()
        for item in models:
            oui = item["oui"]
            dash_format = oui.replace(":", "-").upper()
            self.assertIn(dash_format, oui_text, f"OUI {oui} ({dash_format}) not found in {OUI_DB_PATH}")

    def test_generate_random_mac(self):
        """Verify generate_random_mac returns a valid profile with fresh random MACs."""
        generated_macs = set()
        for _ in range(25):
            res = generate_random_mac()
            mac = res["mac"]
            self.assertTrue(validate_mac(mac), f"Generated MAC {mac} is not valid")
            self.assertIn("model", res)
            self.assertIn("vendor", res)
            self.assertIn("chipset", res)
            self.assertIn("oui", res)
            self.assertTrue(mac.startswith(res["oui"]))
            generated_macs.add(mac)

        # Every generation should produce distinct random MACs
        self.assertEqual(len(generated_macs), 25, "Random MACs should not collide in 25 samples")

    def test_validate_mac_edge_cases(self):
        """Verify validate_mac correctly rejects invalid, multicast, or locally administered addresses."""
        # Valid globally administered unicast
        self.assertTrue(validate_mac("A4:BB:6D:12:34:56"))
        self.assertTrue(validate_mac("00:14:22:AA:BB:CC"))
        self.assertTrue(validate_mac("3C:52:82:FE:DC:BA"))

        # Multicast (bit 0 = 1) -> Must reject
        self.assertFalse(validate_mac("01:00:5E:00:00:01"))
        self.assertFalse(validate_mac("FF:FF:FF:FF:FF:FF"))

        # Locally administered (bit 1 = 1) -> Must reject
        self.assertFalse(validate_mac("A2:11:43:FA:14:53"))
        self.assertFalse(validate_mac("02:14:22:AA:BB:CC"))
        self.assertFalse(validate_mac("06:14:22:AA:BB:CC"))
        self.assertFalse(validate_mac("0A:14:22:AA:BB:CC"))
        self.assertFalse(validate_mac("0E:14:22:AA:BB:CC"))

        # Malformed
        self.assertFalse(validate_mac("invalid"))
        self.assertFalse(validate_mac("A4:BB:6D:12:34"))
        self.assertFalse(validate_mac("A4:BB:6D:12:34:56:78"))
        self.assertFalse(validate_mac("ZZ:BB:6D:12:34:56"))


if __name__ == "__main__":
    unittest.main()
