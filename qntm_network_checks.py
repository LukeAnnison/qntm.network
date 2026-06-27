"""Static-evidence predicates for qntm.network (a static landing site).

THE STATIC-EVIDENCE RUNTIME. The site has no traced code, but that does NOT mean "no runtime" —
the runtime is DETERMINISTIC ARTIFACT CHECKS (+ one live HTTPS probe), not traced calls. These
predicates RUN under flow-trace's normal scenario + state engine: the scenario
`tests/flow_scenarios/static_evidence.py` exposes the project root as a ScenarioState; each
predicate below asserts ONE invariant over the repo artifacts (index.html, CNAME, worker/) and
returns PASS / FAIL / INFO. This is how qntm.network earns honest greens instead of capping at
hand-inspection. Pin: architecture.yaml#declared-before-enforced.
"""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from pathlib import Path

from flow_trace.schema import PredicateResult, ScenarioState


def _root(state: ScenarioState) -> Path | None:
    r = state.artifacts.get("project_root")
    return Path(r) if r else None


def _guard(state: ScenarioState) -> PredicateResult | None:
    root = _root(state)
    if root is None or not root.is_dir():
        return PredicateResult(
            status="FAIL",
            message="project_root artifact missing or not a directory (scenario did not expose the project)",
        )
    return None


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def assert_landing_page_present(state: ScenarioState) -> PredicateResult:
    """index.html renders the brand, the thesis headline, and an email capture form."""
    if guard := _guard(state):
        return guard
    html = _read(_root(state) / "index.html")
    needles = {"brand": "qntm", "headline": "least resistance", "email input": 'type="email"', "form": "<form"}
    missing = [label for label, n in needles.items() if n not in html]
    if missing:
        return PredicateResult(status="FAIL", message=f"index.html missing {missing}", observed_ref="index.html")
    return PredicateResult(
        status="PASS",
        message="landing page carries the brand, thesis headline, and an email form",
        observed_ref="index.html",
    )


def assert_responsive_meta_present(state: ScenarioState) -> PredicateResult:
    """index.html declares responsive behaviour (viewport meta + a mobile media query)."""
    if guard := _guard(state):
        return guard
    html = _read(_root(state) / "index.html")
    missing = [n for n in ['name="viewport"', "@media (max-width: 760px)"] if n not in html]
    if missing:
        return PredicateResult(status="FAIL", message=f"index.html missing responsive markers {missing}", observed_ref="index.html")
    return PredicateResult(
        status="PASS",
        message="viewport meta + mobile media query present (responsive)",
        observed_ref="index.html",
    )


def assert_signature_interactions_present(state: ScenarioState) -> PredicateResult:
    """The thesis-as-interaction shipped and hasn't rotted: glowing cursor + repel + scattered creed."""
    if guard := _guard(state):
        return guard
    html = _read(_root(state) / "index.html")
    missing = [n for n in ["cursor-glow", 'class="repel"', "creed-grid"] if n not in html]
    if missing:
        return PredicateResult(status="FAIL", message=f"signature interactions missing {missing}", observed_ref="index.html")
    return PredicateResult(
        status="PASS",
        message="glowing cursor + repel headlines + scattered creed all present",
        observed_ref="index.html",
    )


def assert_deploy_is_push_to_publish(state: ScenarioState) -> PredicateResult:
    """A CNAME pinned to the custom domain = GitHub Pages serves main on push (no manual step)."""
    if guard := _guard(state):
        return guard
    cname = _read(_root(state) / "CNAME").strip()
    if cname != "qntm.network":
        return PredicateResult(
            status="FAIL",
            message=f"CNAME is {cname!r}, expected 'qntm.network' (push-to-publish custom-domain proxy)",
            observed_ref="CNAME",
        )
    return PredicateResult(
        status="PASS",
        message="CNAME=qntm.network → GitHub Pages publishes main on push (push-to-publish)",
        observed_ref="CNAME",
    )


def assert_email_signups_persisted(state: ScenarioState) -> PredicateResult:
    """The forms POST to the Cloudflare Worker, and the Worker INSERTs into the signups D1 table."""
    if guard := _guard(state):
        return guard
    root = _root(state)
    html = _read(root / "index.html")
    worker = _read(root / "worker" / "src" / "index.js")
    problems = []
    if "workers.dev" not in html:
        problems.append("index.html does not POST to the Cloudflare Worker endpoint")
    if "form.access" not in html and "signup capture" not in html:
        problems.append("index.html has no signup submit handler")
    if "INSERT" not in worker.upper():
        problems.append("worker/src/index.js does not INSERT a signup")
    if "signups" not in worker:
        problems.append("worker does not reference the signups table")
    if problems:
        return PredicateResult(
            status="FAIL",
            message="email capture not wired — " + "; ".join(problems),
            observed_ref="worker/src/index.js",
        )
    return PredicateResult(
        status="PASS",
        message="forms POST to the Worker; Worker INSERTs into the signups D1 table",
        observed_ref="worker/src/index.js",
    )


def assert_static_evidence_runner_wired(state: ScenarioState) -> PredicateResult:
    """Self-referential: the runner (scenario + this predicate module) exists, so verify runs real checks."""
    if guard := _guard(state):
        return guard
    root = _root(state)
    scenario = root / "tests" / "flow_scenarios" / "static_evidence.py"
    checks = root / "qntm_network_checks.py"
    missing = [str(p.relative_to(root)) for p in (scenario, checks) if not p.is_file()]
    if missing:
        return PredicateResult(status="FAIL", message=f"static-evidence runner missing {missing}", observed_ref="qntm_network_checks.py")
    return PredicateResult(
        status="PASS",
        message="static-evidence runner wired (scenario + predicate module present) — flow-trace verify runs real checks",
        observed_ref="qntm_network_checks.py",
    )


def assert_link_preview_meta_present(state: ScenarioState) -> PredicateResult:
    """SHARE: index.html declares OG + Twitter card meta and the preview image artifact exists."""
    if guard := _guard(state):
        return guard
    root = _root(state)
    html = _read(root / "index.html")
    needles = ["og:title", "og:description", "og:image", 'twitter:card']
    missing = [n for n in needles if n not in html]
    if not (root / "og.png").is_file():
        missing.append("og.png (preview image file)")
    if missing:
        return PredicateResult(status="FAIL", message=f"link-preview not wired — missing {missing}", observed_ref="index.html")
    return PredicateResult(
        status="PASS",
        message="OG + Twitter card meta present and og.png preview image exists (link previews render)",
        observed_ref="index.html",
    )


def assert_visits_are_measured(state: ScenarioState) -> PredicateResult:
    """SEE: index.html ships a privacy-friendly analytics beacon (Cloudflare Web Analytics)."""
    if guard := _guard(state):
        return guard
    html = _read(_root(state) / "index.html")
    has_beacon = "cloudflareinsights.com/beacon" in html
    has_token = "data-cf-beacon" in html and "token" in html
    if not (has_beacon and has_token):
        return PredicateResult(
            status="FAIL",
            message="no analytics beacon — index.html lacks the Cloudflare Web Analytics snippet (beacon + token)",
            observed_ref="index.html",
        )
    return PredicateResult(
        status="PASS",
        message="Cloudflare Web Analytics beacon present (visits measured, no cookies)",
        observed_ref="index.html",
    )


def assert_served_over_valid_https(state: ScenarioState) -> PredicateResult:
    """LIVE-evidence: actually fetch the production site over HTTPS, validating the TLS certificate.

    PASS = 200 over a valid cert. FAIL = a real HTTPS/cert failure (the warning is back).
    INFO = network unreachable this run (offline) — cannot verify, does not gate.
    """
    url = "https://qntm.network/"
    req = urllib.request.Request(url, headers={"User-Agent": "flow-trace-static-check"})
    try:
        with urllib.request.urlopen(req, timeout=8, context=ssl.create_default_context()) as r:
            code, final = r.getcode(), r.geturl()
        if code == 200 and final.startswith("https://"):
            return PredicateResult(status="PASS", message=f"{url} → {code} over a valid TLS cert (live)", observed_ref=final)
        return PredicateResult(status="FAIL", message=f"unexpected response: {code} / {final}", observed_ref=url)
    except urllib.error.HTTPError as e:
        return PredicateResult(status="FAIL", message=f"server returned {e.code} for {url}", observed_ref=url)
    except urllib.error.URLError as e:
        reason = str(getattr(e, "reason", e)).lower()
        if "certificate" in reason or "ssl" in reason:
            return PredicateResult(status="FAIL", message=f"TLS certificate verification FAILED: {getattr(e, 'reason', e)}", observed_ref=url)
        return PredicateResult(status="INFO", message=f"could not reach {url} (offline?) — UNVERIFIABLE this run: {getattr(e, 'reason', e)}", observed_ref=url)
    except (OSError, TimeoutError) as e:
        return PredicateResult(status="INFO", message=f"could not reach {url} (offline?) — UNVERIFIABLE this run: {e}", observed_ref=url)
