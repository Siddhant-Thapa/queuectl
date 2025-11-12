# queuectl/utils.py
import datetime
import uuid
import math

def utcnow_iso() -> str:
    """Return current UTC time in ISO8601 with 'Z' suffix."""
    return datetime.datetime.utcnow().isoformat()

def generate_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())

def compute_backoff(base: int, attempts: int) -> int:
    """
    Exponential backoff delay.
    Example: base=2, attempts=3 -> 8 seconds
    """
    return int(math.pow(base, attempts))

def pretty_time() -> str:
    """Return local readable timestamp for logs."""
    return datetime.datetime.now().strftime("[%H:%M:%S]")

def log(msg: str):
    """Print a simple timestamped log message."""
    print(f"{pretty_time()} {msg}")
