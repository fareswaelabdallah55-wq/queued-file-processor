import os, sys, tempfile, threading, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from qfp import db as D, queue as Q, service as S, worker

class Concurrent(unittest.TestCase):
    def test_many_workers_one_result_per_job(self):
        path = os.path.join(tempfile.mkdtemp(), "t.db")
        c = D.connect(path); Q.init(c)
        ids = [S.submit(c, f"k{i}", f"f{i}") for i in range(40)]
        def go():
            w = D.connect(path); worker.run(w)
        ts = [threading.Thread(target=go) for _ in range(4)]
        [t.start() for t in ts]; [t.join() for t in ts]
        rows = c.execute("SELECT job_id FROM results").fetchall()
        self.assertEqual(sorted(r[0] for r in rows), sorted(ids))
        self.assertEqual(c.execute("SELECT count(*) FROM queue").fetchone()[0], 40)

    def test_concurrent_duplicate_submits_make_one_job(self):
        path = os.path.join(tempfile.mkdtemp(), "t.db")
        D.connect(path)
        out = []
        def go(): out.append(S.submit(D.connect(path), "same", "x"))
        ts = [threading.Thread(target=go) for _ in range(8)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertEqual(len(set(out)), 1)

if __name__ == "__main__": unittest.main()
