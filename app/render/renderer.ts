/**
 * MarkdownRenderer — the pure markdown -> HTML transform (CommonMark).
 *
 * Ported from qntm_network/render/renderer.py (2026-07-23), which retired in the same change.
 * The port is deliberately faithful: same library family (markdown-it), same CommonMark preset,
 * same table rule enabled. Only the execution site moved — from build time on the server to
 * runtime in the browser — because a live editor cannot re-run a Python build on every keystroke.
 *
 * PURE by design: toHtml(string) -> string, no I/O, no DOM. Keeping the transform pure is what
 * lets the editor call it on every keystroke without coordinating side effects, and it keeps the
 * mounting concern (main.ts) as the single place that touches the page.
 *
 * There is exactly ONE markdown implementation in this repo and this is it
 * (architecture.yaml#one-implementation-per-concern).
 */

import MarkdownIt from "markdown-it";

export class MarkdownRenderer {
  readonly #md: MarkdownIt;

  constructor() {
    // CommonMark base + the GFM table rule — the demo content advertises a table, so the
    // renderer has to actually render one (carried over from the Python original).
    this.#md = new MarkdownIt("commonmark").enable("table");
  }

  /** Render markdown source to an HTML fragment. Pure — no side effects. */
  toHtml(markdown: string): string {
    return this.#md.render(markdown);
  }
}
