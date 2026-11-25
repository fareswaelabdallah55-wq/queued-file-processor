import time
from . import queue as Q, service as S

MAX_ATTEMPTS = 3

def run(db, lease_seconds=30, now=None):
    """Relay outbox, then process jobs. Jobs failing MAX_ATTEMPTS times go to 'dead'."""
    Q.relay_outbox(db)
    while True:
        try:
            if not S.work_once(db, now=now, lease_seconds=lease_seconds):
                return
        except Exception:
            pass  # job stays leased; retried after lease expiry
        db.execute("UPDATE jobs SET status='dead' WHERE attempts>=? AND status!='done'", (MAX_ATTEMPTS,))

if __name__ == "__main__":
    import sys
    from . import db as D
    c = D.connect(sys.argv[1])
    while True:
        run(c); time.sleep(1)
