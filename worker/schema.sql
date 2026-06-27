-- qntm.network signups — D1 (SQLite) schema.
CREATE TABLE IF NOT EXISTS signups (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  email      TEXT NOT NULL UNIQUE,            -- dedup: one row per address
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  source     TEXT,                            -- which form / page
  ip         TEXT,                            -- CF-Connecting-IP (coarse abuse signal)
  user_agent TEXT
);
CREATE INDEX IF NOT EXISTS idx_signups_created_at ON signups(created_at);
