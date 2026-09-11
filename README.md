# KM6 Deluxe: Android TV + internal Debian

**Restore checkpoint: [v0.2.0-rc2](https://github.com/gwyacnt/km6_deluxe_linux/releases/tag/v0.2.0-rc2).**
All required images and the Amlogic flasher are attached to **that same release**.
The USB-writing tool and installation source are in this tag. No files from a
different release or the author's private working folder are required.

This checkpoint provides a 15-second boot menu with **Android as default** and
Debian as the second choice. Both operating systems use internal eMMC. It
does **not** contain the later proposed USB-presence automatic-selection rule.

## Reproduce the setup

The supported device is the tested **KM6 Deluxe Rev2, S905X4, 4 GB RAM, 64 GB
A1511X eMMC**. Debian desktop boot without a USB stick, Ethernet and HDMI audio
are confirmed on it. The packaged installer is still a release candidate:
fresh-media boot and a complete installation using that package remain untested.

1. Get the tagged source:

   ```sh
   git clone --branch v0.2.0-rc2 https://github.com/gwyacnt/km6_deluxe_linux.git
   cd km6_deluxe_linux
   python3 source/reproduce.py --download-all
   ```

   This downloads and verifies the images, flasher and installer bundle from
   this release. Files are saved under `downloads/v0.2.0-rc2/`.

2. If the box is not already running our modified Android firmware, use the
   included `V3_setup_V3.1.6.exe` Amlogic USB Burning Tool to flash
   `modified-km6.img`. The tested download connection uses the black USB 2.0
   port. Flashing erases the device. On this KM6, boot recovery without a stick
   while holding reset, perform a factory reset, and confirm Android starts.
   The unmodified stock ROM is included as a recovery option.

3. On a **Linux PC with Python 3**, connect an 8 GB or larger USB stick and
   identify its device name with `lsblk`. Unmount its partitions first. Then:

   ```sh
   sudo python3 source/reproduce.py --usb /dev/sdb --write
   ```

   Replace `/dev/sdb` with the actual stick. This erases that USB stick and
   verifies the written image. The supplied script replaces the need to obtain
   a separate USB image-writing application. It refuses internal disks,
   mounted devices and partitions supplied instead of whole disks.

4. Power off the KM6, insert the stick, connect a keyboard, hold reset and
   apply power. Set a new password for `samer` at the HDMI prompt. In the
   Debian desktop terminal, install to internal storage:

   ```sh
   sudo km6-install-internal --apply
   ```

   After it reports completion, shut down, remove the stick and power on
   normally. The menu will default to Android; choose Debian when wanted.

The Android flasher is a Windows executable; a compatible environment is
needed to run it. Python 3 and the host operating systems themselves are host
requirements, not bundled operating-system installers. No upstream Devmfc
image download, compiler or driver-building tools are needed for this restore.

## Included in this release

| File | Purpose |
| --- | --- |
| `modified-km6.img` | Android firmware with working external boot support |
| `KM6-QTT2.200903.001-V4.20201026.img` | Exact stock recovery ROM |
| `V3_setup_V3.1.6.exe` | Matching Amlogic USB Burning Tool |
| `km6-debian-desktop-installer.img.xz` | Prepared persistent Debian USB installer |
| `km6-installer-bundle.tar.xz` | Internal-install scripts, signed partition metadata and initramfs |
| `packages.tsv` | Preserved installed package versions |
| `SHA256SUMS` | Release asset checksums |
| `INSTALL.md` | Detailed restoration instructions |

The public image preserves the desktop, applications, drivers, audio/network
fixes and boot configuration. It removes personal logins, password hashes,
SSH keys and the Tailscale identity. Create fresh credentials and sign into
your own tailnet after restoring. It is not a backup of your private accounts.

See [the detailed tagged reproduction guide](source/docs/REPRODUCE.md),
[hardware/boot design](source/dualboot/README.md) and
[performance settings](source/performance/README.md). This is a binary OS
snapshot with maintained customization source, not a complete from-source
distribution build or a single combined Amlogic burning ROM.
