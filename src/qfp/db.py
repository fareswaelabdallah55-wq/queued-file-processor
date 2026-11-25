import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs(
  id TEXT PRIMARY KEY,
  idem_key TEXT UNIQUE NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  lease_until REAL,
  attempts INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS outbox(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  published INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS results(
  job_id TEXT PRIMARY KEY,
  output TEXT NOT NULL);
"""

def connect(path):
    c = sqlite3.connect(path, isolation_level=None, timeout=10)
    c.executescript(SCHEMA)
    return c
