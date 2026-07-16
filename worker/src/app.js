// The qntm app skeleton — capture, and surface THE ONE THING.
// Every route requires a valid bearer session. "The one thing" is DERIVED (not stored):
// v1 = the oldest still-open capture — the thing you've known needed doing the longest.
// (prioritization-is-derived — sharpen the heuristic later without a data migration.)

import { json, getSession, uuid } from "./util.js";

async function loadState(env, userId, handle) {
  const rows = await env.DB.prepare(
    `SELECT id, text, created_at FROM captures
      WHERE user_id = ? AND status = 'open' ORDER BY created_at ASC`
  )
    .bind(userId)
    .all();
  const open = rows.results || [];
  return {
    ok: true,
    handle,
    oneThing: open.length ? open[0] : null, // oldest open = the one thing
    captures: open,
    count: open.length,
  };
}

async function capture(request, env, origin, session) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "bad request" }, 400, origin);
  }
  const text = String(body?.text || "").trim();
  if (!text) return json({ ok: false, error: "nothing to capture" }, 422, origin);
  if (text.length > 2000) return json({ ok: false, error: "too long" }, 422, origin);

  await env.DB.prepare("INSERT INTO captures (id, user_id, text) VALUES (?, ?, ?)")
    .bind(uuid(), session.user_id, text)
    .run();
  return json(await loadState(env, session.user_id, session.handle), 200, origin);
}

async function markDone(request, env, origin, session) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "bad request" }, 400, origin);
  }
  const id = String(body?.id || "");
  if (!id) return json({ ok: false, error: "bad request" }, 400, origin);
  await env.DB.prepare(
    "UPDATE captures SET status = 'done', done_at = datetime('now') WHERE id = ? AND user_id = ?"
  )
    .bind(id, session.user_id)
    .run();
  return json(await loadState(env, session.user_id, session.handle), 200, origin);
}

async function state(request, env, origin, session) {
  return json(await loadState(env, session.user_id, session.handle), 200, origin);
}

// Route /app/* -> handler (all session-gated). Returns null if not an app route.
export async function handleApp(request, env, url, origin) {
  const routes = {
    "GET /app/state": state,
    "POST /app/capture": capture,
    "POST /app/done": markDone,
  };
  const fn = routes[`${request.method} ${url.pathname}`];
  if (!fn) return null;

  const session = await getSession(env, request);
  if (!session) return json({ ok: false, error: "not authenticated" }, 401, origin);
  return fn(request, env, origin, session);
}
