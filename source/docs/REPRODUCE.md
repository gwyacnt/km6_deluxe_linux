# Reproduce checkpoint v0.2.0-rc2

This checkpoint preserves the working **Android-default 15-second menu** and
internal Debian desktop. It predates the proposed USB-presence selection rule.
The source tag alone is not an OS image: use its matching release assets.

## Downloads

From [v0.2.0-rc2](https://github.com/gwyacnt/km6_deluxe_linux/releases/tag/v0.2.0-rc2):

- `km6-debian-desktop-installer.img.xz`: clean persistent Debian USB image.
- `km6-installer-bundle.tar.xz`: partition metadata, initramfs and installer sources used in that image.
- `packages.tsv`: installed Debian package versions.
- `SHA256SUMS`: hashes of these assets.

The same release also includes `modified-km6.img`,
`KM6-QTT2.200903.001-V4.20201026.img` and `V3_setup_V3.1.6.exe`.
No older release or separate upstream image/tool download is required.
The tagged `source/reproduce.py` downloads these pinned assets and writes the
USB image on a Linux PC using Python 3, without another image-writing program.
See the root README for the exact commands and host requirements.

## Short installation path

**Supported target:** the tested KM6 Deluxe Rev2, S905X4, 4 GB RAM, 64 GB eMMC
with model A1511X and the recorded stock Android layout. This is not a generic
Amlogic installer. The packaged USB installer is not yet end-to-end hardware
validated; the underlying internal installation and boot configuration are.

1. If the device is not already on our modified Android firmware, flash
   `modified-km6.img` with USB Burning Tool. On this unit, boot recovery without
   external media and wipe/factory-reset afterward, then verify Android starts.
   Flashing and factory reset erase Android user data.
2. Verify `SHA256SUMS`, decompress the installer, and write the **whole `.img`**
   to an 8 GB or larger USB stick using the included `source/reproduce.py --usb DEVICE --write` tool (with sudo). This erases that stick.
3. With the KM6 powered off, insert the stick, connect a keyboard, hold reset
   and apply power. The clean image is designed to ask for a new password for
   user `samer` on the HDMI console, then start Xfce. The password also serves
   as the sudo password. Verify Ethernet, display and sound before installing.
4. In the USB desktop terminal, run:

   ```sh
   sudo km6-install-internal --apply
   ```

   This validates the exact original layout, backs up metadata on the USB,
   shrinks Android data to 32 GiB, creates a 256 MiB Linux boot partition and
   approximately 23 GiB Debian root, copies the USB system, checks it, and
   enables the timed boot menu. Keep power connected until it reports completion.
5. Shut down, remove the stick and power on normally. Android is the default;
   select Debian with the keyboard when desired. No reset button is needed.

Without `--apply`, the installer validates the target without writing eMMC.
It deliberately refuses an already installed internal layout. Do not use it
as an update command on the current working device. If an installation stops,
preserve `/root/km6-internal-work` on the USB and its backups before retrying.

## What is preserved

The image contains Debian, the tested kernel and Ethernet/audio drivers,
initramfs/menu, Xfce/LightDM, Firefox, uBlock Origin, enhanced-h264ify,
performance defaults, Tailscale and installed system packages. It retains the
automatic audio route and the separate Android/Debian storage design.

The public image intentionally contains no personal Firefox profile or logins,
password hashes, SSH host/admin keys or Tailscale identity. First boot creates
fresh credentials and SSH host keys. After installation, sign in to your own
tailnet with `sudo tailscale up --advertise-exit-node` and approve its exit-node
role in the Tailscale admin console. Forwarding configuration is included.
Tailscale runs when Debian runs, not while Android is selected.

TigerVNC is installed but its service is disabled in the clean image because
the existing private VNC password/profile is excluded. The physical HDMI
desktop starts automatically. VNC can be configured separately afterward.

## Source and image maintenance

Check out the exact source with:

```sh
git clone --branch v0.2.0-rc2 https://github.com/gwyacnt/km6_deluxe_linux.git
```

`usb/export_installer.py` makes a sanitized USB image from a working internal
installation. Its input bundle is supplied as a release asset, so it does not
depend on the author's private `archive/` directory. On the KM6, extract the
bundle and run the exporter as root with `--bundle /path/to/bundle` and a new
`--output /var/lib/km6-image-build-new` directory. It needs free space for the
staging tree and image. It modifies only its build directory and loop devices
backed by that image; it does not repartition the running device.

The kernel/base system originates from
[devmfc/debian-on-amlogic](https://github.com/devmfc/debian-on-amlogic), using
`Devmfc_Debian-Trixie_6.18.49-meson64_Minimal-26.09.02.img.xz`.
This is a reproducible binary installation snapshot plus our maintained
customization source, **not a complete from-source kernel/distribution build**.
Upstream does not publish every part of that build. Package versions and the
supplied kernel/modules are preserved in the release.

## Why no single Android-flasher ROM yet?

A raw eMMC backup is not an Amlogic USB Burning Tool image. A combined burning
image would need packaging and testing of the new Android partition metadata,
Linux filesystems and initial boot environment. That flash path has not been
validated. This checkpoint supplies the existing Android flash plus a prepared
USB installer rather than labeling an untested combined ROM as working.
