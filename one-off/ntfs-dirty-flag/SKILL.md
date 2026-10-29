---
name: ntfs-dirty-flag
description: Fix an external NTFS disk that Linux mounts only read-only because the volume is flagged dirty ("Volume is scheduled for check"), without losing data - check the hardware, back up the NTFS metadata, rehearse ntfsfix on a copy, repair, verify. Builds on the recovery-storage skill. One-off, used once in October 2026.
---

# NTFS disk flagged dirty

The disk was unplugged without ejecting (or Windows found an error), so NTFS carries a "scheduled for check"
flag. ntfs-3g then refuses a read-write mount. The fix is one command, `ntfsfix -d`; everything around it
makes sure it runs on the right disk, on healthy hardware, with a way back.

Used once (2026-10): a 1 TB 2.5" HDD in a USB enclosure, about 240 000 files, no full copy possible because
no 1 TB destination was free. Repair succeeded, nothing lost.

## Rules

- First decide the layer. Healthy hardware + dirty flag = filesystem problem, software can fix it. Pending or
  reallocated sectors, I/O errors in the kernel log, clicking = hardware: stop, image with ddrescue
  (recovery-storage `imaging-ddrescue`), never repair on the source.
- Identify the disk by serial, never by `/dev/sdX`; the name can change on every replug.
- Nothing writes to the disk before the data that matters is copied and checked, and a metadata backup exists.
- `ntfsfix` is not `chkdsk`. It fixes the basics, resets the journal and clears the flag. When a Windows
  machine is at hand, `chkdsk X: /f` there is the better repair.

## Steps

```sh
DEV=/dev/sdX; PART=${DEV}1; B=$HOME/disk-backup; mkdir -p "$B"   # keep everything under $HOME: /tmp is wiped on reboot
```

1. **Identify and lock.** `lsblk -dno NAME,SERIAL,SIZE,MODEL,TRAN "$DEV"`, write down the serial.
   `sudo blockdev --setro "$DEV" "$PART"`. The lock is lost on reboot and replug: re-check with `lsblk -o NAME,RO`.
2. **Hardware.** `sudo smartctl -d sat -H -A -l error "$DEV"` (`-d sat` for most USB bridges) and
   `sudo journalctl -k -b | grep -iE 'sdX|I/O error|reset'`. Must be 0: 5 Reallocated, 197 Pending,
   198 Offline_Uncorrectable, 187 Reported_Uncorrect. 199 UDMA_CRC = cable/USB, not the disk. Huge raw values in
   1 Raw_Read_Error_Rate and 7 Seek_Error_Rate are normal on Seagate (compare VALUE with THRESH).
   192 Power-Off_Retract_Count shows how often power was cut while running, i.e. unplugged without eject.
3. **Confirm the flag.** `sudo ntfsinfo -m "$PART"` says "Volume is scheduled for check".
   `sudo ntfsfix -n "$PART"` is a dry run and must end with "processed successfully".
4. **Copy what matters.** `sudo mount -t ntfs-3g -o ro,norecover "$PART" /mnt/x`, `rsync -a` it off, verify with
   `rsync -rcn src/ dst/` (no output = identical). `df -h /mnt/x` tells how big a full copy would be.
5. **Metadata backup** (when a full image does not fit). Reads only; stores the MFT, journal, boot sectors and
   everything else `ntfsfix` can touch, no file contents (a few hundred MB for ~250 000 files):
   ```sh
   sudo ntfsclone --metadata --save-image --force --preserve-timestamps --output "$B/meta.ntfsclone" "$PART"
   sudo dd if="$DEV" of="$B/first-1MiB.bin" bs=1M count=1
   sha256sum "$B"/* > "$B/SHA256SUMS"
   ```
   ntfsclone also checks the cluster bitmap and aborts on an inconsistency: a clean run is extra evidence.
6. **Test-restore the backup.** It becomes a sparse file of the full volume size that stores only the metadata
   (needs a filesystem with sparse files, e.g. ext4, btrfs, xfs):
   ```sh
   sudo ntfsclone --restore-image --output "$B/meta.img" "$B/meta.ntfsclone"
   sudo mount -t ntfs-3g -o ro,loop,norecover "$B/meta.img" /mnt/r && sudo find /mnt/r -xdev | wc -l; sudo umount /mnt/r
   ```
   The count is the reference for step 9.
7. **Rehearse on the copy.** Stop here if any check fails; the disk is still untouched.
   ```sh
   cp --reflink=auto "$B/meta.img" "$B/fix.img"                  # instant on btrfs/xfs, stays sparse elsewhere
   sudo ntfsfix -d "$B/fix.img"                     # same output you expect on the disk
   sudo ntfsinfo -m "$B/fix.img" | grep Flags       # Volume Flags: 0x0000
   sudo ntfs-3g.probe --readwrite "$B/fix.img"      # exit 0 = a read-write mount would work
   sudo mount -t ntfs-3g -o ro,loop "$B/fix.img" /mnt/r && sudo find /mnt/r -xdev | wc -l; sudo umount /mnt/r
   ```
8. **Repair.** Check again that the serial matches, `lsblk -no PKNAME "$PART"` is the disk and
   `findmnt "$PART"` is empty. Then `sudo blockdev --setrw "$DEV" "$PART"` (if still locked) and
   `sudo ntfsfix -d "$PART"`. The output must match the rehearsal.
9. **Verify.** `ntfsinfo -m` shows `Volume Flags: 0x0000`; a normal `mount -o ro` (without `norecover`) works;
   `find | wc -l` equals the count from step 6; `rsync -rcn` against the copies from step 4 shows nothing;
   read a random sample of big files to the end
   (`find /mnt/x -type f -iname '*.jpg' -print0 | shuf -z -n 25 | xargs -0 cat >/dev/null`, no error output);
   SMART counters unchanged; no new errors in `journalctl -k`. Delete `meta.img` and `fix.img`, keep the backup.
10. **Prevent it.** Eject before unplugging: `udisksctl power-off -b "$DEV"`, on Windows "Safely Remove".

## With recovery-storage

[recovery-storage](https://github.com/DungGramer/recovery-storage) adds identity checks, a case record and a
guard hook that blocks writing commands until a gate is confirmed. It has no license: install it from its
repo (pin a commit you have read), do not copy it into this repo. Traps it had on Linux:

- `sudo rs.py` puts the case store in `/root/.recovery-storage`, but the guard reads the user's
  `~/.recovery-storage`, so it never sees a gate. Always run
  `sudo python3 <skill>/scripts/rs.py --json --home "$HOME/.recovery-storage" ...`, then
  `sudo chown -R "$USER": "$HOME/.recovery-storage"`.
- The repair is gate kind `fs-repair-on-source` (R2): `session set <sid> --ceiling R2`, then data state
  `secured` (a full ddrescue mapfile) or `waived --reason ...`, typed by the owner in an interactive terminal.
- The guard blocks every `ntfsfix`, even `--version` and a run on an image file: read the manual with
  `zcat /usr/share/man/man8/ntfsfix.8.gz`, rehearse (step 7) only after `gate confirm`. It checks a whole
  Bash command before it starts, so `gate confirm` and `ntfsfix` go in separate commands. It does not match
  `blockdev`.
- Before `collect`, inventory may class a USB HDD as `usb-flash-or-card`; after `collect` it is `external-hdd`.
  Your own `blockdev --setro` plus the symptom `read-only` produce a false `write-locked` hypothesis: say so in
  `session note`.
- Waiver and `gate confirm` need a TTY so the agent cannot confirm for the owner. Only when the owner says in
  chat that the agent may do it: write that into `session note` first, then feed the answer through a
  pseudo-terminal, e.g. `printf 'YES\n' | script -qec "sudo python3 ... session data-state ..." /dev/null`.
- A PASS verdict for an HDD needs an extended SMART self-test (hours). Without it, leave the verdict unset.
