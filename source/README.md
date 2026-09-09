# KM6 Deluxe USB Linux

Enable USB Linux boot on the tested Mecool KM6 Deluxe Rev2 (HDMI-marked chassis, S905X4, 4 GB RAM, 64 GB eMMC), while retaining the stock Android firmware components.

## Current status

Modified firmware flashes successfully. Android works after recovery/factory reset, as with the stock image. Debian USB boots to an HDMI terminal. Manually loading the Maxio driver enabled Ethernet DHCP at 100 Mbps/full duplex.

The first automatic-Ethernet image skipped our module because upstream lists `maxio` as built in. Revision 2 uses the distinct module name `km6_maxio`, orders networkd after module loading, and saves an automatic boot report. On 2026-09-09 the user reported an Ethernet IP address after booting revision 2. Startup logs, SSH and Gigabit operation still await verification. CoreELEC boot remains unresolved. No Linux installation to internal storage has been tested.

## Why modify the firmware?

The stock reset/recovery FAT loader invokes `autoscr`, but its U-Boot command table provides `source` and lacks `autoscr`. The firmware patch replaces that invocation and updates the required integrity fields. Only 81 actual bytes change; stock board configuration, partition layout and Android components are retained. Reference firmware supports the alias but fails flashing compatibility checks on this KM6.

## From stock to USB boot

1. Use the exact confirmed stock image identified in `manifests/releases.json`. The similarly named ATV image is not the baseline.
2. Use Amlogic USB Burning Tool 3.1.6 to flash the modified image from the firmware release. The tested download connection uses the black USB 2.0 port. See the original investigation for hardware context; detailed flasher UI instructions are still to be consolidated.
3. On the tested device, both stock and modified firmware required recovery/factory reset after flashing before Android setup worked. Boot without external media while holding reset to reach recovery. Factory reset erases Android user data.
4. Prepare the customized Devmfc Debian USB image, insert it with power disconnected, connect Ethernet/HDMI, hold reset and apply power. The tested Debian image reaches a terminal. The automatic Ethernet configuration is still under investigation.

## Folder organization

The enclosing workspace has three directories:

- `archive/`: preserved original investigation, input images, dependencies, logs and experimental outputs; ignored by Git.
- `releases/`: the three requested firmware/flasher binaries plus checksums, for manual release upload; ignored by Git.
- `source/`: this maintained source tree and documentation, tracked by Git.

The root `.gitignore` allows only itself and `source/`. Initialize Git in the enclosing KM6 directory. On GitHub, open `source/` to read this README.

## Build source

`firmware/` contains the firmware patcher. `usb/` contains boot sources, original upstream boot files, rootfs configuration and image customization scripts. `drivers/maxio/` contains driver source and its original community version. `diagnostics/` retains the optional manual test; the historical installer is not required or recommended for normal startup.

The three Python build scripts default to the preserved sibling `archive/` working directory. Override `KM6_WORKDIR` to use another workspace with the same input layout. They write generated files into that workspace, not into this source tree. This organization preserves the existing recipes; it does not yet provide a standalone fresh-checkout build. See `docs/BUILD-STATUS.md`.

Upstream: https://github.com/devmfc/debian-on-amlogic . Our base is `Devmfc_Debian-Trixie_6.18.49-meson64_Minimal-26.09.02.img.xz`. We preserve our customization source; some upstream sources/build scripts are unavailable, so this is not a complete from-source OS build.

See `docs/DEBIAN-CHANGES.md`, `THIRD_PARTY.md` and `docs/REPOSITORY-PLAN.md` for details.
