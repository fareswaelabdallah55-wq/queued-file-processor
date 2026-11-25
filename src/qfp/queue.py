"""Tiny durable queue (SQLite table) standing in for a broker, plus the outbox relay."""
SCHEMA = """CREATE TABLE IF NOT EXISTS queue(
  id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, outbox_id INTEGER UNIQUE NOT NULL);"""

def init(db): db.executescript(SCHEMA)

def relay_outbox(db, crash=None):
    """Publish unpublished outbox rows to the queue. At-least-once; outbox_id UNIQUE
    makes a re-publish after a crash a no-op, so the consumer never sees duplicates."""
    n = 0
    for oid, jid in db.execute("SELECT id,job_id FROM outbox WHERE published=0").fetchall():
        db.execute("INSERT OR IGNORE INTO queue(job_id,outbox_id) VALUES(?,?)", (jid, oid))
        if crash == "after_publish_before_mark":
            raise SystemExit("injected crash")
        db.execute("UPDATE outbox SET published=1 WHERE id=?", (oid,))
        n += 1
    return n
