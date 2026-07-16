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
