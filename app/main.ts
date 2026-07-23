/**
 * The app's wiring — mount the document, wire the view/edit toggle.
 *
 * This is the only module that touches the DOM. The renderer is pure and the session holds mode
 * plus text, so everything page-shaped is concentrated here rather than smeared across all three.
 *
 * DELIBERATELY SIDE-EFFECT-FREE ON IMPORT. This module used to end with a bare `void main()`,
 * which meant importing it ran it — so it could not be exercised by anything that was not a
 * browser, and flow-trace's node observer could not see a single call. Adopting the TypeScript
 * capture backend forced the split that should have existed anyway: the bootstrap moved to
 * boot.ts (the build's entry point), and the stylesheet imports went with it, since they are a
 * bundler concern that node cannot resolve. What remains here is importable, observable, and
 * callable with a stub DOM — which is exactly why tests/flow_scenarios/render_and_edit.ts can
 * drive the real chain.
 *
 * `mount()` is the SINK (`app/main:mount`, sinks.yaml). A browser app's terminal effect is the
 * DOM mount, not a disk write — depth-to-sink here reads "how many hops from entry to the
 * document being on screen".
 */

import { MarkdownRenderer } from "./render/renderer.js";
import { EditorSession } from "./editor/session.js";

export const SOURCE_URL = "../content/demo.md";

function required<T extends Element>(selector: string): T {
  const el = document.querySelector<T>(selector);
  if (el === null) {
    throw new Error(`missing required element: ${selector}`);
  }
  return el;
}

/** Mount the app: render the source, wire the toggle, reflect mode in the DOM. */
export function mount(source: string): void {
  const renderer = new MarkdownRenderer();
  const session = new EditorSession(source);

  const root = required<HTMLElement>("#app");
  const rendered = required<HTMLElement>("#rendered");
  const editor = required<HTMLTextAreaElement>("#source");
  const toggle = required<HTMLButtonElement>("#mode-toggle");

  const paint = (): void => {
    rendered.innerHTML = renderer.toHtml(session.source);
  };

  const reflect = (): void => {
    const mode = session.mode;
    root.dataset["mode"] = mode;
    // The button names the mode you'd GO to, not the one you're in — a toggle labelled with
    // its current state reads as a status display and gets clicked by mistake.
    toggle.textContent = mode === "view" ? "Edit" : "View";
    toggle.setAttribute("aria-pressed", String(mode === "edit"));
    if (mode === "edit") {
      editor.focus();
    }
  };

  editor.value = session.source;
  editor.addEventListener("input", () => {
    session.setSource(editor.value);
    // Re-render on every keystroke: the renderer is pure and the documents are small, so the
    // simple thing is correct here. If a document ever grows big enough for this to stutter,
    // that is the point to debounce — not before.
    paint();
  });

  toggle.addEventListener("click", () => {
    session.toggle();
    reflect();
  });

  paint();
  reflect();
}

/** Fetch the document and mount it. Called by boot.ts; never on import. */
export async function main(): Promise<void> {
  const rendered = required<HTMLElement>("#rendered");
  try {
    const response = await fetch(SOURCE_URL);
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    mount(await response.text());
  } catch (error) {
    // Fail visibly rather than leaving a blank page — a silent empty document looks like a
    // rendering bug and sends you hunting in the wrong module.
    rendered.textContent = `Could not load ${SOURCE_URL}: ${String(error)}`;
  }
}
