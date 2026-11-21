---
name: disky
description: What is on each of Karchi's disks (Ľuptákovci, Hitachi „Karol-HP“, Seagate 500 GB, the old WD, asus ~/zaloha) and how to keep that current. Use when he asks which disk has what, where some photos or a backup are, what is on a disk, or when one of his external disks is connected to a machine (refresh its overview before or after any copy), and before planning any copy, wipe or rescue across his disks.
---

# Disky

The overview lives on asus in `~/zaloha/disky/` (from another machine: `ssh asus`). `README.md` lists every
known disk (serial, filesystem UUID, what it is, where it is, date of the last list) and links each disk's
`prehlad.md`: top folders and their subfolders with file counts, sizes and kinds (fotky, videá, hudba, dokumenty,
archívy). The full file list is `zoznam-<date>.jsonl.gz` next to it (`path`, `bytes`); search it with
`zcat … | rg` when he asks for a specific file or folder.

## What goes where (Karchi, 2026-11-21)

- **Ľuptákovci** is the family's disk: family photos and videos, old family computers, and everything from the
  old WD rescue. None of Karol's (Karchi's) own files go there, not even as a second copy.
- Karol's own files (his photos, laptop backups and archives, passwords) go on the Hitachi „Karol-HP“, with
  their second copy on the Seagate 500 GB.

## Answering

Read `README.md`, then the disk's `prehlad.md`. Say which disk and folder, in his words, and the date the list
is from; a list older than the last copy onto that disk is out of date, say so.

## When a disk is connected

1. Identify it by serial and UUID (`lsblk -o NAME,SERIAL,SIZE,FSTYPE,UUID,LABEL`). Never write to it for this.
   NTFS: `sudo -n mount -t ntfs-3g -o ro,norecover,nosuid,nodev,noexec,uid=1000,gid=1000 /dev/disk/by-uuid/<uuid> /mnt/<name>`.
2. `python3 inventar.py <mount> ~/zaloha/disky/<disk>/zoznam-<YYYY-MM-DD>.jsonl.gz`, then
   `python3 prehlad.py <that list> ~/zaloha/disky/<disk>/prehlad.md "<name – what, serial, filesystem>, stav <date>"`
   (both scripts are in this skill folder). Do it again after copying onto the disk.
3. Update the disk's row in `README.md` (a new disk gets a new row and folder). Older lists stay.

## Doing disk work fast

Lessons from the WD rescue and the disk sorting of 8.–18. 11. 2026: 10 days, dozens of his messages, several
verifier rounds lost on wording, and asus filled to 99 %. Each rule below would have saved days.

- **Trust the serial, not the name.** He calls disks loosely (he called the Seagate "Hitachi", and the Hitachi
  "an empty spare" when it held Karol's archive). Before any plan, match the serial to `README.md` and tell him in
  one line which disk it is and what is on it.
- **Plan all disks at once.** Ask once where everything should end up, check free space on every target and on
  asus (`df -h /`), then give him the order of plugging in. asus has one USB adapter: each disk should go in once,
  not five times. When two disks must be compared live, say a second adapter (or a two-bay dock) saves a swap.
- **Hash once, compare from manifests.** Every copy writes `path, bytes, sha256` next to the disk's list. Comparing
  two disks then needs only the disk that is plugged in (the Seagate check on 17. 11. used the Hitachi copy
  record of 10. 11. and saved a swap). A full re-read is needed only right before wiping the other copy.
- **A failing disk: image first, then work only on the image.** One `ddrescue` image with one map file (fast pass,
  then retries on the bad areas), then every extraction, repair and retry reads the image, never the disk again.
  Results go into one folder; intermediate copies are reflinks and get deleted once the result is on two disks.
  On the WD each new attempt made a new full folder (`~/zaloha` reached 176 GB, partly copies of the same WD data).
- **asus is not storage.** Stage on asus only what the next step needs, and keep `df -h /` above 50 GB free.
- **Write only measured facts** in `README.md`, `prehlad.md` and replies: "15 photos found by name and size",
  not "almost everything is only here"; "formatted NTFS, not tried on Windows", not "works on Windows". Every
  stronger word cost a verifier round.
- **The adapter is the bottleneck.** asus's SATA adapter is a JMicron JM20329, USB 2.0 (`lsusb -t`: 480M,
  usb-storage): about 34 MB/s, the Hitachi's 292 GB took 2 h 21 min. A USB 3 adapter with UASP in asus's 10 Gbit
  port would read a 2.5" disk at about 100 MB/s, three times faster; suggest it before any job over 100 GB.
- **Long reads run as one systemd unit with one wait**; tell him the expected time once (bytes / 34 MB/s with
  today's adapter) instead of status turns.
