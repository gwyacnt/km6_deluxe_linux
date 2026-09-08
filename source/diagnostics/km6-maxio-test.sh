#!/bin/sh
# Manual, volatile driver test. No kernel, firmware or eMMC installation.
set -u
if [ "$(id -u)" != 0 ]; then echo 'Run as root.'; exit 1; fi
if [ "$(uname -r)" != '6.18.49-meson64' ]; then echo 'Kernel version mismatch; stopped.'; exit 1; fi
phy=/sys/bus/mdio_bus/devices/mdio_mux-0.0:00
id=$(cat "$phy/phy_id" 2>/dev/null)
case "$id" in 0xffff4411|0x7b744411) ;; *) echo "Unexpected PHY ID: $id; stopped."; exit 1;; esac
report=/boot/km6-maxio-test.txt
(
 echo 'KM6 manual Maxio driver test'; date -Is; uname -a
 echo "Original PHY ID: $id"
 echo 'Original PHY driver:'; readlink "$phy/driver"
 ip link set eth0 down
 if ! grep -q '^maxio ' /proc/modules; then
  if ! insmod /boot/km6-maxio.ko; then
   echo 'MODULE LOAD FAILED'; dmesg; exit 1
  fi
 fi
 # Failed stmmac open has disconnected the PHY. Reprobe only if still
 # bound to Generic PHY; leave any specific hardware driver untouched.
 driver=$(readlink "$phy/driver" 2>/dev/null || true)
 case "$driver" in
  */Generic\ PHY)
   printf '%s' 'mdio_mux-0.0:00' > "$phy/driver/unbind"
   printf '%s' 'mdio_mux-0.0:00' > /sys/bus/mdio_bus/drivers_probe
   ;;
 esac
 echo 'PHY driver after module load:'; readlink "$phy/driver"
 timeout 20 ip link set eth0 up
 networkctl reconfigure eth0
 sleep 20
 echo '--- Interfaces ---'; ip -br link; ip -br address; ip route
 echo '--- PHY ---'; cat "$phy/phy_id"; readlink "$phy/driver"
 echo '--- Status ---'; timeout 15 networkctl status eth0 --no-pager
 echo '--- Kernel log ---'; dmesg
) > "$report" 2>&1
sync
printf 'Saved %s\n' "$report"
ip -br address
