-- qntm.network APP schema — passkey auth + captures (the app skeleton, 2026-07-17).
-- Additive to schema.sql (signups). Apply with:
--   wrangler d1 execute qntm-signups --file=./schema-app.sql            (local)
--   wrangler d1 execute qntm-signups --remote --file=./schema-app.sql   (prod)

-- A person with an account. `handle` is the human label shown at passkey creation.
CREATE TABLE IF NOT EXISTS users (
  id         TEXT PRIMARY KEY,                       -- uuid
  handle     TEXT NOT NULL UNIQUE,                   -- login label (e.g. "luke")
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- A registered passkey (WebAuthn credential). One user may have several (phone, laptop).
CREATE TABLE IF NOT EXISTS credentials (
  id          TEXT PRIMARY KEY,                      -- credential ID (base64url)
  user_id     TEXT NOT NULL REFERENCES users(id),
  public_key  TEXT NOT NULL,                         -- base64url COSE public key
  counter     INTEGER NOT NULL DEFAULT 0,            -- signature counter (clone detection)
  transports  TEXT,                                  -- json array ["internal","hybrid",...]
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_credentials_user ON credentials(user_id);

-- Transient WebAuthn ceremony state — the challenge issued by /options must be verified
-- against the /verify response. Keyed by a random flow id the client echoes back; deleted
-- on verify (single-use) and swept when expired. `handle` is set for registration flows.
CREATE TABLE IF NOT EXISTS webauthn_challenges (
  id         TEXT PRIMARY KEY,                       -- flow id (base64url)
  challenge  TEXT NOT NULL,                          -- base64url challenge
  handle     TEXT,                                   -- pending handle (registration only)
  user_id    TEXT,                                   -- pending user id (registration only)
  expires_at TEXT NOT NULL
);

-- A logged-in session. The token is returned to the client, stored in localStorage, and
-- sent as `Authorization: Bearer <token>` (bearer, not cookie — the app frontend and the
-- Worker API are different origins, so a cross-site cookie would be blocked by Safari/ITP;
-- a same-origin `api.qntm.network` route with a Domain=.qntm.network cookie is the later
-- hardening).
CREATE TABLE IF NOT EXISTS sessions (
  token      TEXT PRIMARY KEY,                       -- random 256-bit, base64url
  user_id    TEXT NOT NULL REFERENCES users(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- The app's atomic gesture: a captured thing you know needs doing. `status` open|done.
-- "The one thing" is DERIVED from these (v1: the oldest still-open capture).
CREATE TABLE IF NOT EXISTS captures (
  id         TEXT PRIMARY KEY,                       -- uuid
  user_id    TEXT NOT NULL REFERENCES users(id),
  text       TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'open',           -- open | done
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  done_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_captures_user_status ON captures(user_id, status, created_at);

-- ── graph hosting (Option A) — see docs/architecture/graph-hosting-plan.md ──
-- The projection engine (qntm-md, local) pushes a rendered snapshot; the browser displays it.
-- Truth stays in the vault. These tables are the cloud half of the stable seam.
--
-- v1 stores the snapshot IN D1 (R2 not enabled on the account). It is split across two tables so
-- no single row nears D1's 1 MB cap: the graph blob in its own row (~712 KB today), each rendered
-- view in its own row (≤60 KB). Only the LATEST version per user is retained (older pruned on
-- push). Swapping to R2 later is behind the /app/graph seam — the browser contract is unchanged.

-- The graph blob + node→location map, one row per pushed version.
CREATE TABLE IF NOT EXISTS graph_snapshots (
  user_id        TEXT NOT NULL REFERENCES users(id),
  version        INTEGER NOT NULL,           -- monotonic per user
  generated_at   TEXT NOT NULL,             -- when qntm-md produced it
  graph_json     TEXT NOT NULL,             -- the graph_state blob {version,nodes,edges}
  locations_json TEXT NOT NULL DEFAULT '{}',-- node_id → {view,line} (empty in v1)
  pushed_at      TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, version)
);

-- One row per rendered view (the rendering of the graph), keyed to the snapshot version.
CREATE TABLE IF NOT EXISTS graph_snapshot_views (
  user_id  TEXT NOT NULL REFERENCES users(id),
  version  INTEGER NOT NULL,
  view_id  TEXT NOT NULL,                    -- e.g. "this-week"
  path     TEXT NOT NULL,                    -- vault-relative output path
  title    TEXT NOT NULL,
  domain   TEXT,
  markdown TEXT NOT NULL,
  PRIMARY KEY (user_id, version, view_id)
);
CREATE INDEX IF NOT EXISTS idx_graph_snapshot_views_ver
  ON graph_snapshot_views(user_id, version);

-- The two-way write queue. A web gesture lands here; the laptop drains it, applies it as the
-- textual vault edit a human would make, re-runs the cycle, and pushes a new snapshot. qntm-md's
-- own reconciliation is the single ingestion path — nothing here writes the graph directly.
CREATE TABLE IF NOT EXISTS graph_edits (
  id                 TEXT PRIMARY KEY,        -- uuid
  user_id            TEXT NOT NULL REFERENCES users(id),
  kind               TEXT NOT NULL,           -- done | reopen | capture | reprioritise
  node_id            TEXT,                    -- target node (null for capture)
  payload_json       TEXT,                    -- gesture-specific data
  status             TEXT NOT NULL DEFAULT 'pending',  -- pending | applied | rejected
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  applied_at         TEXT,
  applied_in_version INTEGER                  -- snapshot version that reflects it
);
CREATE INDEX IF NOT EXISTS idx_graph_edits_user_status
  ON graph_edits(user_id, status, created_at);
