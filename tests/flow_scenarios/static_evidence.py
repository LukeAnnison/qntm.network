"""Static-evidence scenario for qntm.network — the static-evidence RUNTIME.

A flow-trace scenario is a module with a `run()` returning a ScenarioState. This one does NO
capture (no traced code in a static site) — it READS the repo artifacts (index.html and the rest
live alongside) and exposes the project root to the state predicates in qntm_network_checks.py,
which assert deterministic invariants over those artifacts (plus one live HTTPS probe).

It reads source via `read_text` — so flow-trace's tier audit classifies it `static-evidence`, the
honest ceiling for a no-traced-runtime project. `flow-trace verify .` discovers this scenario, runs
the state stage against it, and emits a real PASS/FAIL verdict per invariant.
"""

from __future__ import annotations

from pathlib import Path

from flow_trace.schema import ScenarioState

# .../qntm.network/tests/flow_scenarios/static_evidence.py
#   parents[2] = .../qntm.network  (the project root)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run() -> ScenarioState:
    # Read the primary artifact up front: confirms this is the qntm.network project (fail fast if
    # the tree is wrong) and makes this a genuine static-evidence scenario (read_text → tier audit).
    index_html = (_PROJECT_ROOT / "index.html").read_text(encoding="utf-8")
    return ScenarioState(
        artifacts={"project_root": str(_PROJECT_ROOT), "index_html_len": len(index_html)}
    )
