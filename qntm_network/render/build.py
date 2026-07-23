"""The render build entry + the page-write SINK.

Follows the scripts/make_og.py precedent: a Python build step that produces a static artifact,
committed and served by Cloudflare Pages (push-to-deploy intact). render_demo reads the bundled
demo markdown, renders it via MarkdownRenderer (pure), wraps it in a minimal page shell, and
writes the output HTML — the `rendered-page-written` sink, the terminal effect where the work
lands.

Observed call flow (the depth-to-sink number reads this):
    render_demo -> write_page -> [SINK: file write]        depth 2  (the headline)
    render_demo -> render_page -> MarkdownRenderer.to_html  (returns; off the sink-path)
"""

from __future__ import annotations

from pathlib import Path

from qntm_network.render.renderer import MarkdownRenderer

_ROOT = Path(__file__).resolve().parents[2]  # .../qntm.network
_DEMO_MD = _ROOT / "content" / "demo.md"
_OUT = _ROOT / "demo" / "index.html"  # served at qntm.network/demo/

_PAGE_SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body>
<main style="max-width:44rem;margin:3rem auto;padding:0 1.25rem;font:16px/1.6 system-ui,sans-serif">
{body}
</main>
</body>
</html>
"""


def render_page(markdown: str, title: str = "qntm.network — markdown demo") -> str:
    """Pure: markdown -> a full HTML page string (renderer + shell, no I/O)."""
    body = MarkdownRenderer().to_html(markdown)
    return _PAGE_SHELL.format(title=title, body=body)


def write_page(html: str, out_path: Path = _OUT) -> Path:
    """SINK — rendered-page-written: the page HTML written to disk for Pages to serve."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_demo() -> Path:
    """Build entry (sibling of scripts/make_og.py): render the bundled demo md to the page."""
    markdown = _DEMO_MD.read_text(encoding="utf-8")
    html = render_page(markdown)
    return write_page(html)


if __name__ == "__main__":
    print(f"rendered -> {render_demo()}")
