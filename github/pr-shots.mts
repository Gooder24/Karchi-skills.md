#!/usr/bin/env node
// pr-shots: puts the screenshots of a UI change into the PR's description, so the PR on GitHub shows every screen
// the change touches (skill github, "UI changes").
//
//   pr-shots <pr> <after-dir> [--before <before-dir>] [--dry-run]
//
// Run in the PR's checkout. Every PNG in <after-dir> is one screen, in file-name order (01-noty.png, 02-…). With
// --before, a PNG of the same name there is put next to it as one image, "before: main" left and "after: this PR"
// right (ImageMagick); a screen the base does not have gets a gray "not on main" half. Captions come from the file
// names (01-noty-klarinet → "noty klarinet"), or from <after-dir>/captions.tsv ("01-noty<TAB>Noty with the chips").
// The images go to the orphan branch `pr-shots` under pr<N>/<head sha>/ (never into the PR's branch or main), and
// the section between <!-- pr-shots --> and <!-- /pr-shots --> of the PR body is replaced with them; without the
// markers it goes in above the closing "Generated with" / "Created with" line.
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, writeFileSync, copyFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join, resolve } from "node:path";
import { die, repoOf, sh } from "./flow.mts";

const args = process.argv.slice(2);
let before = "", dry = false;
const pos: string[] = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--before") before = resolve(args[++i] ?? die("--before bez priečinka"));
  else if (args[i] === "--dry-run") dry = true;
  else if (args[i] === "-h" || args[i] === "--help") { console.log("pr-shots <pr> <after-dir> [--before <before-dir>] [--dry-run]"); process.exit(0); }
  else pos.push(args[i]);
}
const [pr, afterArg] = pos;
if (!pr || !/^\d+$/.test(pr) || !afterArg) die("pr-shots <pr> <after-dir> [--before <before-dir>]");
const after = resolve(afterArg);
const shots = readdirSync(after).filter((f) => f.endsWith(".png")).sort();
if (!shots.length) die(`v ${after} nie je žiadne PNG`);

const repo = repoOf();
const view = JSON.parse(sh("gh", ["pr", "view", pr, "-R", repo.full, "--json", "body,headRefOid,baseRefName"]).out) as { body: string; headRefOid: string; baseRefName: string };
const head = view.headRefOid.slice(0, 7);
const dir = `pr${pr}/${head}`;
const captions = new Map<string, string>();
if (existsSync(join(after, "captions.tsv"))) {
  for (const line of readFileSync(join(after, "captions.tsv"), "utf8").split("\n")) {
    const [k, ...v] = line.split("\t");
    if (k && v.length) captions.set(k.replace(/\.png$/, ""), v.join("\t"));
  }
}
const caption = (f: string) => captions.get(f.replace(/\.png$/, "")) ?? f.replace(/\.png$/, "").replace(/^\d+-/, "").replace(/-/g, " ");

const work = mkdtempSync(join(tmpdir(), "pr-shots-"));
try {
  const out = join(work, "repo", dir);
  mkdirSync(out, { recursive: true });
  const font = sh("fc-match", ["-f", "%{file}", "sans:bold"], { allowFail: true }).out;
  const half = (img: string, label: string, color: string) => [
    "(", img, "-resize", "900x2400>", "-gravity", "north", "-background", "#fff", "-splice", "0x44",
    ...(font ? ["-font", font] : []), "-pointsize", "26", "-fill", color, "-annotate", "+0+8", label, ")",
  ];
  for (const f of shots) {
    if (!before) { copyFileSync(join(after, f), join(out, f)); continue; }
    const was = join(before, f);
    const left = existsSync(was)
      ? half(was, `before: ${view.baseRefName}`, "#a33")
      : ["(", "-size", "900x200", "xc:#ddd", "-gravity", "center", ...(font ? ["-font", font] : []), "-pointsize", "26", "-fill", "#555", "-annotate", "+0+0", `not on ${view.baseRefName}`, ")"];
    sh("magick", [...left, ...half(join(after, f), "after: this PR", "#262"), "-background", "#bbb", "-gravity", "north", "+smush", "6", join(out, f)]);
  }
  const url = (f: string) => `https://github.com/${repo.full}/blob/pr-shots/${dir}/${encodeURIComponent(f)}?raw=true`;
  const section = [
    "<!-- pr-shots -->",
    `**How it looks** (${before ? `before and after, ` : ""}every screen this PR changes, at ${head})`,
    "",
    ...shots.flatMap((f) => [`${caption(f)}`, "", `![${caption(f)}](${url(f)})`, ""]),
    "<!-- /pr-shots -->",
  ].join("\n");
  let body = view.body;
  const marked = /<!-- pr-shots -->[\s\S]*?<!-- \/pr-shots -->/;
  if (marked.test(body)) body = body.replace(marked, section);
  else {
    const lines = body.split("\n");
    const sig = lines.findLastIndex((l) => /Generated with|Created with/.test(l));
    if (sig >= 0) lines.splice(sig, 0, section, "");
    else lines.push("", section);
    body = lines.join("\n");
  }
  if (dry) { console.log(section); process.exit(0); }

  // the orphan branch: fetched shallow when it exists, so this stays quick however many PRs it holds
  const git = (a: string[], allowFail = false) => sh("git", a, { cwd: join(work, "repo"), allowFail });
  git(["init", "-q"]);
  git(["remote", "add", "origin", `https://github.com/${repo.full}.git`]);
  if (git(["fetch", "-q", "--depth", "1", "origin", "pr-shots"], true).ok) git(["reset", "-q", "FETCH_HEAD"]);
  else git(["checkout", "-q", "--orphan", "pr-shots"]);
  git(["add", dir]);
  git(["-c", "user.name=pr-shots", "-c", "user.email=pr-shots@users.noreply.github.com", "commit", "-q", "-m", `PR #${pr} at ${head}: ${shots.length} screens`]);
  git(["push", "-q", "origin", "HEAD:refs/heads/pr-shots"]);
  const file = join(work, "body.md");
  writeFileSync(file, body);
  sh("gh", ["pr", "edit", pr, "-R", repo.full, "--body-file", file]);
  console.log(`PR #${pr}: ${shots.length} screens at ${head} in the description (${basename(after)})`);
} finally {
  rmSync(work, { recursive: true, force: true });
}
