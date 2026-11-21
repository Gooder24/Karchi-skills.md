// Shared by ship.mts and land.mts: git and gh calls, the repo's rules, and waiting for CI with one line out.
import { spawnSync } from "node:child_process";

// eSYST work repos: no commit, push or merge without Karchi's yes in the thread (skill github).
export const WORK_REPOS = new Set(["spotrex", "esystak", "partsheet", "enex-crz-email-mvp"]);

export function sh(cmd: string, args: string[], opts: { cwd?: string; allowFail?: boolean } = {}) {
  const r = spawnSync(cmd, args, { encoding: "utf8", maxBuffer: 64 << 20, cwd: opts.cwd });
  const out = (r.stdout ?? "").trim();
  if (r.status !== 0 && !opts.allowFail) die(`${cmd} ${args.join(" ")} zlyhalo:\n${(r.stderr || r.stdout || "").trim()}`, 2);
  return { ok: r.status === 0, out, err: (r.stderr ?? "").trim() };
}

export function die(message: string, code = 2): never {
  console.error(message);
  process.exit(code);
}

export function repoOf(cwd?: string) {
  const url = sh("git", ["remote", "get-url", "origin"], { cwd }).out;
  const m = /github\.com[:/]([^/]+)\/(.+?)(?:\.git)?\/?$/.exec(url);
  if (!m) die(`origin ${url} nie je GitHub`);
  return { owner: m[1], name: m[2], full: `${m[1]}/${m[2]}` };
}

type Run = { databaseId: number; name: string; status: string; conclusion: string; url: string };

// Waits for every workflow run of `sha` and prints one line; returns true when all passed (or none exist).
export function waitForCi(repo: string, sha: string, minutes: number): boolean {
  const deadline = Date.now() + minutes * 60_000;
  const appearBy = Date.now() + 90_000;
  const sleep = (s: number) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, s * 1000);
  for (;;) {
    const runs = JSON.parse(sh("gh", ["run", "list", "-R", repo, "--commit", sha, "--json", "databaseId,name,status,conclusion,url"]).out) as Run[];
    if (!runs.length && Date.now() > appearBy) { console.log("CI: pre tento commit sa nespustilo nič"); return true; }
    const bad = runs.filter((r) => r.status === "completed" && !["success", "skipped", "neutral"].includes(r.conclusion));
    if (bad.length) {
      for (const r of bad) {
        console.log(`CI: ${r.name} ${r.conclusion}: ${r.url}`);
        const log = sh("gh", ["run", "view", String(r.databaseId), "-R", repo, "--log-failed"], { allowFail: true }).out;
        console.log(log.split("\n").slice(-40).join("\n"));
      }
      return false;
    }
    if (runs.length && runs.every((r) => r.status === "completed")) { console.log(`CI: zelené (${runs.map((r) => r.name).join(", ")})`); return true; }
    if (Date.now() > deadline) { console.log(`CI: po ${minutes} min ešte beží (${runs.filter((r) => r.status !== "completed").map((r) => r.url).join(" ")})`); return false; }
    sleep(15);
  }
}

type Check = { name: string; bucket: string; link: string };

// For a pull request: every check GitHub shows on it (Actions and third-party statuses), not just Actions runs.
export function waitForPrChecks(repo: string, pr: string, minutes: number): boolean {
  const deadline = Date.now() + minutes * 60_000;
  const appearBy = Date.now() + 90_000;
  const sleep = (s: number) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, s * 1000);
  for (;;) {
    const r = sh("gh", ["pr", "checks", pr, "-R", repo, "--json", "name,bucket,link"], { allowFail: true });
    const checks = r.out.startsWith("[") ? (JSON.parse(r.out) as Check[]) : [];
    if (!checks.length && Date.now() > appearBy) { console.log("CI: PR nemá žiadne checky"); return true; }
    const bad = checks.filter((c) => c.bucket === "fail" || c.bucket === "cancel");
    if (bad.length) {
      for (const c of bad) {
        console.log(`CI: ${c.name} ${c.bucket}: ${c.link}`);
        const run = /\/actions\/runs\/(\d+)/.exec(c.link)?.[1];
        if (run) console.log(sh("gh", ["run", "view", run, "-R", repo, "--log-failed"], { allowFail: true }).out.split("\n").slice(-40).join("\n"));
      }
      return false;
    }
    if (checks.length && checks.every((c) => c.bucket !== "pending")) { console.log(`CI: zelené (${checks.length} checkov)`); return true; }
    if (Date.now() > deadline) { console.log(`CI: po ${minutes} min ešte beží: ${checks.filter((c) => c.bucket === "pending").map((c) => c.name).join(", ")}`); return false; }
    sleep(15);
  }
}
