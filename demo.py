"""Run: python demo.py  -- submits files, kills a worker mid-job, recovers, prints results."""
import os, sys, tempfile
sys.path.insert(0, "src")
from qfp import db as D, queue as Q, service as S, worker
path = os.path.join(tempfile.mkdtemp(), "demo.db")
c = D.connect(path); Q.init(c)
ids = [S.submit(c, f"upload-{i}", f"file {i}") for i in range(3)]
try: S.work_once(c, now=0.0, crash="after_process")
except SystemExit: print("worker crashed after processing, before commit")
c.close(); c = D.connect(path)
worker.run(c, now=100.0)
for r in c.execute("SELECT job_id,output FROM results"): print(r)
print("jobs:", len(ids), "results:", c.execute("SELECT count(*) FROM results").fetchone()[0])
