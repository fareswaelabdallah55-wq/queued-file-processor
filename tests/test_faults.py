import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from qfp import db as D, service as S

def fresh():
    return D.connect(os.path.join(tempfile.mkdtemp(), "t.db")), None

def run_with_crash(path, crash):
    c = D.connect(path)
    try:
        S.work_once(c, now=1000.0, crash=crash, lease_seconds=30)
    except SystemExit:
        pass
    c.close()  # simulates process death: open transaction rolls back

class Faults(unittest.TestCase):
    def check(self, crash):
        path = os.path.join(tempfile.mkdtemp(), "t.db")
        c = D.connect(path)
        ids = [S.submit(c, f"k{i}", f"file{i}") for i in range(3)]
        c.close()
        run_with_crash(path, crash)               # worker dies mid-job
        c = D.connect(path)
        while S.work_once(c, now=2000.0):         # lease expired, others retry
            pass
        rows = c.execute("SELECT job_id FROM results").fetchall()
        self.assertEqual(sorted(r[0] for r in rows), sorted(ids))  # none lost, none duplicated
        self.assertEqual(c.execute("SELECT count(*) FROM jobs WHERE status!='done'").fetchone()[0], 0)

    def test_crash_after_claim(self): self.check("after_claim")
    def test_crash_after_process(self): self.check("after_process")
    def test_crash_before_commit(self): self.check("before_commit")

    def test_duplicate_submit_is_idempotent(self):
        c, _ = fresh()
        a = S.submit(c, "same", "x"); b = S.submit(c, "same", "x")
        self.assertEqual(a, b)
        self.assertEqual(c.execute("SELECT count(*) FROM outbox").fetchone()[0], 1)

    def test_rerun_complete_does_not_duplicate(self):
        c, _ = fresh()
        j = S.submit(c, "k", "x")
        S.complete(c, j, "X"); S.complete(c, j, "X")
        self.assertEqual(c.execute("SELECT count(*) FROM results").fetchone()[0], 1)

if __name__ == "__main__":
    unittest.main()
