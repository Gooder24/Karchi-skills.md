#!/usr/bin/env bun
// Wires the overenie-gate Stop hook into every Codex home on this machine (~/.codex and T3's ~/.codex-t3code/<account>)
// and trusts it, since Codex skips a user hook until it is trusted. install.sh runs this; safe to run again: a home whose
// hooks.json already holds the hook and whose config.toml already trusts it costs one file read.
// Usage: codex-hooks.mts [codex home …]     (default: every home on this machine)
// See it: `codex` → /hooks lists the hook and whether it is trusted. Way out: disable it there (hooks.state enabled =
// false, which this script leaves alone); deleting it from hooks.json does not stick, install.sh adds it back.
// Failures go to stderr with a <4> prefix: the timer's journal keeps them as warnings; a normal run prints nothing there.
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";

const HOME = process.env.HOME ?? "";
const COMMAND = `python3 -I ${HOME}/.work/karchi-skills/hooks/overenie-gate.py`;
const HANDLER = { type: "command", command: COMMAND, timeout: 10 };
const warn = (msg: string) => console.error(`<4>codex-hooks: ${msg}`);
type Handler = { type: string; command?: string; timeout?: number };
type HookEntry = { key: string; command?: string; currentHash: string; trustStatus: string };
type Reply = { data?: { hooks: HookEntry[] }[]; error?: unknown };
type Hooks = { hooks?: Record<string, { matcher?: string; hooks: Handler[] }[]> };

function homes() {
  const t3 = `${HOME}/.codex-t3code`;
  const accounts = existsSync(t3) ? readdirSync(t3).map((a) => `${t3}/${a}`) : [];
  return [`${HOME}/.codex`, ...accounts].filter((h) => existsSync(`${h}/config.toml`));
}

// Adds the handler to hooks.json, or brings ours back to HANDLER, keeping any other hooks and fields there.
function wire(home: string) {
  const path = `${home}/hooks.json`;
  const config: Hooks = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {};
  const stop = ((config.hooks ??= {}).Stop ??= []);
  const ours = stop.flatMap((g) => g.hooks).find((h) => h.command === COMMAND);
  if (ours && ours.type === HANDLER.type && ours.timeout === HANDLER.timeout) return;
  if (ours) Object.assign(ours, HANDLER);
  else stop.push({ hooks: [{ ...HANDLER }] });
  writeFileSync(path, JSON.stringify(config, null, 2) + "\n");
}

// The trust stamp holds the hooks.json it was given for: any change there (ours, a field someone added, a failed earlier
// trust) or a trust entry gone from config.toml means the hook is trusted again; otherwise a run costs two reads.
const stampOf = (home: string) => `${home}/.overenie-gate-trusted`;
const digest = (home: string) => new Bun.CryptoHasher("sha256").update(readFileSync(`${home}/hooks.json`)).digest("hex");

// Trusts the hook through Codex's own app-server, the way its /hooks screen does, so the hash is Codex's own.
async function trust(home: string) {
  const proc = Bun.spawn(["codex", "app-server"], {
    env: { ...process.env, CODEX_HOME: home }, stdin: "pipe", stdout: "pipe", stderr: "ignore",
  });
  const waiting = new Map<number, (result: Reply) => void>();
  const call = (id: number, method: string, params: object) =>
    new Promise<Reply>((resolve) => {
      waiting.set(id, resolve);
      proc.stdin.write(JSON.stringify({ id, method, params }) + "\n");
      proc.stdin.flush();
    });
  void (async () => {
    let buf = "";
    for await (const chunk of proc.stdout) {
      buf += new TextDecoder().decode(chunk);
      const lines = buf.split("\n");
      buf = lines.pop() ?? "";
      for (const line of lines) {
        const msg = JSON.parse(line);
        waiting.get(msg.id)?.(msg.error ? { error: msg.error } : msg.result);
      }
    }
  })();
  // install.sh runs under `timeout 60` with steps after this one, so a stuck app-server must not take it all
  const timer = setTimeout(() => { proc.kill(); warn(`${home}: app-server did not answer`); process.exit(1); }, 15_000);
  try {
    await call(0, "initialize", { clientInfo: { name: "karchi-codex-hooks", version: "1" } });
    proc.stdin.write(JSON.stringify({ method: "initialized" }) + "\n");
    const list = async () => ((await call(Date.now(), "hooks/list", { cwds: [HOME] })).data ?? [])
      .flatMap((e) => e.hooks)
      .filter((h) => h.command === COMMAND);
    const ours = await list();
    const todo = ours.filter((h) => h.trustStatus !== "trusted");
    if (todo.length) {
      const value = Object.fromEntries(todo.map((h) => [h.key, { trusted_hash: h.currentHash }]));
      const res = await call(2, "config/batchWrite", {
        edits: [{ keyPath: "hooks.state", value, mergeStrategy: "upsert" }], reloadUserConfig: true,
      });
      if (res?.error) throw new Error(JSON.stringify(res.error));
    }
    const after = await list();
    const ok = after.length > 0 && after.every((h) => h.trustStatus === "trusted");
    if (ok) console.log(`codex-hooks: ${home}: Stop hook trusted`);
    else warn(`${home}: NOT trusted: ${JSON.stringify(after)}`);
    return ok;
  } finally {
    clearTimeout(timer);
    proc.kill();
  }
}

if (!Bun.which("codex")) process.exit(0);
let failed = false;
for (const home of process.argv.length > 2 ? process.argv.slice(2) : homes()) {
  try {
    wire(home);
  } catch (e) {
    warn(`${home}/hooks.json: ${e}`);
    failed = true;
    continue;
  }
  const sum = digest(home);
  const trusted = readFileSync(`${home}/config.toml`, "utf8").includes(`"${home}/hooks.json:stop:`);
  if (trusted && existsSync(stampOf(home)) && readFileSync(stampOf(home), "utf8") === sum) continue;
  if (await trust(home)) writeFileSync(stampOf(home), sum);
  else failed = true;
}
process.exit(failed ? 1 : 0);
