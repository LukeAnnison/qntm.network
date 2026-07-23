"""MarkdownRenderer — the pure markdown -> HTML transform (CommonMark).

PURE by design: to_html(str) -> str, no I/O, no sink. It wraps the CommonMark library and
returns a string; the writing happens in build.py's sink. Because it never reaches a sink,
MarkdownRenderer sits OFF the sink-path — a leaf that adds ZERO call-stack depth. That is the
depth-to-sink model rewarding purity: keep transforms pure and the number stays low.
"""

from __future__ import annotations

from markdown_it import MarkdownIt


class MarkdownRenderer:
    """Pure CommonMark markdown -> HTML transform."""

    def __init__(self) -> None:
        # CommonMark base + the GFM table rule (the demo advertises a table; keep it truthful).
        self._md = MarkdownIt("commonmark").enable("table")

    def to_html(self, markdown: str) -> str:
        """Render markdown source to an HTML fragment. Pure — no side effects."""
        return self._md.render(markdown)
