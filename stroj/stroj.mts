#!/usr/bin/env node
// stroj: is a machine of Karchi's up, and if not, why. Agents ask this before calling a machine asleep or offline.
//
//   stroj [x270|asus|dell|e540]...     (no argument: all four)
//
// One line per machine. A single ssh timeout is not proof: a Tailscale path that sat idle can take tens of
// seconds to come back, so stroj first wakes it with `tailscale ping`, then tries ssh twice.
// Exit 0: every machine asked answers over ssh. 1: at least one does not.
import { spawnSync } from "node:child_process";
import { hostname } from "node:os";

const MACHINES = { x270: "100.96.23.116", asus: "100.110.180.15", dell: "100.75.99.86", e540: "100.86.221.66" } as const;
type Alias = keyof typeof MACHINES;
const isAlias = (a: string): a is Alias => a in MACHINES;

const run = (cmd: string, args: string[], timeoutMs: number) => {
  const t0 = Date.now();
  const r = spawnSync(cmd, args, { encoding: "utf8", timeout: timeoutMs });
  return { ok: r.status === 0, out: `${r.stdout ?? ""}${r.stderr ?? ""}`.trim(), s: ((Date.now() - t0) / 1000).toFixed(1) };
};

type Peer = { Online?: boolean; LastSeen?: string; TailscaleIPs?: string[] };
const peers = (): Peer[] => {
  const r = run("tailscale", ["status", "--json"], 10_000);
  if (!r.ok) return [];
  const d = JSON.parse(r.out) as { Self?: Peer; Peer?: Record<string, Peer> };
  return [...(d.Self ? [d.Self] : []), ...Object.values(d.Peer ?? {})];
};

const ago = (iso: string) => {
  const min = Math.round((Date.now() - Date.parse(iso)) / 60_000);
  return min < 120 ? `${min} min` : min < 2880 ? `${Math.round(min / 60)} h` : `${Math.round(min / 1440)} d`;
};

const check = (alias: Alias, all: Peer[]) => {
  if (hostname().startsWith({ x270: "karchi", asus: "asus", dell: "dell", e540: "thinkpad-e540" }[alias])) return `${alias}: online (toto je on)`;
  const ip = MACHINES[alias];
  const peer = all.find((p) => p.TailscaleIPs?.includes(ip));
  const ping = run("tailscale", ["ping", "-c", "3", "--timeout", "5s", ip], 25_000);
  const pong = ping.out.match(/pong from .* via (\S+) in (\S+)/);
  for (let i = 0; i < 2; i++) {
    const s = run("ssh", ["-o", "BatchMode=yes", "-o", "ConnectTimeout=15", alias, "true"], 30_000);
    if (s.ok) return `${alias}: online (ssh ${s.s} s${pong ? `, ${pong[1]} ${pong[2]}` : ""})`;
    if (i === 1) {
      const why = s.out.split("\n").pop() || "timeout";
      if (pong) return `${alias}: Tailscale odpovedá (${pong[1]}), ale ssh nie: ${why}`;
      // LastSeen is only fresh once Tailscale has marked the peer offline; while it still says online, the machine just dropped.
      const state = peer?.Online === false
        ? peer.LastSeen && !peer.LastSeen.startsWith("0001") ? `, Tailscale ho vedie ako offline, naposledy videný pred ${ago(peer.LastSeen)}` : ", Tailscale ho vedie ako offline"
        : ", práve zmizol (Tailscale ho ešte vedie ako online: uspatý, zavretý alebo bez siete)";
      return `${alias}: nedostupný – neodpovedá na Tailscale ping ani ssh${state}`;
    }
  }
  return `${alias}: ?`;
};

const asked = process.argv.slice(2);
const bad = asked.filter((a) => !isAlias(a));
if (bad.length) {
  console.error(`neznámy stroj: ${bad.join(", ")} (pozná ${Object.keys(MACHINES).join(", ")})`);
  process.exit(2);
}
const all = peers();
let down = false;
for (const alias of asked.length ? asked.filter(isAlias) : (Object.keys(MACHINES) as Alias[])) {
  const line = check(alias, all);
  if (!line.includes(": online")) down = true;
  console.log(line);
}
process.exit(down ? 1 : 0);
