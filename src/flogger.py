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
import traceback
import signal
from datetime import datetime, timezone
from pathlib import Path

__version__ = "0.1.0"


def _get_program_name():
    """Get the program name from sys.argv, handling various launch methods."""
    if not sys.argv or not sys.argv[0]:
        return "python"
    
    script_path = sys.argv[0]
    
    # Handle special cases
    if script_path == "-c":
        return "python-c"
    elif script_path == "-":
        return "python-stdin"
    elif script_path.startswith("-"):
        return "python"
    
    # Extract basename and remove .py extension
    program_name = Path(script_path).stem
    return program_name if program_name else "python"


def _get_log_dir(app_name="flogger"):
    """Get platform-appropriate log directory that persists after program exit."""
    if sys.platform == "win32":
        # Windows: LOCALAPPDATA\AppName\logs
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / app_name / "logs"
        else:
            return Path.home() / "AppData" / "Local" / app_name / "logs"
    
    elif sys.platform == "darwin":
        # macOS: ~/Library/Logs/AppName
        return Path.home() / "Library" / "Logs" / app_name
    
    else:
        # Linux/Unix: ~/.local/state/AppName (XDG Base Directory)
        xdg_state = os.environ.get("XDG_STATE_HOME")
        if xdg_state:
            return Path(xdg_state) / app_name
        else:
            return Path.home() / ".local" / "state" / app_name


def _get_log_filename():
    """Generate log filename in format: program.YYYYMMDD-HHMMSS.log"""
    program = _get_program_name()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{program}.{timestamp}.log"


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
    program_name = _get_program_name()
    cmd_parts = [program_name] + sys.argv[1:]
    cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd_parts)
    
    logger.info("Starting: " + " ".join(info_parts) + f" {cmd_str}")


def _setup_abort_handler(logger):
    """Set up signal handlers to log stack traces on abort."""
    def abort_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        stack_trace = ''.join(traceback.format_stack(frame))
        logger.critical("Program exited with %s, stack trace:\n%s", signal_name, stack_trace)
        sys.exit(1)
    
    # Handle common abort signals
    signal.signal(signal.SIGTERM, abort_handler)
    signal.signal(signal.SIGINT, abort_handler)
    if hasattr(signal, 'SIGQUIT'):
        signal.signal(signal.SIGQUIT, abort_handler)


def log_stack_trace(logger, message="", *args):
    """Log a stack trace without exiting."""
    stack_trace = ''.join(traceback.format_stack()[:-1])  # Exclude this call itself
    logger.warning("%sStack trace:\n%s", message % args, stack_trace)


def die(logger, message, *args):
    """Log a fatal message with stack trace and exit."""
    stack_trace = ''.join(traceback.format_stack()[:-1])  # Exclude die() call itself
    logger.critical("%s\nStack trace:\n%s", message % args, stack_trace)
    sys.exit(1)


def get_logger(name=None, include_git=False, auto_abort_trace=True, to_file=True, to_stderr=True):
    """Get a logger with structured formatting.
    
    Args:
        name: Logger name
        include_git: Include git commit in startup log
        auto_abort_trace: Enable automatic stack traces on abort signals
        to_file: Enable file output to platform-appropriate log directory
        to_stderr: Output to stderr (can be combined with to_file)
    """
    logger = logging.getLogger(name)
    
    # Only add handler if not already present
    if not logger.handlers:
        formatter = StructuredFormatter()
        
        if to_file:
            # Create file handler
            log_dir = _get_log_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / _get_log_filename()
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        if to_stderr:
            # Create stderr handler
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setFormatter(formatter)
            logger.addHandler(stderr_handler)
        
        # If neither file nor stderr, default to stdout
        if not to_file and not to_stderr:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setFormatter(formatter)
            logger.addHandler(stdout_handler)
        
        logger.setLevel(logging.INFO)
        
        # Set up automatic abort stack traces
        if auto_abort_trace:
            _setup_abort_handler(logger)
        
        # Log program start info
        _log_program_start(logger, include_git)
        
        # Log file location if logging to file
        if to_file:
            logger.info(f"Logging to {log_file}")
    
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