# queuectl/worker/manager.py

"""
Worker Manager (subprocess-based)
--------------------------------
Spawns independent python processes for workers using subprocess.Popen.
This avoids Windows multiprocessing pickling issues and is cross-platform.
"""

import os
import signal
import subprocess
import sys
import time
from typing import List

from queuectl.pidfile import write_pidfile, remove_pidfile


class WorkerManager:
    def __init__(self, worker_count: int = 1, pidfile: str = "queuectl_worker.pid"):
        self.worker_count = worker_count
        self.pidfile = pidfile
        self.children: List[subprocess.Popen] = []
        self._stopping = False

    def _signal_handler(self, signum, frame):
        print("Manager: termination signal received")
        self._stopping = True

    def start(self):
        print(f"Manager: starting {self.worker_count} workers (pid {os.getpid()})")
        write_pidfile(self.pidfile, os.getpid())

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        python = sys.executable
        module = "queuectl.worker.worker_proc"

        # Spawn worker processes
        for i in range(self.worker_count):
            args = [python, "-m", module, "--worker-id", str(i + 1)]
            # subprocess.Popen will start independent processes
            p = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr)
            self.children.append(p)
            print(f"Manager: spawned worker pid={p.pid}")

        try:
            while not self._stopping:
                # If all children exited, break
                if not any(p.poll() is None for p in self.children):
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            self._stopping = True
        finally:
            self.stop_children()
            remove_pidfile(self.pidfile)
            print("Manager: stopped")

    def stop_children(self):
        print("Manager: stopping workers...")
        for p in self.children:
            if p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        # Wait for graceful shutdown
        timeout = 5
        deadline = time.time() + timeout
        for p in self.children:
            try:
                remaining = max(0, deadline - time.time())
                p.wait(timeout=remaining)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass


if __name__ == "__main__":
    # Example direct run
    mgr = WorkerManager(worker_count=2)
    mgr.start()
