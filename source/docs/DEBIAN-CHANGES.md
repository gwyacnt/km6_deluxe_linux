# Changes to Devmfc Debian

Base release: https://github.com/devmfc/debian-on-amlogic/releases/tag/v6.18.49

Base asset: Devmfc_Debian-Trixie_6.18.49-meson64_Minimal-26.09.02.img.xz
SHA256: 399e3e4ac2cf5ff7416a1ef6940beb364d7b408a69626e25a59fe9c5d2f8219d

- Select s905x4_generic_gigabit and the supplied meson-sc2-ah212-generic-gbit.dtb.
- Replace aml_autoscript, cfgload and s905_autoscript with USB-only source-compatible entries; load scripts at 0x08000000 without saving the environment.
- Replace an upstream bootscript autoscr invocation with source; add diagnostic buffer markers.
- Build the community Maxio MAE0621A driver for kernel 6.18.49-meson64, adapting the PHY callback and EEE APIs and matching the observed PHY ID. Original source is retained beside our version.
- Install the module in /usr/lib/modules/6.18.49-meson64/extra, regenerate module indexes, and add /etc/modules-load.d/km6-maxio.conf.

The initial boot-only image retained the original kernel, rootfs and DTB. The later automatic-Ethernet candidate changes the rootfs and retains that boot partition. An experimental DTB timing adjustment failed and was reverted.

Manual driver loading achieved DHCP at 100 Mbps/full duplex. The automatic candidate produced a reported failed boot step; cause unknown. Its FAT partition omitted the manual diagnostic script. Normal operation is intended to require no manual installation script.

## Automatic Ethernet revision 2

The saved boot journal reports `Module 'maxio' is built in`, followed by Generic PHY binding and the DMA timeout. The upstream `modules.builtin` includes `kernel/drivers/net/phy/maxio.ko`. systemd's module loader checks built-in status and therefore skips insertion of our same-named external module. The old offline modprobe dependency check was insufficient to detect this.

Build the unchanged driver C source as `km6_maxio.ko` and load `km6_maxio` through modules-load.d. Preserve the upstream built-in metadata. Order systemd-networkd after systemd-modules-load. An enabled diagnostic service waits up to 45 seconds for IPv4 and writes `/boot/km6-network-report.txt`, including driver binding, network state and kernel logs. Its optional helper is also present at `/boot/km6-network-report.sh`; no manual command is needed. Journal syncing is shortened to 30 seconds.

The module built against the matching 6.18.49 headers. Offline libkmod testing reproduced the original built-in state and confirmed the new name is not built in. File-content checks, service/shell validation and the filesystem check passed. On 2026-09-09 the user reported an Ethernet IP address after booting revision 2. This is a user-reported result; startup logs and SSH have not yet been inspected.

References: https://github.com/systemd/systemd/blob/main/src/shared/module-util.c and https://docs.kernel.org/kbuild/kbuild.html .
