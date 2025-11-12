# test_utils.py
from queuectl.utils import utcnow_iso, generate_id, compute_backoff
from queuectl.models import Job

print("UTC Now:", utcnow_iso())
print("Random ID:", generate_id())
print("Backoff (base=2, attempts=3):", compute_backoff(2, 3))

job = Job(id="job123", command="echo Hello Step2")
print("Job dict:", job.to_dict())
