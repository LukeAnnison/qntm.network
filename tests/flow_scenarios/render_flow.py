"""Render-flow scenario — exercises the FULL designed render chain so flow-trace captures
it: render_demo -> render_page -> MarkdownRenderer.to_html (the pure transform) and
render_demo -> write_page (the sink). Unlike static_evidence.py (artifact reads, no capture),
this RUNS the traced code. render_demo writes the demo page (its real, idempotent output).
"""

from __future__ import annotations

from flow_trace.schema import ScenarioState

from qntm_network.render.build import render_demo


def run() -> ScenarioState:
    out = render_demo()  # render_page -> MarkdownRenderer.to_html; then write_page (the sink)
    return ScenarioState(artifacts={"rendered": str(out)})
