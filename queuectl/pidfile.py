# queuectl/pidfile.py

"""
PID File Utility
----------------
Provides simple helpers for writing, reading, and removing
PID files used by the worker manager.
"""

import os

def write_pidfile(path: str, pid: int):
    with open(path, "w") as f:
        f.write(str(pid))

def read_pidfile(path: str) -> int:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None

def remove_pidfile(path: str):
    if os.path.exists(path):
        os.remove(path)
