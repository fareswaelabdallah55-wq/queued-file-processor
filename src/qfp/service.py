import uuid, time

def submit(db, idem_key, payload):
    """Insert job + outbox event in ONE transaction. Same idem_key returns the same job."""
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("SELECT id FROM jobs WHERE idem_key=?", (idem_key,)).fetchone()
        if row:
            db.execute("COMMIT"); return row[0]
        jid = str(uuid.uuid4())
        db.execute("INSERT INTO jobs(id,idem_key,payload) VALUES(?,?,?)", (jid, idem_key, payload))
        db.execute("INSERT INTO outbox(job_id) VALUES(?)", (jid,))
        db.execute("COMMIT")
        return jid
    except Exception:
        db.execute("ROLLBACK"); raise

def claim(db, lease_seconds=30, now=None, crash=None):
    """Claim a queued job, or one whose lease expired (crashed worker)."""
    now = time.time() if now is None else now
    db.execute("BEGIN IMMEDIATE")
    row = db.execute("SELECT id,payload FROM jobs WHERE status!='done' AND "
                     "(lease_until IS NULL OR lease_until<?) LIMIT 1", (now,)).fetchone()
    if not row:
        db.execute("COMMIT"); return None
    db.execute("UPDATE jobs SET status='running',lease_until=?,attempts=attempts+1 WHERE id=?",
               (now + lease_seconds, row[0]))
    db.execute("COMMIT")
    return row

def process(payload):
    return payload.upper()  # stand-in for real file processing

def complete(db, job_id, output, crash=None):
    """Store result (upsert) and mark done atomically. Safe to re-run."""
    db.execute("BEGIN IMMEDIATE")
    if crash == "before_commit":
        raise SystemExit("injected crash")  # connection closed -> rollback
    db.execute("INSERT INTO results(job_id,output) VALUES(?,?) "
               "ON CONFLICT(job_id) DO UPDATE SET output=excluded.output", (job_id, output))
    db.execute("UPDATE jobs SET status='done',lease_until=NULL WHERE id=?", (job_id,))
    db.execute("COMMIT")

def work_once(db, now=None, crash=None, lease_seconds=30):
    row = claim(db, lease_seconds, now)
    if not row:
        return False
    if crash == "after_claim":
        raise SystemExit("injected crash")
    out = process(row[1])
    if crash == "after_process":
        raise SystemExit("injected crash")
    complete(db, row[0], out, crash)
    return True
