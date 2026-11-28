#!/usr/bin/env node
// agy-limit: how much of the Antigravity limits is left (Gemini and Claude & GPT, 5 hours and the week).
//
//   agy-limit
//
// T3 Code shows no Antigravity limits since 25. 11. 2026 (pingdotgg/t3code#43026): it had read them from Google's
// internal API itself, which can get the account flagged. This asks Antigravity's own CLI instead (`agy -p /usage`,
// the /usage command of agy). It uses agy's own sign-in when there is one, else T3's (the newest Antigravity profile
// in ~/.t3/userdata/providers/antigravity), copied for the one call into a private temporary home that is deleted
// right after. Exit 0: limits printed. 1: no sign-in, or agy gave none.
import { spawnSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync, statSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

const HOME = homedir();
const AGY = join(HOME, ".local/bin/agy");
const TOKEN = "antigravity-oauth-token";
const OWN = join(HOME, ".gemini/antigravity-cli", TOKEN);
const T3 = join(HOME, ".t3/userdata/providers/antigravity");

function t3Token() {
  if (!existsSync(T3)) return undefined;
  return readdirSync(T3)
    .map((profile) => join(T3, profile, "antigravity-acp", TOKEN))
    .filter((path) => existsSync(path))
    .sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs)[0];
}

function usage(home: string) {
  const run = spawnSync(AGY, ["-p", "/usage"], {
    cwd: home,
    env: { ...process.env, HOME: home },
    encoding: "utf8",
    timeout: 90_000,
  });
  return { out: run.stdout ?? "", err: `${run.stderr ?? ""}${run.error?.message ?? ""}`.trim() };
}

function fail(message: string): never {
  process.stderr.write(`agy-limit: ${message}\n`);
  process.exit(1);
}

if (!existsSync(AGY)) fail(`${AGY} is missing (Antigravity CLI)`);

let result: ReturnType<typeof usage>;
if (existsSync(OWN)) result = usage(HOME);
else {
  const token = t3Token() ?? fail("no Antigravity sign-in: neither agy's own nor T3's");
  const home = mkdtempSync(join(tmpdir(), "agy-limit-"));
  try {
    mkdirSync(join(home, ".gemini/antigravity-cli"), { recursive: true, mode: 0o700 });
    copyFileSync(token, join(home, ".gemini/antigravity-cli", TOKEN));
    result = usage(home);
  } finally {
    rmSync(home, { recursive: true, force: true });
  }
}

// agy prints one line per limit: group <TAB> limit <TAB> remaining % <TAB> reset (ISO; 1970 when it is not running).
const WINDOW: Record<string, string> = { "Five Hour Limit Remaining": "5 h", "Weekly Limit Remaining": "týždeň" };
const when = new Intl.DateTimeFormat("sk-SK", { weekday: "short", day: "numeric", month: "numeric", hour: "2-digit", minute: "2-digit" });
const rows = result.out
  .split("\n")
  .map((line) => line.split("\t"))
  .filter((cells) => cells.length === 4 && /^\d+%$/.test(cells[2]))
  .map(([group, limit, left, reset]) => {
    const at = new Date(reset);
    const resets = at.getTime() > Date.now() ? `, obnoví sa ${when.format(at)}` : "";
    return `${group.replace("Gemini Models", "Gemini").replace("Claude and GPT models", "Claude a GPT")} · ${WINDOW[limit] ?? limit}: ostáva ${left.replace("%", " %")}${resets}`;
  });
if (rows.length === 0) fail(`agy gave no limits${result.err ? `: ${result.err}` : ""}`);
process.stdout.write(`${rows.join("\n")}\n`);
