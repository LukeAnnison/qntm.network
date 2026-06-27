"""Static-evidence predicates for the qntm brand / design department.

Design pins are frameworks-for-understanding, not all falsifiable — so ONLY the process/asset
capabilities are enforced here (the brief exists, the gallery exists + explores the suite, the
design language is declared, the wordmark is present). The AESTHETIC-DECISION capabilities (which
icon mark is canonical, the final lockups) carry NO predicate — they are human decisions, not
checks, and sit declared/pool until settled. Honest: never a fake green on taste.
"""

from __future__ import annotations

from pathlib import Path

from flow_trace.schema import PredicateResult, ScenarioState


def _root(state: ScenarioState) -> Path | None:
    r = state.artifacts.get("project_root")
    return Path(r) if r else None


def _guard(state: ScenarioState) -> PredicateResult | None:
    root = _root(state)
    if root is None or not root.is_dir():
        return PredicateResult(status="FAIL", message="project_root artifact missing or not a directory")
    return None


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def assert_brief_present(state: ScenarioState) -> PredicateResult:
    """BRAND.md exists and pins the thesis, the taxonomy, and a decisions log."""
    if guard := _guard(state):
        return guard
    md = _read(_root(state) / "BRAND.md")
    needles = ["smallest identifiable", "quantification", "Wordmark", "Lettermark", "Decisions log"]
    missing = [n for n in needles if n not in md]
    if missing:
        return PredicateResult(status="FAIL", message=f"BRAND.md missing {missing}", observed_ref="BRAND.md")
    return PredicateResult(status="PASS", message="BRAND.md pins the thesis, the taxonomy, and a decisions log", observed_ref="BRAND.md")


def assert_gallery_present(state: ScenarioState) -> PredicateResult:
    """index.html is a browsable gallery: the category sections, a surface toggle, and a real set of tiles."""
    if guard := _guard(state):
        return guard
    html = _read(_root(state) / "index.html")
    sections = [f'id="{s}"' for s in ("wordmark", "qmark", "atom", "lockups", "icon")]
    missing = [s for s in sections if s not in html]
    if 'data-s=' not in html:
        missing.append("surface toggle (data-s=)")
    tiles = html.count('class="tile"')
    if tiles < 10:
        missing.append(f"enough concept tiles (found {tiles}, want >=10)")
    if missing:
        return PredicateResult(status="FAIL", message=f"gallery incomplete — missing {missing}", observed_ref="index.html")
    return PredicateResult(status="PASS", message=f"browsable gallery present: all category sections, surface toggle, {tiles} tiles", observed_ref="index.html")


def assert_design_language_declared(state: ScenarioState) -> PredicateResult:
    """The portable kit is declared: quantum green, the two typefaces, and the glow/radiance signature."""
    if guard := _guard(state):
        return guard
    corpus = (_read(_root(state) / "index.html") + _read(_root(state) / "BRAND.md")).lower()
    needles = ["#3ff07f", "inter", "jetbrains"]
    missing = [n for n in needles if n not in corpus]
    if "glow" not in corpus and "radiance" not in corpus:
        missing.append("glow/radiance")
    if missing:
        return PredicateResult(status="FAIL", message=f"design language not fully declared — missing {missing}", observed_ref="BRAND.md")
    return PredicateResult(status="PASS", message="design language declared (quantum green + Inter/JetBrains + glow/radiance)", observed_ref="BRAND.md")


def assert_wordmark_present(state: ScenarioState) -> PredicateResult:
    """The wordmark exists in the gallery — the stampable asset to refine around."""
    if guard := _guard(state):
        return guard
    html = _read(_root(state) / "index.html")
    if 'id="wordmark"' not in html or "qntm" not in html:
        return PredicateResult(status="FAIL", message="wordmark section / 'qntm' not found in gallery", observed_ref="index.html")
    return PredicateResult(status="PASS", message="wordmark present in the gallery (● qntm)", observed_ref="index.html")
