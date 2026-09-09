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

The module built against the matching 6.18.49 headers. Offline libkmod testing reproduced the original built-in state and confirmed the new name is not built in. File-content checks, service/shell validation and the filesystem check passed. On 2026-09-09 the user reported an Ethernet IP address after booting revision 2. Subsequent SSH and startup-log verification is recorded below.

References: https://github.com/systemd/systemd/blob/main/src/shared/module-util.c and https://docs.kernel.org/kbuild/kbuild.html .

## Revision 2 hardware verification — 2026-09-09

Read-only SSH inspection confirmed the expected KM6 MAC and kernel, with `/` and `/boot` mounted from the USB disk. Internal eMMC was not mounted. The automatically saved boot report shows `km6_maxio` loading at 4.397 seconds, the MAE0621A driver attached at 5.927 seconds, and Ethernet link up at 9.024 seconds. DHCP and SSH worked without a manual driver command. The diagnostic service completed successfully and systemd reported no failed units.

Router ping returned three responses with no loss; Debian mirror DNS resolution and clock synchronization worked. This is not a throughput or long-term stability test. The link negotiated 100 Mbps/full duplex. ethtool shows the KM6 advertising 1000baseT, while the link partner advertises only 10/100 Mbps. Check the connected router/switch port and connection before attributing this limit to the KM6 driver. Gigabit operation remains unverified. Raw reports and host-key pinning are retained only in the ignored archive.

## Revision 3: automatic stereo HDMI audio

Add the SC2 audio clock, FRDDR_A, TDMOUT_C, TDM C interface and HDMI routing nodes in a separate DTB. Preserve the original DTB and all its existing properties. The custom HDMI component uses the SC2 clock/data gates (bits 28/29) and TDM C MCLK settings. The adapted AXG sound-card driver recognizes the SC2 component as a codec-to-codec link. Both modules are built against the original 6.18.49 kernel headers; the kernel image is unchanged.

Integration builds this audio source, installs both modules with regenerated dependency indexes and modules-load configuration, enables km6-audio-route.service, and selects the audio DTB in boot.config. The original boot.config is preserved alongside it for rollback. The automatic service configures the mixer without playing anything.

On 2026-09-09 the physical KM6 loaded all three custom drivers automatically, obtained Ethernet/SSH, and completed silent PCM transfers. The user then confirmed that both stereo test tones sounded clear. Tested format: 48 kHz, S16_LE, two channels. No other audio format or long-duration playback is claimed. The assembled revision 3 image passed file-content, module-dependency and ext4 consistency checks; a fresh flash/boot of that complete image remains untested.
