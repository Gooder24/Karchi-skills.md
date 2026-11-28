#!/usr/bin/env node
// agy-limit: how much of the Antigravity limits is left (Gemini and Claude & GPT, 5 hours and the week).
//
//   agy-limit
//
// T3 Code shows no Antigravity limits since 25. 11. 2026 (pingdotgg/t3code#43026): it had read them from Google's
// internal API itself, which can get the account flagged. This asks Antigravity's own CLI instead (`agy -p /usage`,
// the /usage command of agy). It uses agy's own sign-in when there is one, else T3's (the newest Antigravity profile
// in ~/.t3/userdata/providers/antigravity), copied for the one call into a private temporary home that is deleted
// right after, also on Ctrl+C. It lives in $XDG_RUNTIME_DIR (memory, gone at logout), and a copy a killed run left
// behind is deleted by the next run. Exit 0: limits printed. 1: no sign-in, or agy failed or gave none.
import { spawn } from "node:child_process";
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

const RUNTIME = process.env.XDG_RUNTIME_DIR && existsSync(process.env.XDG_RUNTIME_DIR) ? process.env.XDG_RUNTIME_DIR : tmpdir();

let running: ReturnType<typeof spawn> | undefined;

// agy's stdout when it exits 0 within 90 s; else what went wrong.
function usage(home: string) {
  return new Promise<{ out: string; err: string }>((resolve) => {
    const agy = (running = spawn(AGY, ["-p", "/usage"], { cwd: home, env: { ...process.env, HOME: home } }));
    let out = "";
    let err = "";
    agy.stdout.on("data", (chunk) => (out += chunk));
    agy.stderr.on("data", (chunk) => (err += chunk));
    const timer = setTimeout(() => agy.kill("SIGTERM"), 90_000);
    agy.on("error", (error) => (err += error.message));
    agy.on("close", (code, signal) => {
      clearTimeout(timer);
      const failed = code === 0 ? "" : signal ? `agy ended by ${signal}` : `agy exited with ${code}`;
      resolve(failed ? { out: "", err: `${failed}${err.trim() ? `: ${err.trim()}` : ""}` } : { out, err: err.trim() });
    });
  });
}

function fail(message: string): never {
  process.stderr.write(`agy-limit: ${message}\n`);
  process.exit(1);
}

if (!existsSync(AGY)) fail(`${AGY} is missing (Antigravity CLI)`);

// Older than any run can last (90 s for agy): a run still going keeps its copy.
for (const left of readdirSync(RUNTIME).filter((name) => name.startsWith("agy-limit-"))) {
  const path = join(RUNTIME, left);
  if (Date.now() - statSync(path).mtimeMs > 120_000) rmSync(path, { recursive: true, force: true });
}

let result: Awaited<ReturnType<typeof usage>>;
if (existsSync(OWN)) result = await usage(HOME);
else {
  const token = t3Token() ?? fail("no Antigravity sign-in: neither agy's own nor T3's");
  const home = mkdtempSync(join(RUNTIME, "agy-limit-"));
  const clean = () => rmSync(home, { recursive: true, force: true });
  for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"] as const) {
    process.on(signal, () => {
      running?.kill("SIGTERM");
      clean();
      process.exit(1);
    });
  }
  try {
    mkdirSync(join(home, ".gemini/antigravity-cli"), { recursive: true, mode: 0o700 });
    copyFileSync(token, join(home, ".gemini/antigravity-cli", TOKEN));
    result = await usage(home);
  } finally {
    clean();
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
