# queuectl/worker/worker_proc.py

"""
Worker Process
---------------
Each worker process polls the database for pending jobs, claims one,
executes it using the executor module, and updates its status.

Responsibilities:
- Select and lock a pending job (so no other worker can take it)
- Execute the job command
- Handle success, retry, or move to DLQ
- Respect graceful shutdown signals
"""

import datetime
import signal
import time
from threading import Event

from queuectl.db.repo import connect
from queuectl.executor import execute_command
from queuectl.utils import utcnow_iso, compute_backoff, log


class Worker:
    def __init__(self, worker_id: int, base_backoff: int = 2):
        self.worker_id = worker_id
        self.conn = connect()
        self.stop_event = Event()
        self.base_backoff = base_backoff

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.handle_stop_signal)
        signal.signal(signal.SIGINT, self.handle_stop_signal)

    def handle_stop_signal(self, signum, frame):
        log(f"Worker-{self.worker_id}: received termination signal")
        self.stop_event.set()

    def claim_next_job(self):
        """
        Find and atomically claim one pending job ready for execution.
        Returns a tuple (job_id, command, attempts, max_retries) or None.
        """
        now = utcnow_iso()
        cur = self.conn.cursor()

        # Find a pending job ready to run
        cur.execute("""
            SELECT id, command, attempts, max_retries
            FROM jobs
            WHERE state='pending' AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
            ORDER BY created_at ASC
            LIMIT 1
        """, (now,))
        job = cur.fetchone()
        if not job:
            return None

        job_id, command, attempts, max_retries = job

        # Try to mark as 'processing' (only if still pending)
        cur.execute("""
            UPDATE jobs
            SET state='processing', updated_at=?
            WHERE id=? AND state='pending'
        """, (utcnow_iso(), job_id))
        self.conn.commit()

        if cur.rowcount == 1:
            return job_id, command, attempts, max_retries
        return None

    def update_job_success(self, job_id: str, attempts: int, output: str):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE jobs
            SET state='completed', attempts=?, updated_at=?, output=?
            WHERE id=?
        """, (attempts + 1, utcnow_iso(), output, job_id))
        self.conn.commit()
        log(f"Worker-{self.worker_id}: job {job_id} completed successfully")

    def update_job_failure(self, job_id: str, attempts: int, max_retries: int,
                           stderr: str, stdout: str):
        attempts += 1
        delay = compute_backoff(self.base_backoff, attempts)
        next_attempt = (datetime.datetime.utcnow() +
                        datetime.timedelta(seconds=delay)).isoformat() + "Z"
        cur = self.conn.cursor()

        if attempts > max_retries:
            # Move to DLQ
            cur.execute("""
                UPDATE jobs
                SET state='dead', attempts=?, updated_at=?, last_error=?, output=?
                WHERE id=?
            """, (attempts, utcnow_iso(), stderr, stdout, job_id))
            log(f"Worker-{self.worker_id}: job {job_id} moved to DLQ")
        else:
            # Schedule retry
            cur.execute("""
                UPDATE jobs
                SET state='failed', attempts=?, updated_at=?, last_error=?, next_attempt_at=?, output=?
                WHERE id=?
            """, (attempts, utcnow_iso(), stderr, next_attempt, stdout, job_id))
            log(f"Worker-{self.worker_id}: job {job_id} failed, retry in {delay}s")

        self.conn.commit()

    def run(self):
        """Main worker loop."""
        log(f"Worker-{self.worker_id}: started")

        while not self.stop_event.is_set():
            job = self.claim_next_job()
            if not job:
                time.sleep(1)
                continue

            job_id, command, attempts, max_retries = job
            log(f"Worker-{self.worker_id}: picked job {job_id} (attempt {attempts + 1})")

            exit_code, stdout, stderr = execute_command(command)

            if exit_code == 0:
                self.update_job_success(job_id, attempts, stdout)
            else:
                self.update_job_failure(job_id, attempts, max_retries, stderr, stdout)

        log(f"Worker-{self.worker_id}: stopping gracefully")
        self.conn.close()
