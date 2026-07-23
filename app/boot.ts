/**
 * The bootstrap — the build's entry point, and the ONLY module with a top-level side effect.
 *
 * Everything importable lives in main.ts; the act of starting lives here. That separation is
 * what makes the app observable: flow-trace's node observer imports modules to watch them, so a
 * module that starts itself on import cannot be watched (it runs before anything is listening,
 * and in node's case throws on a relative fetch URL). Concentrating the side effect in one file
 * that nothing else imports means every other module stays inert until called.
 *
 * The stylesheet imports live here for the same reason, one layer down: `import "./x.css"` is a
 * bundler instruction that node cannot resolve, so keeping it out of main.ts is what lets a
 * scenario import main.ts at all.
 */

import "./styles/reading.css";
import "./styles/editor.css";
import { main } from "./main.js";

void main();
