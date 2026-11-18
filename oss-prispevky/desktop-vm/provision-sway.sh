#!/usr/bin/env bash
# Inside a fresh Debian 13 cloud VM (as root, run by `dvm.sh debian provision sway`): a light desktop for a
# small VM (2 GB is enough). sway on Wayland with XWayland off, started by tty1 autologin of $DVM_USER,
# Nautilus for clipboard interop, then the app's .deb when one is given.
#   provision-sway.sh [/path/to/app.deb]
set -euxo pipefail
user=${DVM_USER:-tester} pkg=${1:-}
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends sway swaybg foot nautilus gvfs dbus-user-session \
  wl-clipboard fuse3 python3 mesa-vulkan-drivers libgl1-mesa-dri fonts-dejavu-core xdg-desktop-portal-gtk
[[ -n $pkg ]] && apt-get install -y "$pkg"
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf <<CONF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $user --noclear %I \$TERM
CONF
install -d -o "$user" -g "$user" "/home/$user/.config" "/home/$user/.config/sway"
cat > "/home/$user/.config/sway/config" <<CONF
include /etc/sway/config
output * resolution 1366x768
xwayland disable
CONF
chown "$user:$user" "/home/$user/.config/sway/config"
cat >> "/home/$user/.profile" <<'CONF'
[ "$(tty)" = /dev/tty1 ] && [ -z "$WAYLAND_DISPLAY" ] && exec sway > /tmp/sway.log 2>&1
CONF
