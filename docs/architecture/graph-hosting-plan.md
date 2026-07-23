# Hosting the graph — v1 plan (Option A)

**Goal.** See the qntm-md graph rendered, hosted, private, and two-way — from the app.
Not the source notes: the *rendering of the graph* (`render = f(graph_state, view_config)`),
which qntm-md already produces as view files (`this_week.md`, `daily.md`, …).

**Decision (settled).** Private (existing passkey). Vault stays the single source of truth;
web edits queue and are re-derived. Whole graph, all ~60 views. The projection engine runs on
the **laptop** for v1 and pushes results up — the same architecture as "render on a server",
wired at its first deployment point.

---

## The two engines and the seam

- **Projection engine** — `graph_state + view_config → view`. qntm-md (Python), local. Unchanged.
- **Display engine** — `view → pixels`. `app/render/renderer.ts` (markdown-it), in the browser. Reused as-is.

Between them, one **stable contract**:

> *A rendered snapshot + the graph JSON, fetched behind the passkey session.*

The browser doesn't know or care **where** the snapshot was produced. That is what lets the
projection engine slide laptop → server later with **zero browser change**.

```
LAPTOP (projection)                CLOUD (existing stack)            BROWSER (existing app)
qntm-md run                        Cloudflare Worker + D1 + R2       passkey login  (done)
  ├─ graph_state.json  ──push──►   POST /app/graph   (operator key)  GET /app/graph
  ├─ rendered views/*.md ─push──►    blob → R2, pointer → D1   ────► MarkdownRenderer.toHtml()
  └─ node→location map ──push──►                                      paints all ~60 views
                                                                       + freshness banner
  ┌─◄── GET /app/edits/pending ──   graph_edits queue (D1)      ◄──── [done] [capture] gestures
  └─ apply as vault edits           POST /app/edit   (session)         → POST /app/edit (queued)
     → qntm-md run → re-push
```

---

## What crosses the wire (the snapshot envelope)

Versioned so the browser can detect staleness and the producer is swappable:

```jsonc
{
  "ok": true,
  "handle": "luke",
  "snapshot": {
    "version": 42,                 // monotonic per user
    "generated_at": "2026-07-23T…",// when qntm-md produced it
    "views": [                     // the RENDERING of the graph — qntm-md output
      { "id": "this-week", "path": "this_week.md", "title": "This Week", "markdown": "…" },
      … all ~60 …
    ],
    "graph": { "nodes": [ … ], "edges": [ … ] },  // the graph_state blob, rides along
    "locations": {                 // node_id → where it renders (from qntm-md line_cache)
      "<node-uuid>": { "view": "this-week", "line": 12 }
    }
  },
  "pending_edits": 3               // queued web gestures not yet in this version
}
```

`graph` + `locations` ride along so interactivity attaches to **real node IDs** later
(progressive enhancement), not to scraped HTML.

---

## Storage

Payload is ~1 MB and grows (1,482 nodes today). Keep D1 for metadata + the edit queue;
put the blob in **R2** (object storage) behind a pointer row. Clean, and dodges D1 row-size limits.

Additive to `worker/schema-app.sql`:

```sql
-- Pointer to a pushed projection snapshot (payload lives in R2).
CREATE TABLE IF NOT EXISTS graph_snapshots (
  user_id      TEXT NOT NULL REFERENCES users(id),
  version      INTEGER NOT NULL,            -- monotonic per user
  r2_key       TEXT NOT NULL,               -- e.g. "graph/<user>/<version>.json"
  generated_at TEXT NOT NULL,               -- when qntm-md produced it
  pushed_at    TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, version)
);

-- Two-way write queue. Web gestures land here; the laptop drains them.
CREATE TABLE IF NOT EXISTS graph_edits (
  id                 TEXT PRIMARY KEY,       -- uuid
  user_id            TEXT NOT NULL REFERENCES users(id),
  kind               TEXT NOT NULL,          -- done | reopen | capture | reprioritise
  node_id            TEXT,                   -- target node (null for capture)
  payload_json       TEXT,                   -- gesture-specific data
  status             TEXT NOT NULL DEFAULT 'pending',  -- pending | applied | rejected
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  applied_at         TEXT,
  applied_in_version INTEGER                 -- snapshot version that reflects it
);
CREATE INDEX IF NOT EXISTS idx_graph_edits_user_status
  ON graph_edits(user_id, status, created_at);
```

R2 binding in `worker/wrangler.toml`:

```toml
[[r2_buckets]]
binding = "GRAPH"
bucket_name = "qntm-graph"
```

---

## Worker routes (mirror the `app.js` pattern)

All session-gated except the operator push/pull (headless laptop → dedicated key, like `EXPORT_KEY`).

| Route | Auth | Does |
|---|---|---|
| `GET  /app/graph` | session | latest pointer → read R2 → return envelope + `pending_edits` count |
| `POST /app/graph` | operator `GRAPH_PUSH_KEY` | write blob to R2, insert pointer (version+1), mark drained edits `applied_in_version` |
| `POST /app/edit` | session | enqueue one gesture into `graph_edits` |
| `GET  /app/edits/pending` | operator `GRAPH_PUSH_KEY` | return pending gestures for the laptop to apply |

`GRAPH_PUSH_KEY` maps to your `user_id` (set via `wrangler secret put`). Swapping the laptop
for a hosted producer later = a new caller of the **same** two operator routes; nothing else moves.

---

## Laptop wrapper — `scripts/graph-sync.mjs`

One loopable command: **pull → apply → run → push.**

1. **Pull** `GET /app/edits/pending`.
2. **Apply** each gesture as the *textual vault edit a human would make* — because qntm-md's cycle
   already round-trips edits made to its rendered views back into the graph
   (`filesystem_reconciliation → content_diff → parse → apply`, via `line_cache`/`applier.py`).
   Using `locations` (node_id → view+line):
   - `done`   → tick the checkbox on that line in the view file
   - `reopen` → untick it
   - `capture`→ append a line to `inbox.md`
   - `reprioritise` → edit the priority marker on the line
   This keeps **one** ingestion path (qntm-md's existing reconciliation) — no new apply code in qntm-md.
3. **Run** `qntm-md run` — graph updates, all views re-render.
4. **Push** `POST /app/graph`: read `graph_state.data`, read the rendered view files, build
   `locations` from the render/line cache, upload the envelope.

Drive it however suits: manual, launchd, or appended to your existing cycle. Snapshot is fresh
after each run; the freshness banner + `pending_edits` count make the lag honest in the UI.

---

## Browser (app.html + app/)

1. After passkey login, `GET /app/graph`.
2. View switcher (sidebar/tabs over the ~60 views, grouped) → paint the selected view's markdown
   with the **existing** `MarkdownRenderer.toHtml()`.
3. Freshness banner: "as of `generated_at` · N edits queued".
4. **Progressive enhancement** (two-way): using `graph` + `locations`, make checkboxes/priority
   controls live → optimistic UI → `POST /app/edit`. No full structural editing in v1 — just the
   narrow gestures qntm-md ingests cleanly.

---

## Build order

1. **Contract + storage** — envelope shape; `graph_snapshots` + `graph_edits` in `schema-app.sql`;
   R2 bucket + binding.
2. **Worker routes** — the four above, mirroring `handleApp`.
3. **`graph-sync` push** — laptop → R2 (read-only site works end-to-end here).
4. **Browser display** — view switcher + freshness banner (read-only).
5. **Two-way** — clickable gestures → `/app/edit`; `graph-sync` pull+apply loop.

## The seam, restated (why this isn't throwaway)

The browser talks only to `GET /app/graph` + `POST /app/edit`. The **producer** of snapshots is
behind the operator key. Moving projection to an always-on server later means: host qntm-md (or a
thin HTTP layer over `qntm_graph`), point it at the same two operator routes. Browser unchanged,
D1/R2 unchanged, one renderer throughout. Option A **is** the proper setup at deployment point #1.
