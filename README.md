# treelimb

Sets up Python standard logging with some essentials.  Loosely inspired by Google's glog.

## Example Output

```
I2025-05-30 14:32:15.123-0700 0 example.py:42] Starting: pid=12345 modified=2025-05-30 14:30:12 python=3.11.2 commit=f38ea87 example.py
I2025-05-30 14:32:15.124-0700 0 example.py:42] Logging to /home/user/.local/state/treelimb/example.20250530-143215.log
I2025-05-30 14:32:15.125-0700 0 example.py:15] Processing user data
W2025-05-30 14:32:15.126-0700 0 example.py:18] Invalid input detected
E2025-05-30 14:32:15.127-0700 1234 worker.py:25] Connection failed
F2025-05-30 14:32:15.128-0700 0 example.py:30] Fatal error occurred
Stack trace:
  File "example.py", line 30, in main
    die(logger, "Fatal error occurred")
```

## Features

* **No external dependencies**
* **Logs program metadata** - On startup, logs git commit, modification time, Python version, and command line
* **Backtraces on abort** - Automatic stack traces when program receives SIGTERM, SIGINT, or SIGQUIT
* **File:line and thread ID** - Shows source location and thread (0 for main thread)
* **Sortable by severity** - Sorting entries alphabetically groups by level (DEBUG, ERROR, FATAL, INFO, WARNING) then timestamp
* **Logs to stderr+file by default** - Simultaneous output to console and persistent log files

## Quick Examples

### Command Line

You can run the module directly from the command line to try it out.

```bash
$ src/treelimb.py "hello, world"
I2025-05-30 14:32:15.123-0700 0 treelimb.py:255] Starting: pid=12345 modified=2025-05-30 14:30:12 python=3.11.2 treelimb hello, world
I2025-05-30 14:32:15.124-0700 0 treelimb.py:255] Logging to /home/user/.local/state/treelimb/treelimb.20250530-143215.log
I2025-05-30 14:32:15.125-0700 0 treelimb.py:255] hello, world

$ src/treelimb.py --level warning "something went wrong"
I2025-05-30 14:32:15.123-0700 0 treelimb.py:255] Starting: pid=12349 modified=2025-05-30 14:30:12 python=3.11.2 treelimb --level warning "something went wrong"
I2025-05-30 14:32:15.124-0700 0 treelimb.py:255] Logging to /home/user/.local/state/treelimb/treelimb.20250530-143215.log
W2025-05-30 14:32:15.125-0700 0 treelimb.py:255] something went wrong

$ src/treelimb.py --log-dir /tmp/logs "custom location"
I2025-05-30 14:32:15.123-0700 0 treelimb.py:255] Starting: pid=12350 modified=2025-05-30 14:30:12 python=3.11.2 treelimb --log-dir /tmp/logs "custom location"
I2025-05-30 14:32:15.124-0700 0 treelimb.py:255] Logging to /tmp/logs/treelimb.20250530-143215.log
I2025-05-30 14:32:15.125-0700 0 treelimb.py:255] custom location
```

### In Your Program

```python
import treelimb

# Default behavior - logs to platform-appropriate directory
logger = treelimb.get_logger()
logger.info("Application started")

# Or use a custom log directory
logger = treelimb.get_logger(log_dir="/var/log/myapp")
logger.warning("This is a warning")

# Log stack trace without exiting
treelimb.log_stack_trace(logger, "Debug checkpoint")

# Log fatal error with stack trace and exit
treelimb.die(logger, "Something went wrong: %s", error_msg)
```

## API Reference

### `get_logger(name=None, include_git=False, auto_abort_trace=True, to_file=True, to_stderr=True, log_dir=None)`

Get a logger with structured formatting.

**Parameters:**
- `name` (str, optional): Logger name
- `include_git` (bool): Include git commit in startup log (default: False)
- `auto_abort_trace` (bool): Enable automatic stack traces on abort signals (default: True)
- `to_file` (bool): Enable file output to platform-appropriate log directory (default: True)
- `to_stderr` (bool): Output to stderr (default: True)
- `log_dir` (str, optional): Custom directory for log files (overrides platform defaults)

**Returns:** Logger instance

### `log_stack_trace(logger, message="", *args)`

Log a stack trace without exiting the program.

**Parameters:**
- `logger`: Logger instance
- `message` (str): Optional message to include
- `*args`: Arguments for message formatting

### `die(logger, message, *args)`

Log a fatal message with stack trace and exit with code 1.

**Parameters:**
- `logger`: Logger instance  
- `message` (str): Fatal error message
- `*args`: Arguments for message formatting

### `get_log_file(logger)`

Get the active log file path for a logger.

**Parameters:**
- `logger`: Logger instance created with `get_logger()`

**Returns:** Path object of log file, or None if not logging to file

## Thread ID Handling

treelimb displays thread identifiers in log messages to help track multi-threaded execution:

- **Main thread**: Displays as `0`
- **Other threads**: Shows the last 4 digits of the thread ID

This approach keeps thread identification compact while still distinguishing between different threads in your application.

## Log File Locations

By default, treelimb automatically creates log files in platform-appropriate directories:

- **Linux**: `~/.local/state/treelimb/`
- **macOS**: `~/Library/Logs/treelimb/`  
- **Windows**: `%LOCALAPPDATA%\treelimb\logs\`

You can override this behavior by specifying a custom directory:

```python
# API usage
logger = treelimb.get_logger(log_dir="/path/to/custom/logs")

# CLI usage  
python -m treelimb --log-dir /path/to/custom/logs "message"
```

Log files are named: `{program}.{YYYYMMDD-HHMMSS}.log`
