# KM6 Deluxe Android / Debian dual boot

Enable USB Linux boot on the tested Mecool KM6 Deluxe Rev2 (HDMI-marked chassis, S905X4, 4 GB RAM, 64 GB eMMC), while retaining the stock Android firmware components.

## Current status

Android TV and the Debian Xfce desktop both boot from separate internal eMMC
areas on the tested KM6 Deluxe Rev2 (S905X4, 4 GB RAM, 64 GB A1511X eMMC).
Debian boot with the USB stick removed was confirmed on HDMI and over SSH.
On current main, any external USB device (including the receiver) selects
internal Debian automatically. Without USB, the menu defaults to Android after
15 seconds. Both cold-boot paths were confirmed on September 11, 2026.
Ethernet, HDMI display/audio and Tailscale work in Debian; Ethernet reliability
after warm restarts remains an open issue. See [the developer handoff](docs/HANDOFF.md).

**Checkpoint: `v0.2.0-rc4`.** See [the reproduction guide](docs/REPRODUCE.md)
and its matching GitHub release for the prepared USB installer and checksums.
The device setup is hardware-tested. The newly packaged clean installer still
needs a fresh USB boot and complete installation test; it is a release candidate.
This checkpoint includes the current USB-presence automatic-selection rule.

Firefox uses Panfrost/WebRender, but video decoding remains software-only.
The desktop defaults to 720p without Xfce compositing; `km6-desktop-mode sharp`
selects 1080p. See [performance measurements](performance/README.md).
Ethernet currently negotiates 100 Mbps/full duplex with the tested router;
Gigabit operation, the infrared remote and CoreELEC remain unverified.

## Why modify the firmware?

The stock reset/recovery FAT loader invokes `autoscr`, but its U-Boot command table provides `source` and lacks `autoscr`. The firmware patch replaces that invocation and updates the required integrity fields. Only 81 actual bytes change; stock board configuration, partition layout and Android components are retained. Reference firmware supports the alias but fails flashing compatibility checks on this KM6.

## From stock to USB boot

1. Use the exact confirmed stock image identified in `manifests/releases.json`. The similarly named ATV image is not the baseline.
2. Use Amlogic USB Burning Tool 3.1.6 to flash the modified image from the firmware release. The tested download connection uses the black USB 2.0 port. See the original investigation for hardware context; detailed flasher UI instructions are still to be consolidated.
3. On the tested device, both stock and modified firmware required recovery/factory reset after flashing before Android setup worked. Boot without external media while holding reset to reach recovery. Factory reset erases Android user data.
4. Prepare the customized Devmfc Debian USB image, insert it with power disconnected, connect Ethernet/HDMI, hold reset and apply power. The tested Debian image reaches a terminal. Ethernet and stereo HDMI audio configure automatically; no manual setup script is needed.

## Folder organization

The enclosing workspace has three directories:

- `archive/`: private recovery backups and historical investigation material; ignored by Git.
- `releases/`: staged firmware, flasher, Debian installer and checksums for release upload; ignored by Git.
- `source/`: this maintained source tree and documentation, tracked by Git.

The root `.gitignore` allows the root README, AGENTS.md, itself and `source/`. The root README contains the restoration instructions.

## Build source

`firmware/` contains the firmware patcher. `usb/` contains boot sources, original upstream boot files, rootfs configuration and image customization scripts. `drivers/maxio/` contains driver source and its original community version. `drivers/sc2-audio/` contains the HDMI audio drivers, device-tree additions and automatic mixer configuration. `diagnostics/` retains the optional manual test; the historical installer is not required or recommended for normal startup.

Run `python3 source/bootstrap_build.py` from the repository root to download
and verify public build inputs from the same release. Then run
`python3 source/build.py`. These use ignored `build/`, not `archive/`. See
[build instructions](docs/BUILD-STATUS.md) for host requirements and outputs.

Upstream: https://github.com/devmfc/debian-on-amlogic . Our base is `Devmfc_Debian-Trixie_6.18.49-meson64_Minimal-26.09.02.img.xz`. We preserve our customization source; some upstream sources/build scripts are unavailable, so this is not a complete from-source OS build.

See `docs/DEBIAN-CHANGES.md`, `THIRD_PARTY.md` and `docs/REPOSITORY-PLAN.md` for details.
