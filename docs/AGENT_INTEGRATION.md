# Agent integration

MemoryGate has three runtime calls. Your agent wrapper should expose these to
the conversational agent rather than exposing the database CRUD routes.

Two are documented below. The third, `POST /runtime/ask`, retrieves the same
context and has a local model answer from it; it returns 503 when no answer
provider is reachable.

## Retrieve context

`POST /runtime/context`

```json
{
  "query": "What food would fit the user right now?",
  "session_context": "The user said they are hungry before training.",
  "max_items": 12,
  "include_evidence": false
}
```

Headers:

```text
X-MemoryGate-Key: <managed key>
X-Agent-Id: conker
```

The response contains a bounded briefing, ranked memories, matching entities,
episodes, and optionally raw evidence. The agent should treat memories and
entities as primary context. Episodes and evidence are supporting material,
not automatically settled truth.

`session_context` is accepted by the schema but no code path reads it. It is
recorded here so a caller does not assume it influences retrieval.

### Which retrieval path produced the answer

Every response carries a `retrieval` block, and every memory carries the path
that found it:

```json
{
  "retrieval": {
    "mode": "lexical",
    "semantic": {
      "status": "degraded",
      "component": "embeddings",
      "reason": "embedding provider ... is not installed"
    }
  },
  "memories": [{ "retrieval_path": "lexical", "...": "..." }]
}
```

`mode` is `hybrid` when vector search ran and `lexical` when it could not.
When semantic retrieval is degraded the same warning is appended to
`usage.instruction`, so a reading model is told the result set is incomplete
rather than being handed a confident-looking list. **No embedding provider
ships in the API image today**, so `lexical` is the current state - see the
README's "Semantic retrieval is currently degraded".

## Ingest an event

Listeners and the session scraper call `POST /runtime/ingest`:

```json
{
  "source_key": "hermes-session",
  "title": "Conversation message",
  "content": "I always prefer thin-crust pepperoni pizza.",
  "payload": {
    "session_id": "session-123",
    "speaker": "user"
  },
  "tags": ["conversation"],
  "integrity_confidence": 1.0,
  "auto_process": true
}
```

The source must first be configured and enabled in **Sources & Evidence**.
The call creates immutable evidence, groups it into an episode, records the
deterministic analysis, and writes durable memory only when the value filter
finds a strong explicit signal. Every transition receives a lineage link.

## Failure handling

Every automatic run creates a processing job. Failed jobs retain their error,
mark the evidence as quarantined, and can be retried from **Agent Runtime** or
with `POST /runtime/jobs/{job_id}/retry`.

Incorrect source data can be invalidated with
`POST /runtime/evidence/{evidence_id}/invalidate?reason=...`. This preserves
history and drops its outgoing support confidence to zero.

## Recommended boundary

Give your agent access only to the context-query wrapper. Keep ingestion,
retry, invalidation, direct writes, and all admin CRUD routes unavailable to
the agent. Trusted listeners and MemoryGate's operator UI may use the write
routes.
