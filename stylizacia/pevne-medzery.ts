// Puts non-breaking spaces (Word: Ctrl+Shift+Space) where Slovak typography (STN 01 6910) wants them.
// Usage: bun pevne-medzery.ts [FILE]          text from FILE or stdin, fixed text to stdout
//        bun pevne-medzery.ts --check [FILE]  lists the places that still need one, exits 1 when any
const NBSP = " ";
const MONTHS = "januára|februára|marca|apríla|mája|júna|júla|augusta|septembra|októbra|novembra|decembra";
const UNITS = "eur|€|%|‰|ks|kg|g|t|km|m|cm|mm|m2|m²|m3|m³|l|ml|h|hod\\.|min\\.|sek\\.|dní|dni|dňa|dňoch|rokov|USD|CZK|Kč";
const TITLES = "Ing\\.|Mgr\\.|Bc\\.|MUDr\\.|JUDr\\.|PhDr\\.|RNDr\\.|Doc\\.|doc\\.|prof\\.|p\\.|č\\.|s\\.|str\\.|tel\\.|ods\\.|čl\\.|písm\\.|§";

// Each rule matches a normal space (or several) that must not break the line.
const rules: [string, RegExp][] = [
  ["jednopísmenové slovo", /(?<=(?:^|[\s(„"' ])[kKsSvVzZoOuUaAiI]) +(?=\S)/g],
  ["skratka alebo titul pred slovom", new RegExp(`(?<=(?:^|[\\s(„])(?:${TITLES})) +(?=\\S)`, "g")],
  ["iniciála mena", /(?<=(?:^|[\s(„])\p{Lu}\.) +(?=\p{Lu}\p{Ll})/gu],
  ["deň a mesiac", new RegExp(`(?<=\\b\\d{1,2}\\.) +(?=(?:${MONTHS})\\b)`, "g")],
  ["dátum číslami", /(?<=\b\d{1,2}\.) +(?=\d{1,2}\.(?:\s| )*\d{4}\b)|(?<=\b\d{1,2}\.(?:\s| )*\d{1,2}\.) +(?=\d{4}\b)/g],
  ["tisícky v čísle", /(?<=\b\d{1,3}) +(?=\d{3}(?![\d-]))/g],
  ["číslo a jednotka", new RegExp(`(?<=\\d(?:,\\d+|,[–-])?) +(?=(?:${UNITS})(?![\\p{L}\\d]))`, "gu")],
  ["s. r. o. a a. s.", /(?<=\S) +(?=s\.\s*r\.\s*o\.|a\.\s*s\.(?!\p{L}))|(?<=\bs\.) +(?=r\.)|(?<=\bs\.\s*r\.) +(?=o\.)|(?<=\ba\.) +(?=s\.)/gu],
];

export const fix = (text: string) => rules.reduce((t, [, re]) => t.replace(re, NBSP), text);

export const missing = (text: string) =>
  rules.flatMap(([why, re]) =>
    [...text.matchAll(re)].map((m) => {
      const at = m.index ?? 0;
      return { why, at, context: text.slice(Math.max(0, at - 20), at + 20).replaceAll("\n", " ") };
    }),
  );

if (import.meta.main) {
  const args = process.argv.slice(2);
  const check = args[0] === "--check";
  const file = check ? args[1] : args[0];
  const text = file ? await Bun.file(file).text() : await new Response(Bun.stdin.stream()).text();
  if (!check) process.stdout.write(fix(text));
  else {
    const found = missing(text);
    for (const m of found) console.log(`${m.why}: …${m.context}…`);
    process.exit(found.length ? 1 : 0);
  }
}
