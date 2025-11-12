# test_worker.py
from queuectl.worker.worker_proc import Worker
from queuectl.db.repo import connect, insert_job
from queuectl.utils import generate_id

# Prepare a test job
conn = connect()
insert_job(conn, {
    "id": generate_id(),
    "command": "echo WorkerTest",
    "attempts": 0,
    "max_retries": 2
})

# Run one worker for a few seconds
worker = Worker(worker_id=1)
worker.run()
