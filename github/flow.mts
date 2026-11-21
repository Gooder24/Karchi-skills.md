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
