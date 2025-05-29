#!/usr/bin/env python3
"""
Simple regression tests for flogger.
"""

import unittest
import sys
import os

from src import flogger


class TestFlogger(unittest.TestCase):

    def test_basic_logging(self):
        """Test that basic logging produces expected format."""
        logger = flogger.get_logger("test", to_stderr=False)
        logger.info("test message")
        
        # Get the log file and read its contents
        log_file = flogger.get_log_file(logger)
        self.assertIsNotNone(log_file)
        
        with open(log_file, 'r') as f:
            output = f.read()
        
        self.assertIn("test message", output)
        self.assertIn("test_flogger.py:", output)
        self.assertIn(" 0 ", output)  # main thread
        self.assertIn("Starting:", output)
        self.assertIn("Logging to", output)
        
        # Clean up
        os.unlink(log_file)

    def test_log_stack_trace(self):
        """Test that log_stack_trace includes stack trace."""
        logger = flogger.get_logger("test_stack", to_stderr=False)
        flogger.log_stack_trace(logger, "debug point")
        
        # Get the log file and read its contents
        log_file = flogger.get_log_file(logger)
        self.assertIsNotNone(log_file)
        
        with open(log_file, 'r') as f:
            output = f.read()
        
        self.assertIn("debug point", output)
        self.assertIn("Stack trace:", output)
        self.assertIn("test_log_stack_trace", output)
        
        # Clean up
        os.unlink(log_file)

    def test_die_exits(self):
        """Test that die() calls sys.exit."""
        logger = flogger.get_logger("test_die")
        
        with self.assertRaises(SystemExit) as cm:
            flogger.die(logger, "fatal error (not really, just testing)")
        
        self.assertEqual(cm.exception.code, 1)

    def test_message_formatting(self):
        """Test that message % args works correctly."""
        logger = flogger.get_logger("test_format", to_stderr=False)
        flogger.log_stack_trace(logger, "value is %d", 42)
        
        # Get the log file and read its contents
        log_file = flogger.get_log_file(logger)
        self.assertIsNotNone(log_file)
        
        with open(log_file, 'r') as f:
            output = f.read()
        
        self.assertIn("value is 42", output)
        
        # Clean up
        os.unlink(log_file)


if __name__ == "__main__":
    unittest.main()
