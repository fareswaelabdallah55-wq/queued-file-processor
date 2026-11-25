import os, sys, json, tempfile, threading, unittest, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from http.server import HTTPServer
from qfp import db as D, queue as Q, service as S, api, worker

class T(unittest.TestCase):
    def test_end_to_end_with_duplicate_upload(self):
        path = os.path.join(tempfile.mkdtemp(), "t.db")
        srv = HTTPServer(("127.0.0.1", 0), api.make_handler(path))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_port}"
        def post(key):
            r = urllib.request.Request(url + "/files", b"hello", {"Idempotency-Key": key}, method="POST")
            return json.load(urllib.request.urlopen(r))["job_id"]
        a, b = post("k1"), post("k1")          # client retry
        self.assertEqual(a, b)
        c = D.connect(path); worker.run(c)
        r = json.load(urllib.request.urlopen(f"{url}/files/{a}"))
        self.assertEqual(r, {"status": "done", "result": "HELLO"})
        srv.shutdown()

    def test_relay_crash_does_not_duplicate_queue(self):
        path = os.path.join(tempfile.mkdtemp(), "t.db")
        c = D.connect(path); Q.init(c); S.submit(c, "k", "x")
        with self.assertRaises(SystemExit): Q.relay_outbox(c, crash="after_publish_before_mark")
        Q.relay_outbox(c)                       # restart: re-publishes safely
        self.assertEqual(c.execute("SELECT count(*) FROM queue").fetchone()[0], 1)

    def test_poison_job_goes_dead(self):
        path = os.path.join(tempfile.mkdtemp(), "t.db")
        c = D.connect(path); Q.init(c); j = S.submit(c, "k", "x")
        orig = S.process; S.process = lambda p: 1/0
        try:
            for t in (0, 100, 200, 300): worker.run(c, lease_seconds=10, now=float(t))
        finally: S.process = orig
        self.assertEqual(c.execute("SELECT status FROM jobs WHERE id=?", (j,)).fetchone()[0], "dead")

if __name__ == "__main__": unittest.main()
