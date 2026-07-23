/**
 * Render-and-edit scenario — the observed runtime for the qntm.network app.
 *
 * flow-trace's node observer imports this module, installs its load hook first, and records every
 * cross-module call the run makes. Those CallRecords are what flows.yaml is measured against, so
 * this file is the reason the app has an OBSERVED half at all and not only static existence
 * checks. It exports `run()`, the same convention the Python scenarios use.
 *
 * WHAT IT DRIVES — the real chain, in the order a reader produces it:
 *   mount(source)         -> MarkdownRenderer.toHtml   (the initial paint)
 *   mount(source)         -> EditorSession construction
 *   click the toggle      -> EditorSession.toggle      (view -> edit)
 *   type into the source  -> EditorSession.setSource + MarkdownRenderer.toHtml (live re-render)
 *
 * WHAT IS STUBBED, and why that is honest. The modules under app/ are REAL — nothing here
 * substitutes for renderer.ts or session.ts, and the calls recorded are genuine calls into them.
 * What is faked is the browser: a handful of DOM objects with only the members mount() actually
 * touches. That is the same posture as the static-evidence predicates — real code, deterministic
 * environment — and it is the standard shape for observing a browser app off-browser. The claim
 * it supports is "these modules call each other this way", which is exactly what flows.yaml
 * declares. It does NOT claim the page renders correctly in a browser; that is what the
 * in-browser verification at each close is for. Do not read one as the other.
 */

import { mount } from "../../app/main.js";

const SOURCE = [
  "# heading",
  "",
  "Some **bold** text and `code`.",
  "",
  "- a list item",
].join("\n");

type Listener = () => void;

/** The smallest object that satisfies what mount() touches — no more surface than that. */
class StubElement {
  innerHTML = "";
  textContent = "";
  value = "";
  readonly dataset: Record<string, string> = {};
  readonly attributes: Record<string, string> = {};
  readonly #listeners = new Map<string, Listener[]>();

  addEventListener(type: string, listener: Listener): void {
    const existing = this.#listeners.get(type) ?? [];
    existing.push(listener);
    this.#listeners.set(type, existing);
  }

  setAttribute(name: string, value: string): void {
    this.attributes[name] = value;
  }

  focus(): void {
    /* no-op: focus has no observable consequence off-browser */
  }

  /** Fire the handlers mount() registered — this is what makes the scenario a real run. */
  dispatch(type: string): void {
    for (const listener of this.#listeners.get(type) ?? []) {
      listener();
    }
  }
}

export function run(): void {
  const elements: Record<string, StubElement> = {
    "#app": new StubElement(),
    "#rendered": new StubElement(),
    "#source": new StubElement(),
    "#mode-toggle": new StubElement(),
  };

  // mount() reaches for `document` at module scope, so the stub has to be global before it runs.
  (globalThis as unknown as { document: unknown }).document = {
    querySelector: (selector: string): StubElement | null => elements[selector] ?? null,
  };

  const toggle = elements["#mode-toggle"];
  const source = elements["#source"];
  const app = elements["#app"];
  const rendered = elements["#rendered"];
  if (!toggle || !source || !app || !rendered) {
    throw new Error("scenario stub is incomplete");
  }

  // 1. The initial paint — mount -> renderer, mount -> session.
  mount(SOURCE);
  if (!rendered.innerHTML.includes("<h1>")) {
    throw new Error("mount did not render the document");
  }

  // 2. Toggle to edit — mount's click handler -> EditorSession.toggle.
  toggle.dispatch("click");
  if (app.dataset["mode"] !== "edit") {
    throw new Error(`expected edit mode, got ${String(app.dataset["mode"])}`);
  }

  // 3. Type — the input handler -> EditorSession.setSource, then the renderer again.
  source.value = `${SOURCE}\n\n## typed`;
  source.dispatch("input");
  if (!rendered.innerHTML.includes("typed")) {
    throw new Error("typing did not re-render");
  }

  // 4. Back to view — the toggle is genuinely two-way, so the scenario proves both directions.
  toggle.dispatch("click");
  if (app.dataset["mode"] !== "view") {
    throw new Error(`expected view mode, got ${String(app.dataset["mode"])}`);
  }
}
