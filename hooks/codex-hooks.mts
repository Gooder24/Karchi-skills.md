#!/usr/bin/env bun
// Wires the overenie-gate Stop hook into every Codex home on this machine (~/.codex and T3's ~/.codex-t3code/<account>)
// and trusts it, since Codex skips a user hook until it is trusted. install.sh runs this; safe to run again: a home whose
// hooks.json already holds the hook and whose config.toml already trusts it costs one file read.
// Usage: codex-hooks.mts [codex home …]     (default: every home on this machine)
// Way out: delete the Stop entry from <home>/hooks.json; `codex` → /hooks shows what is wired and trusted.
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";

const HOME = process.env.HOME ?? "";
const COMMAND = `python3 -I ${HOME}/.work/karchi-skills/hooks/overenie-gate.py`;
type Handler = { type: string; command?: string; timeout?: number };
type Hooks = { hooks?: Record<string, { matcher?: string; hooks: Handler[] }[]> };

function homes() {
  const t3 = `${HOME}/.codex-t3code`;
  const accounts = existsSync(t3) ? readdirSync(t3).map((a) => `${t3}/${a}`) : [];
  return [`${HOME}/.codex`, ...accounts].filter((h) => existsSync(`${h}/config.toml`));
}

// Adds the handler to hooks.json, keeping any other hooks there. Returns whether the file changed.
function wire(home: string) {
  const path = `${home}/hooks.json`;
  const config: Hooks = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {};
  const stop = ((config.hooks ??= {}).Stop ??= []);
  if (stop.some((g) => g.hooks.some((h) => h.command === COMMAND))) return false;
  stop.push({ hooks: [{ type: "command", command: COMMAND, timeout: 10 }] });
  writeFileSync(path, JSON.stringify(config, null, 2) + "\n");
  return true;
}

// Trusts the hook through Codex's own app-server, the way its /hooks screen does, so the hash is Codex's own.
async function trust(home: string) {
  const proc = Bun.spawn(["codex", "app-server"], {
    env: { ...process.env, CODEX_HOME: home }, stdin: "pipe", stdout: "pipe", stderr: "ignore",
  });
  const waiting = new Map<number, (result: unknown) => void>();
  const call = (id: number, method: string, params: object) =>
    new Promise<any>((resolve) => {
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
  const timer = setTimeout(() => { proc.kill(); console.error(`codex-hooks: ${home}: app-server did not answer`); process.exit(1); }, 60_000);
  try {
    await call(0, "initialize", { clientInfo: { name: "karchi-codex-hooks", version: "1" } });
    proc.stdin.write(JSON.stringify({ method: "initialized" }) + "\n");
    const list = async () => ((await call(Date.now(), "hooks/list", { cwds: [HOME] })).data ?? [])
      .flatMap((e: { hooks: { key: string; command?: string; currentHash: string; trustStatus: string }[] }) => e.hooks)
      .filter((h: { command?: string }) => h.command === COMMAND);
    const ours = await list();
    const todo = ours.filter((h: { trustStatus: string }) => h.trustStatus !== "trusted");
    if (todo.length) {
      const value = Object.fromEntries(todo.map((h: { key: string; currentHash: string }) => [h.key, { trusted_hash: h.currentHash }]));
      const res = await call(2, "config/batchWrite", {
        edits: [{ keyPath: "hooks.state", value, mergeStrategy: "upsert" }], reloadUserConfig: true,
      });
      if (res?.error) throw new Error(JSON.stringify(res.error));
    }
    const after = await list();
    const ok = after.length > 0 && after.every((h: { trustStatus: string }) => h.trustStatus === "trusted");
    console.log(`codex-hooks: ${home}: ${ok ? "Stop hook trusted" : "NOT trusted: " + JSON.stringify(after)}`);
    return ok;
  } finally {
    clearTimeout(timer);
    proc.kill();
  }
}

if (!Bun.which("codex")) process.exit(0);
let failed = false;
for (const home of process.argv.length > 2 ? process.argv.slice(2) : homes()) {
  const changed = wire(home);
  const config = readFileSync(`${home}/config.toml`, "utf8");
  if (!changed && config.includes(`"${home}/hooks.json:stop:`)) continue;
  if (!(await trust(home))) failed = true;
}
process.exit(failed ? 1 : 0);
