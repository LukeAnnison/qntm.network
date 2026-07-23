"""CSS loader — reads the reading stylesheet so render_page can inline it into the page
<head>. A pure source: load_css() -> str. It reads the css from disk (the boundary) and
returns the text; the page shell inlines it, keeping the artifact self-contained (no external
stylesheet request for Cloudflare Pages to serve). The stylesheet echoes the qntm-quantum
Obsidian snippet's monochrome-plus-teal aesthetic.
"""

from __future__ import annotations

from pathlib import Path

_CSS = Path(__file__).resolve().parent / "reading.css"


def load_css() -> str:
    """Return the reading stylesheet's text, to inline into the page <head>."""
    return _CSS.read_text(encoding="utf-8")
