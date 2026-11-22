---
name: android
description: The Android emulator on asus (pixel8_api35, Android 15, Pixel 8 screen 1080x2400) that agents drive and Karchi watches in T3's Device panel. Use whenever a task needs an Android phone - testing a web page or PWA in mobile Chrome, offline behaviour, installing and trying an APK, a screenshot or recording from a phone - and to set the emulator up on another machine.
---

# Android emulator

asus has the Android SDK in `~/Android/Sdk` and one emulator, `pixel8_api35`: Android 15 with Google APIs
(Chrome, no Play Store, `adb root` works), a Pixel 8 screen (1080x2400, 420 dpi), 2 GB RAM and 2 cores. T3
finds the SDK there on its own; `adb` and `emulator` are on PATH in login shells (`~/.profile`).

## Using it

1. `device_list`, then `device_open` with host `local` and device `pixel8_api35`. That boots it without a
   window (about 30 s cold) and shows it in Karchi's Device panel, on any machine running the T3 app.
2. Every tap, text, app launch, screenshot and recording goes through the `agent-device` command that
   `device_open` returns, so he sees what you do. `adb` only for installs, logs, port forwards and
   things agent-device cannot do (for example `adb reverse tcp:5173 tcp:5173` so the phone reaches a dev
   server on asus at `http://localhost:5173`, or `adb shell svc wifi disable` / `svc data disable` to go
   offline, then `enable` again).
3. When you are done: `device_close` with `shutdown: true`. A running emulator takes about 3 GB of RAM;
   two at once do not fit next to the other agents.

## Setting it up

`android/setup.sh` installs the SDK, the system image and the AVD and adds the PATH lines. It is safe to
run again. It needs `/dev/kvm` (the `kvm` group); ARM machines and Windows are not covered. The x270 has
only 2 cores, so it watches the asus emulator in the Device panel instead of running its own.
