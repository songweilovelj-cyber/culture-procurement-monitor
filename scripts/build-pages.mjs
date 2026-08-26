import { cp, mkdir } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const docsDir = path.join(root, "docs");

const copies = [
  ["public/index.html", "docs/index.html"],
  ["public/app.js", "docs/app.js"],
  ["public/styles.css", "docs/styles.css"],
  ["public/static-engine.js", "docs/static-engine.js"],
  ["data/funds.json", "docs/data/funds.json"],
  ["data/market.json", "docs/data/market.json"],
  ["data/portfolio.json", "docs/data/portfolio.json"]
];

await mkdir(path.join(docsDir, "data"), { recursive: true });

for (const [from, to] of copies) {
  await cp(path.join(root, from), path.join(root, to));
  console.log(`pages: ${from} -> ${to}`);
}
