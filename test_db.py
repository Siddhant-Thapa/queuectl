# test_db.py
from queuectl.db.repo import connect, insert_job, list_jobs

conn = connect()

insert_job(conn, {
    "id": "job1",
    "command": "echo Hello QueueCTL",
    "attempts": 0,
    "max_retries": 3
})

list_jobs(conn)
