# Accessibility

This repository is a set of Markdown skill files, and people read them on GitHub. Clear headings, descriptive links and text alternatives let a screen reader user find the setup steps and the skill list, and let a contributor check a change without rendering it. This file says what we check, how to report a barrier, and what has not been tested yet.

## Priorities

- **Readable Markdown:** headings in order, link text that names the destination, alt text for any image, tables with header rows.
- **Plain language in the README:** the first paragraph says what the project is, and acronyms a reader may not know are spelled out on first use.
- **No meaning by colour alone** in the files this repository keeps.

This repository has no interface of its own, so we do not claim a WCAG conformance level. The pages on github.com belong to GitHub.

## Contributor expectations

Before you open a pull request:

- Run `python3 .github/scripts/check-docs.py`. It must exit with 0.
- Do not add entries to `.github/a11y-baseline.json` to make the check pass. Fix the problem, or open an issue for it.
- Do not skip heading levels (`##` followed by `####`).
- Do not use link text such as "here", "click here", "link", "read more" or "source 1".
- Give every image alt text, and describe a diagram in the text next to it.
- Give every table a header row.
- Complete the accessibility checklist in the pull request template.

`AGENTS.md` is linked into the owner's machines, and the existing skills are in use. The owner reviews changes to them before they are merged.

## Reporting an accessibility barrier

Open an issue with the [accessibility barrier form](.github/ISSUE_TEMPLATE/accessibility.yml), or a blank issue if the form does not suit you. Issues from the form get the `accessibility` label.

Useful details, when you can share them:

- What you were trying to do, and what went wrong.
- The file path and line, or the github.com page address.
- Your browser or terminal, your operating system, and your assistive technology with its version.
- A screenshot, if you want to share one. Describe what it shows in words too.

You do not need to say whether you have a disability.

### Severity

- **Critical:** you cannot complete a task you need, for example you cannot read the setup steps at all.
- **Serious:** you can complete the task, but only with a workaround.
- **Moderate:** the barrier makes the task slower or less consistent.
- **Minor:** the barrier has little effect on the task.

### How we respond

The owner reads new accessibility issues, labels their severity, and says what happens next in the issue. The repository has no guaranteed response time, because one person maintains it. When a fix lands, the issue says what changed, and we may ask you to confirm that the fix works before we close it.

## Ownership

Accessibility is owned by **Gooder24**, the repository owner. The owner is responsible for:

- triaging accessibility issues and setting their severity,
- tracking open barriers and the checks listed below,
- keeping this file and `.github/a11y-baseline.json` current.

## Supported environments

- **Reading the files:** any text editor, and github.com in a desktop browser.
- **Checks:** Python 3 for `check-docs.py`; Node.js 18 or later and Python 3 for the skill tests. The workflow runs on Ubuntu 24.04.
- **Tested:** the checks were run locally on Debian 13 with bash.
- **Screen reader:** Orca 48.1 with Chromium 156 on Debian 13, on GitHub's rendering of `README.md` and this file (see Testing).
- **Not tested:** Windows, macOS, mobile browsers, NVDA, VoiceOver and braille displays.

## Known limitations

- **The screen reader check was a transcript, not a person listening.** It shows the words Orca says, not how a voice pronounces the paths and symbols in code. NVDA and VoiceOver, which [issue #3](https://github.com/Gooder24/Karchi-skills.md/issues/3) asked for, are not tested.
- **One link with non-descriptive text:** `[source 14]` in `avoid-ai-design/references/ai-tells-catalog.md`. Tracked in [issue #2](https://github.com/Gooder24/Karchi-skills.md/issues/2).
- **The automated check is narrow.** It looks at heading order, alt text and link text. It does not read table contents, judge plain language, or check colour contrast on github.com.

## Testing

**Automated:** [`.github/workflows/accessibility.yml`](.github/workflows/accessibility.yml) runs `check-docs.py` on every pull request and every push to `main` that changes a Markdown file or the check itself. It fails on a problem that is not in `.github/a11y-baseline.json`. The baseline is empty: the current files have no known problems of the kinds it checks.

**Keyboard-only check:** not applicable. The repository has no interface of its own; the steps in the README run in a terminal, and the pages on github.com are GitHub's.

**Screen reader spot check (19 November 2026):** Orca 48.1 with speech-dispatcher 0.12.0 and Chromium 156 on Debian 13, on `README.md` and this file as GitHub renders them. An agent ran it with [`citacka`](citacka/SKILL.md), which writes down the text Orca sends to the synthesizer, with the down arrow through the page, then by heading, link and table cell. The transcripts are in [this gist](https://gist.github.com/Gooder24/21335fd6bc7198ec801381064bc82925).

- Every heading is read with its level, followed by GitHub's "Permalink" link.
- The skill table is announced with its number of rows and columns, and each cell is read with its column header, "Skill" or "What it does". Each skill link is read as its name, and its description follows in the next cell.
- Hard to follow: the JSON of the hook wiring is read symbol by symbol, and paths in code are read in pieces (`~ / . claude / settings . json`). The `weft` row began with the bare command name and was read as "weft weft"; it is reworded.
- To repeat it: `citacka README.md --mode lines,headings,links,tables`.

**Manual documentation checks:** every table has a header row, every code block is fenced, and no file contains an image or embedded HTML. Zoom, reflow and colour contrast are GitHub's; we have not tested them.

## Dependencies

The repository depends on bash, git, Python 3, and Node.js 18 or later for the `avoid-ai-design` detector. None of them is an interface. The third-party skills listed in the README (`frontend-design`, `avoid-ai-design`, and the [tstack](https://github.com/t3dotgg/tstack) skills such as `full-send` and `file-pr`) have not been reviewed for accessibility. Before a new third-party skill is added, run `check-docs.py` on its Markdown and list it in the README. Known upstream blockers: none recorded.

## Community

- **Ways to help:** issues labelled [`good first issue`](https://github.com/Gooder24/Karchi-skills.md/labels/good%20first%20issue) have a small scope and a clear done-when. Issues labelled [`help wanted`](https://github.com/Gooder24/Karchi-skills.md/labels/help%20wanted) need outside expertise. See [CONTRIBUTING.md](CONTRIBUTING.md).
- **Ways to take part:** everything happens asynchronously, in GitHub issues and pull requests. We offer no meetings or chat. If you need a different format, ask in an issue; you do not need to explain why.
- **Code of conduct:** none yet.
- **Recognition:** we credit an accessibility contribution in the issue or pull request that fixes it, if the contributor wants that. We ask how each person wants to be named, and we do not mention disability, assistive technology or other personal details without permission.
- **Progress updates:** there is no fixed schedule yet. When a check or a fix lands, the Known limitations section changes in the same pull request.
- **Shared resources:** [`.github/scripts/check-docs.py`](.github/scripts/check-docs.py) needs only Python 3 and git and works on any repository of Markdown files. It reads its baseline from `.github/a11y-baseline.json`. The owner keeps it current.
