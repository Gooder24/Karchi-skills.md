---
name: citacka
description: A transcript of what a screen reader (Orca) says on a web page, a README or a command's output in a terminal, with the `citacka` command on every machine. Use for a screen reader check (an accessibility issue that asks someone to read a README, ACCESSIBILITY.md, a page or a CLI's output with a screen reader), to hear how headings, links and tables sound, and before closing such an issue.
---

# citacka: what the screen reader says

`citacka` (in `~/.local/bin` from `install.sh`) runs Orca in its own Xvfb display and D-Bus session on a
headless machine and saves what it says as text. speech-dispatcher's generic module writes every utterance
to a file instead of a sound card, so the transcript is the text the synthesizer received, not a guess.
Each line is one key press and what Orca said after it.

```
citacka README.md                          GitHub's rendering of the local file (gh api markdown), in Chromium
citacka https://github.com/o/r/blob/main/README.md   any page, with the whole github.com page around it
citacka page.html --mode headings,links    a local HTML file
citacka page.html --mode keys --keys 'Tab Return Escape'   what Orca says after each key (focus, dialogs, live regions)
citacka --terminal 'karchi-doctor'         a command typed into lxterminal; Orca reads the output as it appears
  --mode   page: lines (Down arrow, default), headings (H), links (K), tables (T, then every cell with
           Alt+Shift+arrows), sayall, keys (--keys: xdotool key names from the page as it loads, type:TEXT
           types TEXT); terminal: live,review (default both; review is flat review upwards)
  --out DIR (default ./citacka)  --name NAME  --host HOST  --keep (keep Orca's debug log)
```

- **Where it runs.** Here when `orca`, `Xvfb`, `xdotool` and `speech-dispatcher` are installed (the
  `karchi-headless` package has them from 2026.11.19), otherwise over `ssh e540`; the page or Markdown is
  rendered here and copied there. One run takes 1 to 10 minutes and one Chromium: look at `free -h` first.
  Orca starts only once per user, so runs of one user take turns ("waiting for another citacka run").
- **Settings.** Orca 48 with its defaults, desktop keyboard layout, key echo off. Orca's own debug log stays
  with `--keep`.
- **What it is not.** Orca on Linux with Chromium, not NVDA or VoiceOver. Write the screen reader, its version
  and the browser (the transcript's first lines) next to every result. Sound, voice and speed are not tested.

## A screen reader check

1. Run the modes the check needs. For a README: `--mode lines,headings,links,tables`.
2. Read the transcript as a listener: every heading with its level, every link with a name that says where it
   goes, every table with its size and column headers, code blocks and lists that make sense spoken. Look for
   `(nothing)`, file names spelled out, emoji names, symbols read as words, and repeated text. Orca itself puts
   spaces around symbols inside code (`unattended - upgrades`, `/ run / reboot - required`); whether a voice
   then says "dash" or "slash" depends on the user's punctuation level, which the transcript does not show.
3. Fix what reads badly in the source and run it again until it reads well.
4. Put the transcript where the issue can link to it (a gist, with the machine's IP addresses replaced), write
   the result, the screen reader and its version under Testing in the repository's ACCESSIBILITY.md, and
   close the issue with one sentence and the link. A barrier you cannot fix gets its own issue with the
   `accessibility` label.
