#!/usr/bin/env bash
# Desktop test VMs (QEMU/KVM) with a real display, driven over ssh and QMP. From the Atlas port (2026-11).
#
#   dvm.sh DISTRO up             create on first run, boot, wait for ssh
#   dvm.sh DISTRO ssh [cmd]      run a command as user $DVM_USER (default tester, passwordless sudo)
#   dvm.sh DISTRO put SRC DST / get SRC DST
#   dvm.sh DISTRO provision gnome|sway [PKG]   desktop (+ the app's .deb/.rpm) via provision-*.sh, then reboot
#   dvm.sh DISTRO qmp ARGS...    qmp.py on this VM (key, type, click, drag, wheel, shot, settle)
#   dvm.sh DISTRO down           power off
#   dvm.sh DISTRO destroy        power off and delete the VM directory
#
# DISTRO: arch, debian (13), fedora (44); nixos needs an image built by hand (see SKILL.md).
# VMs live in ~/vm/$DVM_NAME-DISTRO (DVM_NAME defaults to oss; one name per project).
# The display is a 1366x768 virtio-vga screen nobody watches; screenshots come from QMP screendump.
# Before `up`: free -h and uptime (AGENTS.md); at most two VMs on asus, none while it compiles.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
distro=${1:?distro}; shift
name=${DVM_NAME:-oss} user=${DVM_USER:-tester}
case $distro in
  arch) port=2222 url=https://geo.mirror.pkgbuild.com/images/latest/Arch-Linux-x86_64-cloudimg.qcow2 ;;
  debian) port=2223 url=https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2 ;;
  fedora) port=2224
    url=https://download.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/x86_64/images/Fedora-Cloud-Base-Generic-44-1.7.x86_64.qcow2 ;;
  nixos) port=2225 ;;
  *) echo "unknown distro $distro" >&2; exit 2 ;;
esac
port=${DVM_PORT:-$port} dir=$HOME/vm/$name-$distro
cpus=${DVM_CPUS:-4} mem=${DVM_MEM:-4096}
ssh_opts=(-i "$dir/id_ed25519" -p "$port" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
  -o LogLevel=ERROR -o ConnectTimeout=5 -o ServerAliveInterval=15)
scp_opts=(-q -r -i "$dir/id_ed25519" -P "$port" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
  -o LogLevel=ERROR)

fetch_base() {
  [[ -f base.qcow2 ]] && return
  curl -fL -o base.part "$url"
  case $distro in
    arch) curl -fsSL "$url.SHA256" | awk '{print $1 "  base.part"}' | sha256sum -c ;;
    debian) curl -fsSL "${url%/*}/SHA512SUMS" | awk -v f="${url##*/}" '$2 == f {print $1 "  base.part"}' | sha512sum -c ;;
    fedora) curl -fsSL "${url%/*}/Fedora-Cloud-44-1.7-x86_64-CHECKSUM" \
      | awk -v f="${url##*/}" '$2 == "(" f ")" {print $4 "  base.part"}' | sha256sum -c ;;
  esac
  mv base.part base.qcow2
}

create() {
  mkdir -p "$dir"; cd "$dir"
  [[ $distro == nixos ]] && { echo "put a NixOS GNOME image at $dir/disk.qcow2 first (SKILL.md)" >&2; exit 1; }
  fetch_base
  [[ -f id_ed25519 ]] || ssh-keygen -q -t ed25519 -N '' -f id_ed25519
  cat > user-data <<UD
#cloud-config
users:
  - name: $user
    groups: [wheel, sudo]
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    plain_text_passwd: $user
    ssh_authorized_keys:
      - $(cat id_ed25519.pub)
UD
  printf 'instance-id: %s-%s-1\nlocal-hostname: %s-%s\n' "$name" "$distro" "$name" "$distro" > meta-data
  cloud-localds seed.iso user-data meta-data
  qemu-img create -q -f qcow2 -b base.qcow2 -F qcow2 disk.qcow2 30G
}

running() { [[ -f $dir/qemu.pid ]] && kill -0 "$(cat "$dir/qemu.pid")" 2>/dev/null; }
wait_ssh() {
  for _ in $(seq 180); do
    ssh "${ssh_opts[@]}" "$user@127.0.0.1" true 2>/dev/null && { echo "VM $distro up on port $port"; return 0; }
    sleep 2
  done
  echo "VM did not answer on ssh; see $dir/serial.log" >&2; return 1
}

case ${1:-} in
  up)
    [[ -f $dir/disk.qcow2 ]] || create
    running && { echo "VM already running (pid $(cat "$dir/qemu.pid"))"; exit 0; }
    seed=(); [[ -f $dir/seed.iso ]] && seed=(-drive "file=$dir/seed.iso,if=virtio,media=cdrom")
    qemu-system-x86_64 -enable-kvm -cpu host -smp "$cpus" -m "$mem" \
      -drive "file=$dir/disk.qcow2,if=virtio" "${seed[@]}" \
      -nic "user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:$port-:22" \
      -device virtio-rng-pci -device virtio-vga,xres=1366,yres=768 \
      -device qemu-xhci -device usb-tablet -device usb-kbd \
      -display none -qmp "unix:$dir/qmp.sock,server=on,wait=off" \
      -serial "file:$dir/serial.log" -daemonize -pidfile "$dir/qemu.pid"
    wait_ssh ;;
  ssh) shift; exec ssh "${ssh_opts[@]}" "$user@127.0.0.1" "$@" ;;
  put) exec scp "${scp_opts[@]}" "$2" "$user@127.0.0.1:$3" ;;
  get) exec scp "${scp_opts[@]}" "$user@127.0.0.1:$2" "$3" ;;
  provision)
    kind=${2:?gnome or sway}; pkg=${3:-}
    scp "${scp_opts[@]}" "$here/provision-$kind.sh" "$user@127.0.0.1:/tmp/"
    remote_pkg=""
    if [[ -n $pkg ]]; then scp "${scp_opts[@]}" "$pkg" "$user@127.0.0.1:/tmp/"; remote_pkg=/tmp/${pkg##*/}; fi
    ssh "${ssh_opts[@]}" "$user@127.0.0.1" sudo DVM_USER="$user" bash "/tmp/provision-$kind.sh" $remote_pkg
    ssh "${ssh_opts[@]}" "$user@127.0.0.1" sudo systemctl reboot || true
    sleep 5; wait_ssh ;;
  qmp) shift; exec python3 "$here/qmp.py" "$dir/qmp.sock" "$@" ;;
  down)
    running || exit 0
    ssh "${ssh_opts[@]}" "$user@127.0.0.1" sudo systemctl poweroff 2>/dev/null || true
    for _ in $(seq 60); do running || { rm -f "$dir/qemu.pid"; exit 0; }; sleep 1; done
    kill "$(cat "$dir/qemu.pid")"; rm -f "$dir/qemu.pid" ;;
  destroy) "$0" "$distro" down; rm -rf "$dir" ;;
  *) sed -n '2,15p' "$0"; exit 2 ;;
esac
