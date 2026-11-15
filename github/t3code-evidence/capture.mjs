// Screenshot and text capture for before-after.sh. Run from a T3 Code checkout (uses its Playwright).
// node capture.mjs <out-dir> <path> [--hover <text>] [--text <regex>] [--clip x,y,w,h] [--setup <module.mjs>]
// --setup exports `default async (page, origin)` for steps before the capture (switch a setting, open a panel).
// Context: en-US, Europe/Bratislava, 1280x800, system Chromium. Pairing is cached per server start.
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
const require = createRequire(path.join(process.cwd(), "apps/web/package.json"));
const { chromium } = require("playwright");
const [outDir, target, ...rest] = process.argv.slice(2);
const opt = (name) => { const i = rest.indexOf(`--${name}`); return i < 0 ? undefined : rest[i + 1]; };
const { PAIRING_URL, ORIGIN, LABEL = "shot" } = process.env;
fs.mkdirSync(outDir, { recursive: true });
const state = path.join(outDir, `.auth-${new URL(PAIRING_URL).hash.slice(-8)}.json`);
const browser = await chromium.launch({ executablePath: "/usr/bin/chromium" });
const context = await browser.newContext({
  locale: "en-US", timezoneId: "Europe/Bratislava", viewport: { width: 1280, height: 800 },
  ...(fs.existsSync(state) ? { storageState: state } : {}),
});
const page = await context.newPage();
// The app redirects right after pairing and start; a navigation it interrupts is retried.
const go = async (url) => {
  for (let i = 0; ; i++) {
    try { return await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 }); } catch (e) {
      if (i === 2 || !/interrupted by another navigation/.test(e.message)) throw e;
      await page.waitForTimeout(1500);
    }
  }
};
try {
  if (!fs.existsSync(state)) {
    await go(PAIRING_URL);
    await page.waitForURL((u) => !u.pathname.startsWith("/pair"), { timeout: 120000 });
    await context.storageState({ path: state });
  }
  await go(ORIGIN + "/");
  await page.waitForTimeout(2000);
  if (opt("setup")) await (await import(path.resolve(opt("setup")))).default(page, ORIGIN);
  await go(ORIGIN + target);
  await page.waitForTimeout(1500);
  if (opt("hover")) {
    // A tooltip can miss the first hover while a panel mounts; move away and retry.
    for (let i = 0; ; i++) {
      await page.mouse.move(0, 0);
      await page.getByText(opt("hover")).first().hover();
      try { await page.locator("[data-slot=tooltip-popup]").last().waitFor({ timeout: 5000 }); break; }
      catch (e) { if (i === 2) throw e; }
    }
  }
  if (opt("text")) await page.locator(`text=/${opt("text")}/`).first().waitFor({ timeout: 60000 });
  if (opt("text")) console.log(LABEL, JSON.stringify(await page.locator(`text=/${opt("text")}/`).allInnerTexts()));
  const [x, y, width, height] = (opt("clip") ?? "").split(",").map(Number);
  await page.screenshot({ path: path.join(outDir, `${LABEL}.png`), ...(opt("clip") ? { clip: { x, y, width, height } } : {}) });
} finally {
  await browser.close();
}
