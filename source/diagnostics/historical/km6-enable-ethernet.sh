#!/bin/sh
# Install the tested module only into the running Debian USB system.
set -eu
kernel=6.18.49-meson64
[ "$(id -u)" = 0 ] || { echo 'Run as root.'; exit 1; }
[ "$(uname -r)" = "$kernel" ] || { echo 'Kernel mismatch; stopped.'; exit 1; }
rootdev=$(findmnt -n -o SOURCE /)
parent=$(lsblk -ndo PKNAME "$rootdev")
[ -n "$parent" ] && [ "$(lsblk -ndo TRAN "/dev/$parent" | tr -d ' ')" = usb ] || {
 echo 'Root filesystem is not verified as USB; stopped.'; exit 1;
}
cd /boot
sha256sum -c km6-maxio.ko.sha256
backup=/var/backups/km6-maxio
mkdir -p "$backup" "/lib/modules/$kernel/extra"
module="/lib/modules/$kernel/extra/maxio.ko"
config=/etc/modules-load.d/km6-maxio.conf
# Preserve any prior files once; repeated runs do not overwrite backups.
for f in "$module" "$config"; do
 if [ -e "$f" ] && [ ! -e "$backup/$(basename "$f").before" ]; then
  cp -p "$f" "$backup/$(basename "$f").before"
 fi
done
install -m 0644 /boot/km6-maxio.ko "$module"
depmod -a "$kernel"
printf '# KM6 Maxio Ethernet PHY; built for 6.18.49-meson64\nmaxio\n' > "$config"
printf 'Installed Ethernet driver for %s on USB.\n' "$kernel"
sync
# Bring Ethernet up now using the tested sequence, without rebooting.
sh /boot/km6-maxio-test.sh
printf '\nLeave the KM6 powered on and connected to Ethernet for SSH.\n'
