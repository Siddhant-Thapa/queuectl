# queuectl/models.py
from dataclasses import dataclass, asdict
from typing import Optional
import datetime

@dataclass
class Job:
    """
    Represents a background job record.
    Mirrors the structure of the 'jobs' table.
    """
    id: str
    command: str
    state: str = "pending"
    attempts: int = 0
    max_retries: int = 3
    created_at: str = datetime.datetime.utcnow().isoformat() + "Z"
    updated_at: str = datetime.datetime.utcnow().isoformat() + "Z"
    next_attempt_at: Optional[str] = None
    last_error: Optional[str] = None
    output: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_row(row):
        """Convert a DB row (tuple) into a Job instance."""
        keys = [
            "id", "command", "state", "attempts", "max_retries",
            "created_at", "updated_at", "next_attempt_at", "last_error", "output"
        ]
        return Job(**dict(zip(keys, row)))
