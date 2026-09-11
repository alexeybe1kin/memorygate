# Changelog

Versions are the module's own, not an API revision. A change to the shape of any
endpoint is a contract change and gets its own entry - replacing a module has to be
a decision with visible consequences.

## Unreleased

- Bootstrap read-key configuration now only seeds missing authority. Existing
  revocations, agent assignments, labels and credential changes survive restart;
  renaming a revoked key cannot create an active copy of the same credential.

- Add scoped, idempotent Pi conversation ingestion with atomic source/analysis/memory
  lineage, durable deletion tombstones and retryable vector work.
- Admit ordinary Russian preferences at the same threshold as English, including
  short statements; preserve source attribution, dates and uncertainty in context.
- Follow direct conversation lineage on source invalidation; unsupported memories
  leave active retrieval. Flush changed support links before checking remaining support.
- Include conversation receipts in logical backups and expose index lag in retrieval.



## 0.2.0

Two defects made MemoryGate untrustworthy in opposite directions: it authenticated
nobody, and it answered retrieval questions with noise. Both are fixed by making the
service refuse to run in a state it cannot honestly serve, and by reporting degradation
instead of hiding it.

### Contract changes

- `GET /health` now runs real probes against PostgreSQL, Qdrant and the embedding
  provider. It returns `{status, service, degraded[], dependencies{}, age_seconds}`
  instead of a hardcoded `{"status": "ok"}`. Probe detail is coarse because the route is
  unauthenticated; results are cached for five seconds and carry their age.
- `POST /runtime/context` and `POST /memory/search` gained a `retrieval` block
  (`mode`, `semantic.{status,component,reason}`), and every returned memory gained
  `retrieval_path` (`semantic` or `lexical`). `/runtime/context` also states the
  degradation inside `usage.instruction`, which is the text a reading model sees.
- Write responses (`/memory/write`, `/memory/{id}` PATCH, `/entity/create`,
  `/entity/update`, `/observation/create`) gained an optional `indexing` object, present
  only when the row was committed but could not be added to the vector index.
  `/memory/write` also gained `novelty_check` when the near-duplicate check could not run,
  and entity/observation creation gained `dedup` for the same reason. Processing job
  results carry `indexing` on the same terms.
- `GET /auth/check` no longer returns the tier `disabled`; there is no unauthenticated
  tier left to report.

### Security

- **The service refuses to start with no admin key configured.** `verify_admin_key()`
  used to return `True` when neither `MEMORYGATE_ADMIN_KEY` nor a database-managed key
  existed, and the stock compose file set neither - so a freshly composed instance served
  every route, including `POST /system/memory-reset`, to anything that could reach the
  port. Startup now fails with an error naming the exact fix, and the check itself fails
  closed regardless. An environment key must be at least 16 characters.
- **CORS no longer defaults to `*`.** The default is the bundled dashboard's own origins.
  `MEMORYGATE_CORS_ORIGINS=*` remains available as a documented development override and
  logs a warning at startup.
- `POST /system/memory-reset` keeps its `RESET MEMORY` phrase, now compared in constant
  time through one shared helper and covered by a test proving a valid admin key alone is
  not sufficient.

### Retrieval

- **`EMBED_MODEL=hash` is removed.** It derived every vector component from
  `sha256(index:text)`, so near-identical sentences produced uncorrelated vectors and
  cosine similarity over them was noise. `embed_text()` now raises `EmbeddingUnavailable`
  rather than returning a plausible-looking vector, and callers fall back to lexical
  retrieval while saying so.
- The bare `except Exception` around vector search in `_build_context` is gone. The
  retrieval path is chosen from an explicit status check, so a degraded answer is labelled
  as one instead of being indistinguishable from a healthy one.

### Reliability

- A vector-index or embedding failure after a successful Postgres commit no longer
  returns 500 with the row already written. `index_after_commit()` reports the failure
  and the caller surfaces it.
- The API starts when Qdrant is unreachable instead of crash-looping, and re-attempts
  collection creation on first use so it heals once the index returns.
- `services/api/app/services/qdrant_stub.py`, which nothing imported, is deleted.

### Repository

- Added `.env.example` and `services/api/requirements-dev.txt`; the README documents
  creating the external `conker_net` network and running the test suite.
- Fixed a test that leaked a SQLite handle and failed only on Windows.

- F10: Refuse direct hosted generation without a shared-budget adapter; audit its estimated or unknown cost and expose blocked_budget in runtime status.

- F7: Report unverified Qdrant collections as degraded with the collection and failure class.
