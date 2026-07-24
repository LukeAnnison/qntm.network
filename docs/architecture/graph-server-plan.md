# Hosting the graph on a proper server — plan

**The correction that reframed this:** the **graph is the source of truth**; the vault markdown is a
**regenerable projection** (a view). This is not aspiration — qntm-md is *explicitly* strict MVC:
`architecture.yaml` states *"Graph state is the single canonical MODEL. Files are VIEWS."* and
*"The graph IS the truth; files are f(graph_state, filter)."* Verified against the code:
`rm`-ing a view file re-renders it from the graph next cycle; an invariant guarantees *"file
deletion cannot delete graph nodes by construction."* There is **no source-vs-view file class**
(the old `is_projection_file` coupling was deleted in the one-universe pivot). So hosting the model
is *hosting*, not surgery — nothing to untangle.

(One caveat to know, never to rely on: deleting a file re-projects; *emptying* a file — leaving a
blank file on disk — is read as authorial line-removal and deletes those nodes. `rm` safe; blank not.)

## Architecture (locked)

```
   THE MODEL   ─►  FLY.IO: qntm-md (Python) + state.db + vault  (the truth, hosted, backed up)
   (the graph)     run_cycle · projects views · ingests deltas
                        ▲  private (Fly internal networking / shared token)
   THE EDGE    ─►  CF Worker: passkey auth ── proxy            (reuse the login already built)
                        ▲  GET /app/graph · POST /app/edit  (browser contract UNCHANGED)
   THE VIEWS   ─►  website │ laptop vault │ other computer      (all displays of the one model)
```

- **Model + engine on Fly.** The graph already persists as a clean JSON blob (`graph_state`, <1 MB)
  in `state.db`; the 970 MB on disk is rebuildable cache, not truth. Back up = back up the blob.
- **CF Worker stays the front door.** It authenticates (passkey) and proxies to the private Fly
  service. The Python box never faces the public internet directly.
- **R2 not needed.** The projection is served live from the Fly volume. The D1 snapshot path becomes
  an optional offline/cache mirror, not the source.

## Phasing (each ships something real)

1. **Model on the server — read path.** Containerise qntm-md; put `state.db` + vault + bundle config
   on a Fly volume; expose `GET /graph` (graph_state + rendered views). Worker's `GET /app/graph`
   proxies to Fly instead of reading D1. → *graph hosted on a proper server; website works with the
   laptop off.*
2. **Write path.** `POST /edit` on Fly writes the gesture as a vault delta → `run_cycle` → re-project.
   Worker's `POST /app/edit` proxies through. → *two-way from the website against the hosted model.*
3. **Laptop + other-com become clients.** "Run cycle here" ships the local vault delta up, triggers
   the server cycle, pulls the projection back. Other-com = same client. → *one model, many windows.*

## Phase 1 build (in progress)

- **`server/`** (Python): a thin FastAPI over qntm-md — `GET /health`, `GET /graph` (read
  `graph_state` + view files → the same envelope `graph-sync` produces), `POST /cycle` (run a cycle).
  Auth: a shared bearer token the Worker holds (server stays private).
- **`Dockerfile`**: install qntm-md + `qntm_graph` + `qntm_rule_engine` from the monorepo, plus the
  API. (Exact build strategy pending the packaging investigation — uv workspace vs vendored source.)
- **`fly.toml`**: one app, one small machine, a persistent **volume** mounting `/data` = vault +
  state.db + bundle config. Seed the volume with the current `state.db` (the live 1,482-node model).
- **Worker change**: `GET /app/graph` proxies to Fly (keep D1 read as a fallback).

## You-do-it steps (auth I can't complete)

- `fly auth login` — opens a browser; only you can complete it. (flyctl already installed at
  `~/.fly/bin/fly`.) After that I can `fly launch` / `fly deploy` / create the volume.
- Nothing else — no R2, no dashboard.

## Open ops detail (decided or deferred)

- **Where the service code lives** — monorepo (`~/projects/qntm/apps/…`, clean uv-workspace home) vs
  this repo's `server/` installing qntm-md from git. Decided by the packaging facts (pending).
- **Secrets** — a `SERVER_TOKEN` shared between the Worker (proxy caller) and the Fly service.
- **Backups** — periodic dump of `graph_state` (tiny) off the volume; the crown jewel.
