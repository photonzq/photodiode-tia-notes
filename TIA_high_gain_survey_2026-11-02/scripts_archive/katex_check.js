// Render every math span listed by check_math_extract.py with KaTeX and report errors.
//
// Usage: node katex_check.js <path to katex.min.js> <spans.json>
//
// Display blocks are rendered in display mode (\tag allowed); inline spans in
// inline mode.  throwOnError is on, so any unsupported command is reported.
const fs = require("fs");
const katex = require(process.argv[2]);
const items = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
let bad = 0;
for (const it of items) {
  try {
    katex.renderToString(it.tex, { displayMode: it.kind === "display", throwOnError: true, strict: "ignore" });
  } catch (e) {
    bad += 1;
    console.log(`KaTeX error, line ${it.line}: ${JSON.stringify(it.tex.slice(0, 90))}: ${e.message}`);
  }
}
console.log(`${items.length} spans checked with KaTeX ${katex.version}; errors: ${bad}`);
