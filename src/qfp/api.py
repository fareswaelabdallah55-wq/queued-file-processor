"""Minimal upload API: POST /files with header Idempotency-Key; GET /files/<job_id>."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from . import db as D, service as S, queue as Q

def make_handler(path):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_POST(self):
            key = self.headers.get("Idempotency-Key")
            if self.path != "/files" or not key:
                return self._send(400, {"error": "POST /files with Idempotency-Key"})
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            c = D.connect(path); Q.init(c)
            self._send(202, {"job_id": S.submit(c, key, body)}); c.close()
        def do_GET(self):
            c = D.connect(path); jid = self.path.rsplit("/", 1)[-1]
            r = c.execute("SELECT j.status,r.output FROM jobs j LEFT JOIN results r ON r.job_id=j.id WHERE j.id=?", (jid,)).fetchone()
            c.close()
            self._send(200, {"status": r[0], "result": r[1]}) if r else self._send(404, {})
        def log_message(self, *a): pass
    return H

def serve(path, port=8000):
    HTTPServer(("", port), make_handler(path)).serve_forever()
