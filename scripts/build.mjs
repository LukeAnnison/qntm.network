/**
 * The app build — bundle app/main.ts into demo/app.js (+ demo/app.css).
 *
 * Output lands in demo/ and is COMMITTED, because GitHub Pages serves this repo from main:/ with
 * no build of its own. The obvious hazard of a committed build artifact is that it drifts from
 * source when someone forgets to rebuild, so CI does not merely run this — it runs it and then
 * fails if the working tree changed (see .github/workflows/build.yml). That check is what keeps
 * the amended push-to-deploy-loop honest: no human has to remember, because forgetting is caught.
 */

import { build } from "esbuild";

await build({
  entryPoints: ["app/main.ts"],
  bundle: true,
  format: "esm",
  target: ["es2022"],
  minify: true,
  sourcemap: true,
  outfile: "demo/app.js",
  logLevel: "info",
});
