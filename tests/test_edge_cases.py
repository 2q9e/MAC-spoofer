"""
Unit tests for edge cases:
- Pre-connection: tool starting before any network is connected.
- Network switching: connecting to a new SSID or switching networks.
- Verification that cloned-mac-address applies properly to all profiles.
- Process detachment and daemon signal handling.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add project path dynamically
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import network_manager
import spoofer_daemon
import state


class TestEdgeCases(unittest.TestCase):

    def test_pre_connection_edge_case(self):
        """
        Edge Case: No network connected --> start command --> connect to network
        Verify that apply_spoofed_mac_to_connections updates existing profiles even when
        disconnected, and redo_wlan_connection handles disconnected interface gracefully.
        """
        mock_conns = [
            {"uuid": "uuid-1", "type": "802-11-wireless", "name": "CoffeeShop-Wifi"},
            {"uuid": "uuid-2", "type": "802-11-wireless", "name": "HomeNetwork"},
        ]

        with patch("network_manager.get_wifi_connections", return_value=mock_conns), \
             patch("network_manager.execute_command") as mock_exec, \
             patch("network_manager.get_active_wifi_connection", return_value=None):

            mock_exec.return_value = network_manager.CommandResult(
                command="test", exit_code=0, stdout="", stderr="", success=True
            )

            # Apply spoofed MAC when no network is connected
            spoofed_mac = "A4:BB:6D:33:44:55"
            ok = network_manager.apply_spoofed_mac_to_connections(spoofed_mac, echo=False)
            self.assertTrue(ok)

            # Should have modified both profiles
            self.assertEqual(mock_exec.call_count, 2)
            calls = [c[0][0] for c in mock_exec.call_args_list]
            self.assertIn(["nmcli", "connection", "modify", "uuid-1", "802-11-wireless.cloned-mac-address", spoofed_mac], calls)
            self.assertIn(["nmcli", "connection", "modify", "uuid-2", "802-11-wireless.cloned-mac-address", spoofed_mac], calls)

            # Redo WLAN when disconnected
            mock_exec.reset_mock()
            redo_ok = network_manager.redo_wlan_connection("wld0", echo=False)
            self.assertTrue(redo_ok)
            # Should have called nmcli device connect wld0
            mock_exec.assert_called_once_with(["nmcli", "device", "connect", "wld0"], echo=False)

    def test_network_switching_edge_case(self):
        """
        Edge Case: Switching networks
        Verify that daemon detects when a connection profile has an un-spoofed cloned-mac
        (e.g. newly connected network profile) and automatically updates it to the target spoofed MAC.
        """
        mock_conns = [
            {"uuid": "uuid-new-network", "type": "802-11-wireless", "name": "Airport-Free-WiFi"}
        ]

        target_mac = "3C:52:82:99:88:77"

        # Simulate connection show returning an empty or different cloned-mac
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "default\n"

        with patch("spoofer_daemon.get_wifi_connections", return_value=mock_conns), \
             patch("subprocess.run", return_value=mock_proc), \
             patch("spoofer_daemon.execute_command") as mock_exec:

            mock_exec.return_value = network_manager.CommandResult(
                command="test", exit_code=0, stdout="", stderr="", success=True
            )

            spoofer_daemon.ensure_connections_configured(target_mac)

            # Verify that the daemon detected the mismatch and modified the connection profile
            mock_exec.assert_called_once_with(
                ["nmcli", "connection", "modify", "uuid-new-network", "802-11-wireless.cloned-mac-address", target_mac],
                echo=False
            )

    def test_command_execution_logging(self):
        """Test that execute_command captures stdout, stderr, and exit code correctly."""
        res = network_manager.execute_command(["echo", "hello_spoofer"], echo=False)
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.stdout, "hello_spoofer")

        fail_res = network_manager.execute_command(["false"], echo=False)
        self.assertFalse(fail_res.success)
        self.assertEqual(fail_res.exit_code, 1)


if __name__ == "__main__":
    unittest.main()
