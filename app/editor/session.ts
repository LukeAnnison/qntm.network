/**
 * EditorSession — the mode state machine and the in-memory document.
 *
 * Two modes: VIEW (the rendered document, read-only) and EDIT (the markdown source, editable).
 * The session owns which mode is active and what the current source text is, and nothing else —
 * it does no DOM work and no rendering, so the mode logic can be reasoned about (and later
 * tested) without a browser.
 *
 * EPHEMERAL BY DESIGN. The source lives in this object and nowhere else: no localStorage, no
 * sessionStorage, no IndexedDB, no network write. A refresh loses everything, deliberately —
 * this is the smallest honest version of the editing surface, and pretending otherwise would be
 * worse than the limitation. That property is not a comment: it is enforced by
 * state-edits-are-ephemeral, which FAILs if a persistence API appears anywhere under app/.
 * If persistence is wanted later it should arrive as a declared capability with its own
 * enforcer, not as a quiet addition here.
 */

export type Mode = "view" | "edit";

export class EditorSession {
  #mode: Mode = "view";
  #source: string;

  constructor(source: string) {
    this.#source = source;
  }

  get mode(): Mode {
    return this.#mode;
  }

  get source(): string {
    return this.#source;
  }

  /** Replace the in-memory source (called as the user types). Never persisted. */
  setSource(next: string): void {
    this.#source = next;
  }

  /** Switch to the other mode and return the mode now active. */
  toggle(): Mode {
    this.#mode = this.#mode === "view" ? "edit" : "view";
    return this.#mode;
  }
}
