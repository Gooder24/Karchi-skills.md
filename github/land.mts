#!/usr/bin/env node
// land: merges a pull request only when CI passed on its current head, in one call (way 2 of skill github):
//
//   land PR [-R owner/repo] [--method merge|squash|rebase] [--yes-work] [--wait MIN]
//
// Refuses drafts and closed PRs, updates a branch that is behind its base and waits for CI again, merges with
// --match-head-commit (a push while waiting makes GitHub refuse), deletes the branch and syncs a local checkout
// of the base. A repo with scripts/land.sh (Partsheet) lands only through that script. Exit 0: merged.
// 1: not merged because CI failed, the branch conflicts or the wait ran out. 2: refused or bad arguments.
import { existsSync } from "node:fs";
import { join } from "node:path";
import { die, repoOf, sh, waitForCi, WORK_REPOS } from "./flow.mts";

const args = process.argv.slice(2);
let pr = "", repo = "", method = "", yesWork = false, wait = 30;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "-R" || a === "--repo") repo = args[++i] ?? "";
  else if (a === "--method") method = args[++i] ?? "";
  else if (a === "--yes-work") yesWork = true;
  else if (a === "--wait") wait = Number(args[++i]);
  else if (a === "-h" || a === "--help") { console.log("land PR [-R owner/repo] [--method merge|squash|rebase] [--yes-work] [--wait MIN]"); process.exit(0); }
  else if (!pr && !a.startsWith("-")) pr = a;
  else die(`neznáma voľba ${a}`);
}
const fromUrl = /github\.com\/([^/]+\/[^/]+)\/pull\/(\d+)/.exec(pr);
if (fromUrl) [repo, pr] = [fromUrl[1], fromUrl[2]];
if (!/^\d+$/.test(pr)) die("land PR: číslo alebo URL pull requestu");
const inside = sh("git", ["rev-parse", "--show-toplevel"], { allowFail: true });
repo ||= inside.ok ? repoOf(inside.out).full : die("mimo checkoutu daj -R owner/repo");
if (WORK_REPOS.has(repo.split("/")[1].toLowerCase()) && !yesWork) die(`${repo} je pracovné repo eSYST: najprv sa spýtaj Karchiho, potom land --yes-work`);
if (inside.ok && repoOf(inside.out).full === repo && existsSync(join(inside.out, "scripts/land.sh"))) {
  const r = sh(join(inside.out, "scripts/land.sh"), [pr], { cwd: inside.out, allowFail: true });
  console.log(r.out || r.err);
  process.exit(r.ok ? 0 : 1);
}

type Pr = { state: string; isDraft: boolean; headRefOid: string; baseRefName: string; headRefName: string; mergeable: string; url: string; isCrossRepository: boolean };
const view = () => JSON.parse(sh("gh", ["pr", "view", pr, "-R", repo, "--json", "state,isDraft,headRefOid,baseRefName,headRefName,mergeable,url,isCrossRepository"]).out) as Pr;
let p = view();
if (p.state !== "OPEN") die(`${p.url} je ${p.state}, nie je čo zlúčiť`);
if (p.isDraft) die(`${p.url} je draft`);
for (let round = 0; ; round++) {
  if (p.mergeable === "CONFLICTING") { console.log(`${p.url} má konflikt s ${p.baseRefName}; vyrieš ho v jeho vetve a pushni, potom land znova`); process.exit(1); }
  const behind = Number(sh("gh", ["api", `repos/${repo}/compare/${p.baseRefName}...${p.headRefOid}`, "-q", ".behind_by"]).out);
  if (behind > 0) {
    if (round > 2) { console.log(`${p.url} stále zaostáva za ${p.baseRefName}`); process.exit(1); }
    console.log(`${p.headRefName} zaostáva o ${behind} commit(y), aktualizujem vetvu`);
    sh("gh", ["pr", "update-branch", pr, "-R", repo]);
    for (let i = 0; i < 20 && view().headRefOid === p.headRefOid; i++) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 3000);
    p = view();
    continue;
  }
  if (!waitForCi(repo, p.headRefOid, wait)) process.exit(1);
  const again = view();
  if (again.headRefOid === p.headRefOid) break;
  p = again; // someone pushed while CI ran: test the new head
}
const allowed = JSON.parse(sh("gh", ["api", `repos/${repo}`, "-q", "{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}"]).out) as Record<string, boolean>;
method ||= ["merge", "squash", "rebase"].find((m) => allowed[m]) ?? "merge";
const merged = sh("gh", ["pr", "merge", pr, "-R", repo, `--${method}`, "--match-head-commit", p.headRefOid, ...(p.isCrossRepository ? [] : ["--delete-branch"])], { allowFail: true, cwd: inside.ok ? inside.out : undefined });
if (!merged.ok) die(`gh pr merge zlyhal:\n${merged.err}`, 1);
console.log(`zlúčené ${p.url} (${method}, ${p.headRefOid.slice(0, 7)})`);
if (inside.ok && sh("git", ["branch", "--show-current"], { cwd: inside.out }).out === p.baseRefName) {
  const pull = sh("git", ["pull", "-q", "--rebase", "--autostash"], { cwd: inside.out, allowFail: true });
  console.log(pull.ok ? `lokálny ${p.baseRefName} je aktuálny` : `lokálny ${p.baseRefName} sa nepodarilo aktualizovať: ${pull.err}`);
}
