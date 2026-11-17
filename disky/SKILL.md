---
name: disky
description: What is on each of Karchi's disks (Ľuptákovci, Seagate 500 GB, the old WD, asus ~/zaloha) and how to keep that current. Use when he asks which disk has what, where some photos or a backup are, what is on a disk, or when one of his external disks is connected to a machine (refresh its overview before or after any copy).
---

# Disky

The overview lives on asus in `~/zaloha/disky/` (from another machine: `ssh asus`). `README.md` lists every
known disk (serial, filesystem UUID, what it is, where it is, date of the last list) and links each disk's
`prehlad.md`: top folders and their subfolders with file counts, sizes and kinds (fotky, videá, hudba, dokumenty,
archívy). The full file list is `zoznam-<date>.jsonl.gz` next to it (`path`, `bytes`); search it with
`zcat … | rg` when he asks for a specific file or folder.

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
