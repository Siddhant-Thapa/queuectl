# queuectl/cli.py

"""
QueueCTL CLI
------------
Command-line interface for managing the job queue system.

Supports:
- Enqueue new jobs
- Start/stop workers
- List jobs by state
- View or retry DLQ jobs
- Show system status
"""

import argparse
import json
import os
import signal
import sys

from queuectl.db.repo import connect, insert_job
from queuectl.utils import generate_id
from queuectl.worker.manager import WorkerManager


def cmd_enqueue(args):
    """Handle 'enqueue' command."""
    conn = connect()
    try:
        job_data = json.loads(args.job_json)
        if "id" not in job_data:
            job_data["id"] = generate_id()
        if "command" not in job_data:
            print("Error: job must contain a 'command' field.")
            return
        insert_job(conn, job_data)
    except json.JSONDecodeError:
        print("Invalid JSON format for job data.")


def cmd_worker_start(args):
    """Start worker processes."""
    count = args.count or 1
    mgr = WorkerManager(worker_count=count)
    mgr.start()


def cmd_worker_stop(args):
    """Stop running workers using the PID file."""
    from queuectl.pidfile import read_pidfile, remove_pidfile

    pidfile = "queuectl_worker.pid"
    pid = read_pidfile(pidfile)
    if not pid:
        print("No active worker manager found.")
        return

    try:
        os.kill(pid, signal.SIGTERM)
        remove_pidfile(pidfile)
        print(f"Sent stop signal to manager (PID {pid}).")
    except ProcessLookupError:
        print("Manager process not found (already stopped).")
    except Exception as e:
        print(f"Error stopping manager: {e}")


def cmd_list(args):
    """List jobs by state."""
    conn = connect()
    state_filter = args.state
    cur = conn.cursor()

    if state_filter:
        cur.execute("SELECT id, command, state, attempts, max_retries FROM jobs WHERE state=?", (state_filter,))
    else:
        cur.execute("SELECT id, command, state, attempts, max_retries FROM jobs")

    rows = cur.fetchall()
    if not rows:
        print("No jobs found.")
        return

    print(f"{'ID':36} | {'STATE':10} | {'ATTEMPTS':8} | COMMAND")
    print("-" * 80)
    for job_id, command, state, attempts, max_retries in rows:
        print(f"{job_id:36} | {state:10} | {attempts:8} | {command}")


def cmd_dlq_list(args):
    """List all dead jobs."""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, command, last_error FROM jobs WHERE state='dead'")
    rows = cur.fetchall()

    if not rows:
        print("No jobs in DLQ.")
        return

    print(f"{'ID':36} | COMMAND | LAST ERROR")
    print("-" * 80)
    for job_id, command, error in rows:
        print(f"{job_id:36} | {command} | {error}")


def cmd_dlq_retry(args):
    """Retry a job from DLQ."""
    conn = connect()
    job_id = args.job_id
    cur = conn.cursor()

    cur.execute("""
        UPDATE jobs
        SET state='pending', 
        attempts=0, 
        next_attempt_at=NULL, 
        last_error=NULL, 
        updated_at=datetime('now')
        WHERE id=? AND state='dead'
    """, (job_id,))
    conn.commit()

    if cur.rowcount > 0:
        print(f"Job {job_id} moved back to pending queue.")
    else:
        print(f"No DLQ job found with id {job_id}.")


def cmd_status(args):
    """Display summary of job states."""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT state, COUNT(*) FROM jobs GROUP BY state")
    rows = cur.fetchall()
    if not rows:
        print("No jobs found.")
        return

    print("Queue Status:")
    for state, count in rows:
        print(f"  {state:10}: {count}")


def build_parser():
    parser = argparse.ArgumentParser(prog="queuectl", description="Background Job Queue System CLI")

    subparsers = parser.add_subparsers(dest="command")

    # enqueue
    p_enqueue = subparsers.add_parser("enqueue", help="Add a new job to the queue")
    p_enqueue.add_argument("job_json", help="Job data in JSON format")
    p_enqueue.set_defaults(func=cmd_enqueue)

    # worker
    p_worker = subparsers.add_parser("worker", help="Manage workers")
    worker_sub = p_worker.add_subparsers(dest="subcommand")

    p_start = worker_sub.add_parser("start", help="Start worker processes")
    p_start.add_argument("--count", type=int, default=1, help="Number of workers to start")
    p_start.set_defaults(func=cmd_worker_start)

    p_stop = worker_sub.add_parser("stop", help="Stop all workers")
    p_stop.set_defaults(func=cmd_worker_stop)

    # list
    p_list = subparsers.add_parser("list", help="List jobs by state")
    p_list.add_argument("--state", type=str, help="Filter by job state")
    p_list.set_defaults(func=cmd_list)

    # dlq
    p_dlq = subparsers.add_parser("dlq", help="Dead Letter Queue operations")
    dlq_sub = p_dlq.add_subparsers(dest="subcommand")

    p_dlq_list = dlq_sub.add_parser("list", help="List DLQ jobs")
    p_dlq_list.set_defaults(func=cmd_dlq_list)

    p_dlq_retry = dlq_sub.add_parser("retry", help="Retry a DLQ job")
    p_dlq_retry.add_argument("job_id", help="Job ID to retry")
    p_dlq_retry.set_defaults(func=cmd_dlq_retry)

    # status
    p_status = subparsers.add_parser("status", help="Show system summary")
    p_status.set_defaults(func=cmd_status)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
