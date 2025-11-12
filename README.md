# QueueCTL — CLI-Based Background Job Queue System

QueueCTL is a **Python-based background job queue system** that manages asynchronous command execution through worker processes. It provides a **command-line interface (CLI)** to enqueue jobs, run multiple workers in parallel, automatically retry failed jobs with **exponential backoff**, and maintain a **Dead Letter Queue (DLQ)** for permanently failed jobs.

All job data is stored **persistently in SQLite**, surviving restarts.

## Tech Stack

- **Language:** Python 3.11 or higher
- **Database:** SQLite (local persistent storage)
- **Concurrency:** `multiprocessing`
- **CLI Framework:** `argparse`
- **OS Compatibility:** Windows, macOS, Linux

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Siddhant-Thapa/queuectl.git
cd queuectl
```

### 2. Create and activate a virtual environment (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install QueueCTL as a CLI command (optional but recommended)

```bash
pip install -e .
```

This enables you to run the `queuectl` command globally instead of using `python -m queuectl`.

## Usage Examples

> ⚠️ **Windows PowerShell Note:** Always include `--%` before JSON input to prevent argument parsing issues.

### Enqueue a job

```powershell
queuectl enqueue --% "{\"command\": \"timeout /T 2\"}"
```

**Output:**
```
Database schema initialized successfully.
Job 1c23b86a-b7a9-4ac1-9cbb-78a4b8c93fa3 inserted.
```

### Start workers

```powershell
queuectl worker start --count 2
```

**Output:**
```
Manager: starting 2 workers (pid 12345)
Manager: spawned worker pid=23456
Manager: spawned worker pid=23457
[12:30:01] Worker-1: started
[12:30:01] Worker-1: picked job 1c23b86a-… (attempt 1)
[12:30:03] Worker-1: job 1c23b86a-… completed successfully
```

### Stop workers

```powershell
queuectl worker stop
```

### List all jobs

```powershell
queuectl list
```

**Output:**
```
ID                                   | STATE      | ATTEMPTS | COMMAND
--------------------------------------------------------------------------------
1c23b86a-b7a9-4ac1-9cbb-78a4b8c93fa3 | completed  |        1 | timeout /T 2
```

### List jobs by state

```powershell
queuectl list --state failed
```

### Check DLQ and retry jobs

```powershell
queuectl dlq list
queuectl dlq retry <job-id>
```

### Show system status

```powershell
queuectl status
```

**Output:**
```
Queue Status:
  pending    : 0
  processing : 0
  completed  : 5
  failed     : 1
  dead       : 1
```

## Architecture Overview

### High-Level Design

```
+---------------------+
|  queuectl (CLI)     |  <-- enqueue, list, worker, dlq, status
+---------------------+
          |
          v
+---------------------+
|  SQLite Database    |  <-- persistent job storage (jobs table)
+---------------------+
          |
          v
+---------------------+
|  Worker Manager     |  <-- spawns and monitors workers
+---------------------+
          |
          v
+---------------------+
|  Worker Processes   |  <-- executes jobs, retries, DLQ handling
+---------------------+
```

### Data Persistence

SQLite (`queuectl.db`) stores:
- Job state (pending, processing, completed, failed, dead)
- Retry counts and timestamps
- Command output and errors

All job data survives restarts — workers resume unprocessed jobs automatically.

### Job Lifecycle

| State | Description |
|-------|-------------|
| `pending` | Waiting to be picked up by a worker |
| `processing` | Currently being executed |
| `completed` | Successfully executed |
| `failed` | Failed but will retry automatically |
| `dead` | Permanently failed (moved to DLQ) |

### Worker Flow

1. Poll database for pending or retryable failed jobs
2. Atomically claim one job (state='processing')
3. Execute command via subprocess
4. Update job status:
   - ✅ Success → `completed`
   - ❌ Failure → increment attempt + exponential backoff delay
   - ☠️ Retries exhausted → `dead` (DLQ)

### Retry / Backoff Logic

```
delay = base_backoff ^ attempts
```

Example: `base_backoff = 2` → delays 2s, 4s, 8s, …

## Assumptions & Trade-offs

| Design Decision | Rationale |
|----------------|-----------|
| SQLite | Lightweight, ACID-compliant, persists data without extra services |
| argparse CLI | Built-in module, no external dependencies |
| multiprocessing workers | True concurrency; no GIL limitation |
| Persistent workers | Long-running processes that keep polling for jobs |
| Manual stop | Matches production worker behavior; avoids unexpected exit |
| Windows timeout instead of Unix sleep | Cross-platform compatibility during testing |

### Simplifications:
- Logs printed to stdout (not files)
- Single SQLite database instead of a queue broker

## Testing Instructions

### Functional Scenarios

| Test | Command | Expected Outcome |
|------|---------|------------------|
| Basic job | `queuectl enqueue --% "{\"command\": \"timeout /T 2\"}"` | Job completes successfully |
| Invalid job | `queuectl enqueue --% "{\"command\": \"nonexistent_command\"}"` | Retries 3 times → DLQ |
| DLQ retry | `queuectl dlq retry <job-id>` | Job moves to pending and runs again |
| Multiple workers | `queuectl worker start --count 3` | Jobs executed concurrently |
| Restart | Stop and restart workers | Pending/failed jobs persist |

### Verification Steps

1. Run a few enqueue commands
2. Start 2 workers
3. Observe logs for job processing, retries, and DLQ
4. Verify job states with `queuectl list`
5. Retry a DLQ job and check that it re-runs

### Example Output Summary

```
[01:53:17] Worker-1: picked job ... (attempt 1)
[01:53:19] Worker-1: job ... failed, retry in 2s
[01:53:23] Worker-1: job ... failed, retry in 4s
[01:53:31] Worker-1: job ... moved to DLQ
```

## Project Structure

```
queuectl/
├── queuectl/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── executor.py
│   ├── models.py
│   ├── pidfile.py
│   ├── utils.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── migrations.py
│   │   └── repo.py
│   └── worker/
│       ├── __init__.py
│       ├── manager.py
│       └── worker_proc.py
├── test_db.py
├── test_executor.py
├── test_manager.py
├── test_utils.py
├── test_worker.py
├── setup.py
├── .gitignore
└── README.md
```

---

**Author:** Siddhant Thapa  
**Environment:** Python 3.13 on Windows  
**Project:** QueueCTL Backend Developer Internship Assignment