"""Static-evidence scenario for the qntm brand department.

Reads BRAND.md (read_text → tier audit classifies this static-evidence) and exposes the brand
project root to the predicates in brand_checks.py. `flow-trace verify .` runs them for real.
"""

from __future__ import annotations

from pathlib import Path

from flow_trace.schema import ScenarioState

# .../qntm.network/brand/tests/flow_scenarios/static_evidence.py  → parents[2] = .../brand
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run() -> ScenarioState:
    brief_len = len((_PROJECT_ROOT / "BRAND.md").read_text(encoding="utf-8"))
    return ScenarioState(artifacts={"project_root": str(_PROJECT_ROOT), "brief_len": brief_len})
