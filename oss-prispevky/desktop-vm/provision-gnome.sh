#!/usr/bin/env bash
# Inside a fresh Arch, Debian 13 or Fedora 44 cloud VM (as root, run by `dvm.sh DISTRO provision gnome`):
# GNOME on Wayland with GDM autologin for $DVM_USER, no screen lock or idle blanking, Nautilus and
# wl-clipboard for clipboard interop, then the app's package when one is given.
#   provision-gnome.sh [/path/to/app.deb|app.rpm|app.pkg.tar.zst]
set -euxo pipefail
user=${DVM_USER:-tester} pkg=${1:-}
. /etc/os-release
case $ID in
  debian)
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y gnome-core gdm3 nautilus wl-clipboard fuse3 python3 dconf-cli
    [[ -n $pkg ]] && apt-get install -y "$pkg"
    gdm=/etc/gdm3/daemon.conf ;;
  fedora)
    # unoconv needs libreoffice-pyuno, so it goes with LibreOffice.
    dnf -y install @workstation-product-environment -x 'libreoffice*' -x unoconv
    dnf -y install wl-clipboard fuse3 python3
    [[ -n $pkg ]] && dnf -y install "$pkg"
    gdm=/etc/gdm/custom.conf ;;
  arch)
    pacman -Syu --noconfirm gnome-shell gdm nautilus gnome-console wl-clipboard fuse3 python dconf mesa vulkan-swrast
    [[ -n $pkg ]] && pacman -U --noconfirm "$pkg"
    systemctl enable gdm
    gdm=/etc/gdm/custom.conf ;;
  *) echo "unsupported $ID"; exit 1 ;;
esac
mkdir -p "$(dirname "$gdm")"
cat > "$gdm" <<CONF
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=$user
WaylandEnable=true
CONF
mkdir -p /etc/dconf/profile /etc/dconf/db/local.d
printf 'user-db:user\nsystem-db:local\n' > /etc/dconf/profile/user
cat > /etc/dconf/db/local.d/00-test-vm <<CONF
[org/gnome/desktop/session]
idle-delay=uint32 0
[org/gnome/desktop/screensaver]
lock-enabled=false
[org/gnome/desktop/lockdown]
disable-lock-screen=true
[org/gnome/desktop/notifications]
show-banners=false
[org/gnome/shell]
welcome-dialog-last-shown-version='999'
[org/gnome/settings-daemon/plugins/power]
sleep-inactive-ac-type='nothing'
CONF
dconf update
install -d -o "$user" -g "$user" "/home/$user/.config"
echo yes > "/home/$user/.config/gnome-initial-setup-done"
chown "$user:$user" "/home/$user/.config/gnome-initial-setup-done"
systemctl set-default graphical.target
