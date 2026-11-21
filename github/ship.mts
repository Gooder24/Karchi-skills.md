#!/usr/bin/env node
// ship: one change straight to main of Karchi's own repo, the way skill github wants it, in one call:
//
//   ship -m "fix(x): title" [-m "body"] [--yes-work] [--no-ci] [--wait MIN] FILE...
//
// Stages exactly FILE... (nothing else may be staged), commits, `git pull --rebase --autostash`, pushes
// and waits for CI on the pushed commit. Exit 0: pushed and CI green or absent. 1: pushed but CI failed or still
// runs (the failed log tail is printed). 2: nothing pushed (refused or a git step failed).
// --yes-work: an eSYST work repo, after Karchi said yes in the thread.
import { existsSync, statSync } from "node:fs";
import { join } from "node:path";
import { die, repoOf, sh, waitForCi, WORK_REPOS } from "./flow.mts";

const args = process.argv.slice(2);
const messages: string[] = [];
const files: string[] = [];
let yesWork = false, ci = true, wait = 20;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "-m") messages.push(args[++i] ?? die("-m bez textu"));
  else if (a === "--yes-work") yesWork = true;
  else if (a === "--no-ci") ci = false;
  else if (a === "--wait") wait = Number(args[++i]);
  else if (a === "-h" || a === "--help") { console.log("ship -m TITLE [-m BODY] [--yes-work] [--no-ci] [--wait MIN] FILE..."); process.exit(0); }
  else if (a.startsWith("-")) die(`neznáma voľba ${a}`);
  else files.push(a);
}
if (!messages.length) die("chýba -m s názvom commitu (conventional commit, napr. fix(web): …)");
if (!files.length) die("vymenuj súbory tejto zmeny; ship nepridáva nič iné");

const top = sh("git", ["rev-parse", "--show-toplevel"]).out;
const repo = repoOf(top);
if (WORK_REPOS.has(repo.name.toLowerCase()) && !yesWork) die(`${repo.full} je pracovné repo eSYST: najprv sa spýtaj Karchiho, potom ship --yes-work`);
const branch = sh("git", ["branch", "--show-current"]).out;
const main = sh("git", ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], { allowFail: true }).out.replace(/^origin\//, "") || "main";
if (branch !== main) die(`si na vetve ${branch || "(detached)"}, ship ide len do ${main}; PR dokonči cez land`);

// Only this change goes out: no local commits waiting to be pushed, and no folders (they would add untracked files).
const ahead = sh("git", ["rev-list", "--count", "@{upstream}..HEAD"], { allowFail: true });
if (!ahead.ok) die(`${main} nemá upstream; nastav ho (git branch -u origin/${main})`);
if (ahead.out !== "0") die(`${main} má ${ahead.out} nepushnutých commitov, ktoré nie sú táto zmena; najprv ich vyrieš (git log @{u}..HEAD)`);
const dirs = files.filter((f) => existsSync(f) && statSync(f).isDirectory());
if (dirs.length) die(`vymenuj súbory, nie priečinky: ${dirs.join(", ")}`);
// Something already staged outside FILE... would ride along in the commit: refuse before touching the index.
const extra = sh("git", ["diff", "--cached", "--name-only", "--", ":/", ...files.map((f) => `:(exclude)${f}`)]).out;
if (extra) die(`v indexe sú aj iné súbory: ${extra.split("\n").join(", ")}; odstráň ich (git restore --staged) alebo ich vymenuj`);
sh("git", ["add", "--", ...files]);
const staged = sh("git", ["diff", "--cached", "--name-only"]).out.split("\n").filter(Boolean);
if (!staged.length) die("žiadna zmena na commit v týchto súboroch");

sh("git", ["commit", "-q", ...messages.flatMap((m) => ["-m", m])]);
for (let attempt = 0; ; attempt++) {
  const pull = sh("git", ["pull", "-q", "--rebase", "--autostash"], { allowFail: true });
  if (!pull.ok) die(`git pull --rebase zlyhal (konflikt?); commit je lokálne, nič nie je pushnuté:\n${pull.err}`);
  const push = sh("git", ["push", "-q"], { allowFail: true });
  if (push.ok) break;
  if (attempt === 1) die(`push zlyhal:\n${push.err}`);
}
const sha = sh("git", ["rev-parse", "HEAD"]).out;
console.log(`pushnuté ${repo.full} ${main} ${sha.slice(0, 7)}: ${messages[0]}`);
if (!ci) process.exit(0);
if (!existsSync(join(top, ".github/workflows"))) { console.log("CI: repo nemá workflow"); process.exit(0); }
process.exit(waitForCi(repo.full, sha, wait) ? 0 : 1);
