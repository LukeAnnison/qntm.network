// qntm.network — signup capture Worker.
// POST {email, source?, company?}  -> stores in D1 (dedup), returns {ok}.
// GET  /export?key=EXPORT_KEY      -> CSV of the list (operator only).
// 'company' is a honeypot: bots fill it, we silently accept-and-drop.

const ALLOWED_ORIGINS = new Set([
  "https://qntm.network",
  "https://www.qntm.network",
  "http://localhost:8731", // local preview
]);

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function cors(origin) {
  const allow = ALLOWED_ORIGINS.has(origin) ? origin : "https://qntm.network";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(obj, status, origin) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...cors(origin) },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }

    // Operator export — GET /export?key=SECRET  (key set via `wrangler secret put EXPORT_KEY`)
    if (request.method === "GET" && url.pathname === "/export") {
      if (!env.EXPORT_KEY || url.searchParams.get("key") !== env.EXPORT_KEY) {
        return new Response("forbidden\n", { status: 403 });
      }
      const { results } = await env.DB.prepare(
        "SELECT email, created_at, source FROM signups ORDER BY created_at DESC"
      ).all();
      const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
      const csv = ["email,created_at,source"]
        .concat((results || []).map((r) => [esc(r.email), esc(r.created_at), esc(r.source)].join(",")))
        .join("\n");
      return new Response(csv + "\n", {
        headers: {
          "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": "attachment; filename=qntm-signups.csv",
        },
      });
    }

    if (request.method !== "POST") {
      return json({ ok: false, error: "method not allowed" }, 405, origin);
    }

    // Parse JSON or form-encoded body.
    let data = {};
    const ct = request.headers.get("Content-Type") || "";
    try {
      if (ct.includes("application/json")) data = await request.json();
      else data = Object.fromEntries(await request.formData());
    } catch {
      return json({ ok: false, error: "bad request" }, 400, origin);
    }

    // Honeypot — a real user never fills the hidden 'company' field.
    if (data.company) return json({ ok: true }, 200, origin);

    const email = String(data.email || "").trim().toLowerCase();
    if (!EMAIL_RE.test(email) || email.length > 254) {
      return json({ ok: false, error: "invalid email" }, 422, origin);
    }

    const source = String(data.source || "landing").slice(0, 64);
    const ip = request.headers.get("CF-Connecting-IP") || "";
    const ua = (request.headers.get("User-Agent") || "").slice(0, 256);

    try {
      await env.DB
        .prepare("INSERT OR IGNORE INTO signups (email, source, ip, user_agent) VALUES (?, ?, ?, ?)")
        .bind(email, source, ip, ua)
        .run();
    } catch {
      return json({ ok: false, error: "store failed" }, 500, origin);
    }

    return json({ ok: true }, 200, origin);
  },
};
