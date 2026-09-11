# KM6 Deluxe: Android TV + internal Debian

**Restore checkpoint: [v0.2.0-rc3](https://github.com/gwyacnt/km6_deluxe_linux/releases/tag/v0.2.0-rc3).**
All required images and the Amlogic flasher are attached to **that same release**.
The USB-writing tool and installation source are in this tag. No files from a
different release or the author's private working folder are required.

**Current main branch (confirmed September 11, 2026):** any connected external
USB device, including the keyboard/mouse receiver, selects internal Debian
automatically. With no USB device connected, the 15-second menu defaults to
Android. Both paths were confirmed on the device. Ethernet failed after one
warm restart and recovered after removing power; that issue remains open.
The release below includes this USB-selection policy.

**Continue development with Codex:** start with the [developer handoff](source/docs/HANDOFF.md).
The [conversation archive](source/docs/conversation/README.md) preserves the
project discussion. Root [AGENTS.md](AGENTS.md) provides instructions for Codex.

This checkpoint preserves the current boot behavior: **USB connected → Debian;
no USB → 15-second menu, Android default**. Both operating systems use internal
eMMC. Personal credentials and service identities are excluded.

## Reproduce the setup

The supported device is the tested **KM6 Deluxe Rev2, S905X4, 4 GB RAM, 64 GB
A1511X eMMC**. Debian desktop boot without a USB stick, Ethernet and HDMI audio
are confirmed on it. The packaged installer is still a release candidate:
fresh-media boot and a complete installation using that package remain untested.

1. Get the tagged source:

   ```sh
   git clone --branch v0.2.0-rc3 https://github.com/gwyacnt/km6_deluxe_linux.git
   cd km6_deluxe_linux
   python3 source/reproduce.py --download-all
   ```

   This downloads and verifies the images, flasher and installer bundle from
   this release. Files are saved under `downloads/v0.2.0-rc3/`.

2. Start from the original Android partition layout. For a complete rebuild
   of an already dual-booting box, reflash first; the installer is not an updater.
   Use the
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
   apply power. Set a new password for `samer` at the HDMI prompt. Press
   **Ctrl+Alt+F2**, log in as `samer`, and install from that text console:

   ```sh
   sudo km6-install-internal --apply
   ```

   Use the text console because the installer stops the graphical desktop
   while copying Debian. After it reports completion, shut down, remove the
   stick and power on normally. Leave the receiver (or another USB peripheral) connected to start
   Debian automatically. Disconnect all USB devices to get the 15-second
   Android-default menu. No reset button is needed.

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
| `checkpoint-v0.2.0-rc3.json` | Hashes of the working device’s critical files |
| `validation.json` | Packaged-image checks and hardware-test limitations |

The public image preserves the desktop, applications, drivers, audio/network
fixes and boot configuration. It removes personal logins, password hashes,
SSH keys and the Tailscale identity. Create fresh credentials and sign into
your own tailnet after restoring. It is not a backup of your private accounts.

See [the detailed tagged reproduction guide](source/docs/REPRODUCE.md),
[hardware/boot design](source/dualboot/README.md) and
[performance settings](source/performance/README.md). This is a binary OS
snapshot with maintained customization source, not a complete from-source
distribution build or a single combined Amlogic burning ROM.
