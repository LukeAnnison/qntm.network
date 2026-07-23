/**
 * The app entry — mount the document, wire the view/edit toggle.
 *
 * This is the only module that touches the DOM. The renderer is pure and the session holds mode
 * plus text, so everything page-shaped is concentrated here rather than smeared across all three.
 *
 * The old build-time pipeline's terminal effect was a file write (the retired
 * `rendered-page-written` sink). A browser app's terminal effect is the DOM mount, which is what
 * `mount()` below is. That sink is NOT declared in sinks.yaml, deliberately: flow-trace captures
 * Python only, so declaring a TypeScript sink would create a commitment nothing can ever observe.
 * It gets declared when flow-trace's `typescript-capture-backend` lands.
 */

import { MarkdownRenderer } from "./render/renderer.js";
import { EditorSession } from "./editor/session.js";
import "./styles/reading.css";
import "./styles/editor.css";

const SOURCE_URL = "../content/demo.md";

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

async function main(): Promise<void> {
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

void main();
