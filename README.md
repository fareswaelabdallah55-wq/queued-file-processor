# queued-file-processor

A small practice project showing how a queued file-processing backend can survive crashes without losing or duplicating results.

This is a personal learning/portfolio project, not production software and not work experience.

## What it shows
- **Transactional outbox:** a job and its outbox event are written in one DB transaction, so one can never exist without the other.
- **Idempotent submit:** the same idempotency key returns the same job.
- **Lease-based retry:** if a worker dies, its lease expires and another worker takes the job.
- **Idempotent results:** results are written with an upsert keyed by job ID, and the job is marked done in the same transaction.
- **Concurrency tests:** 4 workers over 40 jobs give exactly one result each; 8 concurrent identical uploads create one job.
- **CI:** GitHub Actions runs the tests on push.
- **Fault-injection tests:** crash the worker after claim, after processing, and before commit, then assert every job ends with exactly one result.

## Components
- `api.py`: `POST /files` (Idempotency-Key header) returns a job ID; `GET /files/<id>` returns status/result.
- `service.py`: submit, claim with lease, complete (upsert).
- `queue.py`: outbox relay to the queue (re-publish is a no-op).
- `worker.py`: relay + process loop, retries, dead-letter after 3 attempts.

## Limits
Delivery is at-least-once; results are effectively-once inside the database. Side effects on external systems need their own idempotency keys. SQLite stands in for the database and a table stands in for the message broker (no Kafka/SQS/RabbitMQ). The HTTP API is minimal: no auth, no real file storage, processing is a placeholder.

## Demo
    python demo.py

Submits 3 files, crashes a worker mid-job, recovers, and prints one result per job.

## Run
    python -m unittest discover -s tests -v
