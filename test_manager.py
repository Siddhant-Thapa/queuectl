# test_manager.py
from queuectl.worker.manager import WorkerManager

def main():
    manager = WorkerManager(worker_count=2)
    manager.start()

if __name__ == "__main__":
    main()
