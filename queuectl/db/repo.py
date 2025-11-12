# queuectl/db/repo.py
import sqlite3
import datetime
from queuectl.db.migrations import init_db

DB_PATH = "queuectl.db"

def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Opens a SQLite connection and ensures schema exists.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    init_db(conn)
    return conn

def insert_job(conn, job):
    """
    Inserts a new job record.
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (id, command, state, attempts, max_retries, created_at, updated_at)
        VALUES (?, ?, 'pending', ?, ?, ?, ?)
    """, (job["id"], job["command"], job.get("attempts", 0), job.get("max_retries", 3), now, now))
    conn.commit()
    print(f"Job {job['id']} inserted.")

def list_jobs(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, command, state, attempts, max_retries FROM jobs")
    for row in cur.fetchall():
        print(row)
