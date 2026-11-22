#!/usr/bin/env bash
# Installs the Android SDK and the pixel8_api35 emulator into ~/Android/Sdk, where T3's Device panel finds it.
# Safe to run again. Needs KVM (/dev/kvm and the kvm group), about 5 GB of disk and 3 GB of free RAM to run.
set -euo pipefail
SDK="$HOME/Android/Sdk"
CLT_ZIP=commandlinetools-linux-15859902_latest.zip
IMAGE="system-images;android-35;google_apis;x86_64"
AVD=pixel8_api35
[ -w /dev/kvm ] || { echo "no write access to /dev/kvm: sudo usermod -aG kvm $USER, then log in again" >&2; exit 1; }
if [ ! -x "$SDK/cmdline-tools/latest/bin/sdkmanager" ]; then
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  curl -fsSL -o "$tmp/clt.zip" "https://dl.google.com/android/repository/$CLT_ZIP"
  unzip -q "$tmp/clt.zip" -d "$tmp"
  mkdir -p "$SDK/cmdline-tools" && mv "$tmp/cmdline-tools" "$SDK/cmdline-tools/latest"
fi
export ANDROID_HOME="$SDK"
bin="$SDK/cmdline-tools/latest/bin"
yes | "$bin/sdkmanager" --licenses >/dev/null || true
"$bin/sdkmanager" --install platform-tools emulator "$IMAGE" >/dev/null
if [ ! -d "$HOME/.android/avd/$AVD.avd" ]; then
  # avdmanager prints a devices.xml error for google_apis images and still creates the AVD.
  echo no | "$bin/avdmanager" create avd -n "$AVD" -k "$IMAGE" -d pixel_8 >/dev/null 2>&1 || true
fi
cfg="$HOME/.android/avd/$AVD.avd/config.ini"
[ -f "$cfg" ] || { echo "AVD $AVD was not created" >&2; exit 1; }
# Pixel 8 screen (1080x2400, 420 dpi), 2 GB RAM and 2 cores so it fits next to the other agents.
for kv in hw.ramSize=2048 hw.cpu.ncore=2 disk.dataPartition.size=8G hw.keyboard=yes; do
  k=${kv%%=*}; grep -q "^$k=" "$cfg" && sed -i "s|^$k=.*|$kv|" "$cfg" || echo "$kv" >> "$cfg"
done
grep -q 'Android/Sdk' "$HOME/.profile" 2>/dev/null || cat >> "$HOME/.profile" <<'P'

# Android SDK (emulator pre agentov, Device panel v T3)
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin"
P
echo "ok: $AVD in $SDK"
