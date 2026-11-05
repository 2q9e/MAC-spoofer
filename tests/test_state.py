"""
Unit tests for state management in state.py.
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch

import state


class TestStateManagement(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.state_file = os.path.join(self.test_dir.name, ".test_state.json")
        self.pid_file = os.path.join(self.test_dir.name, ".test.pid")
        self.log_file = os.path.join(self.test_dir.name, "test.log")

        # Patch paths
        self.orig_state_file = state.STATE_FILE
        self.orig_pid_file = state.PID_FILE
        self.orig_log_file = state.LOG_FILE
        state.STATE_FILE = self.state_file
        state.PID_FILE = self.pid_file
        state.LOG_FILE = self.log_file

    def tearDown(self):
        state.STATE_FILE = self.orig_state_file
        state.PID_FILE = self.orig_pid_file
        state.LOG_FILE = self.orig_log_file
        self.test_dir.cleanup()

    def test_save_and_load_state(self):
        self.assertIsNone(state.load_state())

        data = {
            "active": True,
            "interface": "wld0",
            "permanent_mac": "00:11:22:33:44:55",
            "spoofed_mac": "A4:BB:6D:12:34:56",
            "laptop_model": "Dell XPS 15",
            "daemon_pid": 12345
        }
        state.save_state(data)

        loaded = state.load_state()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["interface"], "wld0")
        self.assertEqual(loaded["spoofed_mac"], "A4:BB:6D:12:34:56")
        self.assertTrue(loaded["active"])

    def test_clear_state(self):
        data = {"active": True}
        state.save_state(data)
        state.save_daemon_pid(99999)

        self.assertTrue(os.path.exists(self.state_file))
        self.assertTrue(os.path.exists(self.pid_file))

        state.clear_state()
        self.assertFalse(os.path.exists(self.state_file))
        self.assertFalse(os.path.exists(self.pid_file))
        self.assertIsNone(state.load_state())

    def test_pid_management(self):
        # Current process PID is guaranteed running
        my_pid = os.getpid()
        state.save_daemon_pid(my_pid)
        retrieved = state.get_daemon_pid()
        self.assertEqual(retrieved, my_pid)

        # Stale/dead PID should return None
        state.save_daemon_pid(99999999)
        self.assertIsNone(state.get_daemon_pid())


if __name__ == "__main__":
    unittest.main()
