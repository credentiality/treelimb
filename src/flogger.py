#!/usr/bin/env python3
"""
A formatted logging library with structured output and automatic backtraces.
"""

import logging
import threading
import time
import sys
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

__version__ = "0.1.0"


class StructuredFormatter(logging.Formatter):
    """Custom formatter that produces structured log output."""
    
    LEVEL_MAP = {
        logging.DEBUG: 'D',
        logging.INFO: 'I', 
        logging.WARNING: 'W',
        logging.ERROR: 'E',
        logging.CRITICAL: 'F'
    }
    
    def format(self, record):
        # Get severity level
        level_char = self.LEVEL_MAP.get(record.levelno, 'I')
        
        # Get timestamp with milliseconds and timezone
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        local_dt = dt.astimezone()
        
        # Format timezone offset
        tz_offset = local_dt.strftime('%z')
        timestamp = local_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + tz_offset
        
        # Get thread ID - use 0 for main thread, last 4 digits for others
        current_thread_id = threading.get_ident()
        main_thread_id = threading.main_thread().ident
        thread_id = 0 if current_thread_id == main_thread_id else current_thread_id % 10000
        
        # Get filename and line number
        filename = record.filename
        lineno = record.lineno
        
        # Format the log message
        message = record.getMessage()
        
        return f"{level_char}{timestamp} {thread_id} {filename}:{lineno}] {message}"


def _log_program_start(logger, include_git=False):
    """Log program startup information."""
    # Get main script info
    main_script = sys.argv[0] if sys.argv else "unknown"
    script_path = Path(main_script).resolve()
    
    # Get modification time
    try:
        mtime = datetime.fromtimestamp(script_path.stat().st_mtime)
        mtime_str = mtime.strftime('%Y-%m-%d %H:%M:%S')
    except:
        mtime_str = "unknown"
    
    # Build info message - metadata first
    info_parts = [
        f"pid={os.getpid()}",
        f"modified={mtime_str}",
        f"python={sys.version.split()[0]}"
    ]
    
    # Add git commit if requested
    if include_git:
        try:
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True, timeout=2)
            git_commit = result.stdout.strip() if result.returncode == 0 else None
            if git_commit:
                info_parts.append(f"commit={git_commit}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    # Add command line last (expandable for copy/paste)
    cmd_parts = [str(script_path)] + sys.argv[1:]
    cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd_parts)
    
    logger.info("Starting: " + " ".join(info_parts) + f" {cmd_str}")


def get_logger(name=None, include_git=False):
    """Get a logger with structured formatting."""
    logger = logging.getLogger(name)
    
    # Only add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Log program start info
        _log_program_start(logger, include_git)
    
    return logger


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test flogger formatting")
    parser.add_argument("message", nargs="?", default="hello, world", help="Message to log")
    parser.add_argument("--level", choices=["debug", "info", "warning", "error", "critical"], 
                       default="info", help="Log level")
    parser.add_argument("--git", action="store_true", help="Include git commit in startup log")
    
    args = parser.parse_args()
    
    logger = get_logger("cli", include_git=args.git)
    level_func = getattr(logger, args.level)
    level_func(args.message)