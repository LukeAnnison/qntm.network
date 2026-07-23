// esbuild resolves `import "./x.css"` into the emitted stylesheet; TypeScript needs to be told
// such an import is legal and carries no value.
declare module "*.css";
