# Karchi's taste

Derived from 163 messages that Karchi wrote to Claude in 66 conversations (as of 2026-10-12).
Most of them concern his desktop (KarchiOS, Hyprland, ThinkPad X270), so that is where his taste is
best documented. The quotes in parentheses are his own words (translated from Slovak). Everything else
is Claude's interpretation. When Karchi says something different in the current conversation, what he
says now applies.

## Look

- **Pixel art is the identity.** Icons, widgets and apps should match the system's pixel-art theme and
  change along with it ("so the whole thing matches my computer with the pixelart", "it's part of
  my distro so it'll change according to the pixelart").
- **No square-cornered elements, except the pixel art itself.** The bar, the widgets and the file manager
  should be rounded ("the bar looks bad when it's all square"). He wants to be able to set the amount of
  rounding: natural, or pixel-style.
- **Built in, not stuck on next to it.** A new feature belongs inside what already exists ("I want to have
  kalendarix built right into the calendar I have in the widget, not next to it as an icon").
- **A polished presentation.** A functional but bare listing is not enough ("nicer… not just so primitive").

## Less is more

- What he does not use should not be visible and should not even load: no wallpaper picker, no trash in
  the file manager, no status icon for a running service, no sounds he did not choose.
- Nothing should be created on its own without asking ("I don't want categories like documents or work
  to always get created there automatically").
- One purpose, one way ("no other options… only this").
- Closed means closed. An app should not keep running in the background after it is closed.

## Controls

- **Keyboard first.** Every frequent action should have an easy shortcut (Super+Tab,
  Super+Shift+Enter, F9 without Fn). If the shortcut is taken, remove the original binding and put the new one there.
- **The main action is right at hand.** When a window opens, the selection is on the main button, it is
  triggered with Space or Enter, and the arrow keys reach everything.
- **Do not take the focus or the cursor.** After a panel closes, the cursor should stay where it was in the
  last application.
- **Automation instead of clicking** ("it's pretty unconvenient if I had to click a button, if it got
  triggered automatically when I finish that part"). A sensible default should apply itself
  as soon as it opens; manual adjustment stays possible.
- **Settings belong in Settings.** What he wants to tune (touchpad sensitivity, rounding, battery
  mode) should be visible and selectable in the UI, not in a config file.
- **Directly readable information** alongside a smart shortcut: the Wi-Fi password as text, not just a QR code.
- **Context-aware controls.** Brightness changes only on the monitor where the cursor is.
- **Use the whole screen** and page through with a touchpad gesture.

## Performance and reliability

- **Frugality is a requirement, not a bonus.** With every new tool he asks "does it eat a lot of RAM
  or compute?" and wants it to "not eat a lot of battery/resources". Give him a lightweight solution and tell
  him its consumption before he asks.
- **Speed.** He rejects slow things even when they are otherwise good ("that extension is slow… otherwise it's
  excellent"). He does not like the Firefox engine; he uses Chromium-based browsers (Helium, Brave Origin).
- **It must always work** ("so that any workspaces can always be opened and it never happens that
  I can't open it").
- **Data must not contradict itself.** A battery indicator that does not match the batteries is "total chaos".
  The volume in the player should match the system volume.
- **Smoothness.** No jumps between steps, no flickering.
- **A permanent solution, not a temporary patch** ("are these solutions we're doing temporary, or will
  everything work for me after this setup?"). If something is temporary, say so up front.

## Information and content

- **Chronological, not algorithmic.** He wants RSS from newest to oldest, not a feed that
  adapts itself to him.
- **Generic AI summaries are "kinda meh".** He prefers the original source and specific news, "I don't want
  to waste time".
- **Do not embellish.** In reports about himself, point out the negatives and the positives equally openly.
- **Real numbers for the whole period**, not a slice. When data is missing, say exactly what is missing and why.
- Open source takes precedence. A local solution takes precedence over the cloud, where possible.

## How to work with him

- **Language:** Slovak, informal, brief. He himself writes tersely and with slang.
- **Finish it for him.** He delegates fully and does not want to deal with details ("I don't want to get into it,
  I need you to do it", "can't you do it for me?"). He likes to leave work running overnight.
- **When he narrows the scope, stick to it** ("don't do anything with the asus server, right now I only need to sort out the usb").
- **When he has to do something himself, give him exact commands and values to type in**, not an explanation
  of the principle ("give me the commands I have to run").
- **Verify first, then build.** With ideas he first wants research into whether it already exists; with
  optimization, measurement first. When choosing, he wants a comparison and decides himself ("compare and I'll decide").
- **A demo as soon as possible.** Rather a fast working prototype than long planning.
- **He gives feedback in rounds**, often as a screenshot with one sentence. Fix exactly what it
  shows, and do not add anything extra.
- **Changes in his personal projects** (karchi-os, karchi-skills) are committed straight to `main` and pushed:
  no branches or pull requests, they only piled up (2026-10-19). Work projects get their own workflow, not yet
  agreed. Desktop changes belong in his distro (KarchiOS), not just on one computer, and he wants to hear
  whether a change works right away or only after a restart.

## Finding and moving his files

His files are spread over x270, asus, dell, e540, folder backups of old machines and external disks. On
2026-10-24 "do you have the songbook files and some SQL dumps here?" took five rounds and ended with "wtf,
all it took was for me to word it right". One short request should be enough: work out what it is for
(that time: real data in the test site on dell) and get there in one go.

- **"Do you have X?" means "find X wherever I keep it".** Before saying it is not there, read the project
  memory files themselves (not just the index; another thread may have changed them), then search every
  machine you can reach. Reading on his machines is part of the request; changing anything there still
  needs his word.
- **Search all of it.** On btrfs `/home` is its own mount, so `find / -xdev` skips it: search each mount
  from `findmnt` and any plugged-in disk. Match names case-insensitively, with and without diacritics.
- **"The asus backup" is a folder, not the machine**, e.g. `~/ZALOHA-ASUS-Vivobook_2026-10-10` on x270.
- **Check the content, not the name.** A `.sql` file is the dump he wants only if it holds that project's
  tables and data.
- **"Move it" means copy it there and finish the job.** Keep the source until he says to delete it, then do
  what the data is for (a dump: import it into the test database and run the migrations). Do not answer
  with a menu of options; "compare and I'll decide" is for choosing tools and designs. If the real source
  cannot be reached (a disk that is not plugged in), do everything else and end with one sentence on what
  is missing and the one thing he has to do.
