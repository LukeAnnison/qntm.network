"""The render domain — source content -> served HTML.

qntm.network's first traced package (capability: site-renders-markdown). The topology:
capability -> package (qntm_network.render) -> class (MarkdownRenderer, pure) -> the
rendered-page-written sink. MarkdownRenderer is a pure leaf off the sink-path; the sink
lives in build.py.
"""

from qntm_network.render.renderer import MarkdownRenderer

__all__ = ["MarkdownRenderer"]
