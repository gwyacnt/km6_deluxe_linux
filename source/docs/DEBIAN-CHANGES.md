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
