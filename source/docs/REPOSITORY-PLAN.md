# KM6 Linux repository plan

Proposed repository name: km6-deluxe-linux. This is a migration plan, not a published repository or a completed portable build.

## Release assets

Firmware release: confirmed Stock/KM6-QTT2.200903.001-V4.20201026.img, V3_setup_V3.1.6.exe, output/modified-km6.img, plus SHA256SUMS and release notes. Keep the original filenames and document the exact supported hardware: tested KM6 Deluxe Rev2, HDMI-marked chassis, S905X4, 4 GB RAM, 64 GB eMMC. Do not include the similarly named alternate root-level firmware.

Each requested binary is below GitHub's 2 GiB per-release-asset limit: https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases . Keep binaries out of Git history. Preserve third-party attribution and license information separately from project-authored code.

A separate Debian USB release can carry a compressed generated image once automatic Ethernet is validated. The current autoload candidate is experimental: a boot step failed in the user's latest test. Do not label it working or stable.

## Proposed source tree

```text
README.md
CHANGELOG.md
THIRD_PARTY.md
.gitignore
firmware/              # stock-image patcher and integrity verification
usb/boot/              # readable script sources and configuration
usb/rootfs/            # files to install, including automatic driver configuration
drivers/maxio/         # original attributed source, KM6/kernel changes, Makefile
scripts/               # fetch verified inputs, build module, assemble/verify images
manifests/             # pinned URLs, versions, sizes and SHA256 hashes
docs/                  # flashing, boot design, Debian changes, hardware/test status
```

## Source inventory to migrate

- output/tools/build_modified.py: minimal firmware patch and checksum repair; retain relevant inspection/validation helpers.
- output/debian-usb/prepare.py and boot-prepared/: boot customization and readable legacy-script sources; preserve relevant original scripts for reviewable diffs.
- output/debian-ethernet/maxio/module/maxio.c, Makefile and original source: Maxio driver with attribution to the community TOX3 attachment, plus a documented patch for kernel 6.18 and matching the observed PHY.
- output/debian-usb/autoload/integrate.py: rootfs integration, module indexes and modules-load configuration.
- Selected diagnostic scripts and sanitized test evidence. Include an optional diagnostic helper in future images; normal startup must require no manual installer.

Exclude firmware/OS images, extracted root filesystems, downloaded toolchains and headers, object files, temporary mounts, third-party reference firmware, raw personal logs/photos and device identifiers from Git. Download build dependencies from pinned sources instead. Preserve the existing investigation folder locally.

## README narrative

1. Identify tested hardware and current feature status.
2. Explain the stock defect: its reset/recovery FAT loader calls autoscr, but this bootloader registers source and lacks autoscr. Reference images support the alias but fail this KM6's flashing compatibility checks.
3. Explain the minimal replacement with source and necessary integrity updates: 81 actual bytes differ in the firmware, retaining stock board configuration and Android components.
4. Give the stock-to-modified flashing process, recovery/factory-reset behavior observed with both images, USB preparation and held-reset boot procedure. State that a factory reset erases Android user data.
5. Explain that the firmware fix enables execution of a compatible USB boot script; it does not guarantee every Linux image works. Debian boots; CoreELEC remains unresolved.
6. Link release downloads, verification hashes, reproducible customization instructions, upstream and driver provenance.

## Debian changes and source scope

Upstream: https://github.com/devmfc/debian-on-amlogic
Base asset: https://github.com/devmfc/debian-on-amlogic/releases/download/v6.18.49/Devmfc_Debian-Trixie_6.18.49-meson64_Minimal-26.09.02.img.xz

Preserve all source for our customization. This is an upstream-image-based build, not a complete from-source Debian distribution build: upstream explicitly states some sources/build scripts are unavailable. A full independent source build would additionally require the exact patched kernel source/build configuration and OS/package build inputs.

Document these changes individually:
- Select s905x4_generic_gigabit with the supplied generic Gigabit DTB.
- Replace USB entry scripts with USB-only source-compatible scripts loaded at 0x08000000; no saved environment or internal eMMC installation.
- Adjust the upstream bootscript's autoscr invocation to source and retain documented diagnostic markers.
- Add the Maxio MAE0621A module for kernel 6.18.49-meson64, regenerate module indexes and configure automatic loading.
- Record that the experimental DTB timing change failed and was reverted; it is not part of the current image.

## Verified status and remaining work

Confirmed: firmware flashes; Android works after factory reset; recovery without USB works; Debian USB reaches an HDMI terminal; manually loading the Maxio module produces DHCP at 100 Mbps/full duplex.

Unresolved: latest image had a failed boot step, possibly module loading; identify the failed unit and logs before assigning a cause. The manual test script was omitted from the new image because its FAT partition came from the earlier baseline. SSH, automatic Ethernet, Gigabit operation, media functionality and internal Linux installation are not validated.

Before calling the source build reproducible: remove workspace-specific paths, pin all downloaded inputs, replace the ad-hoc kernel host-tool preparation with a clean build recipe, and verify image construction from a fresh checkout. Distinguish artifact-content reproducibility from byte-identical filesystem images, which may require timestamp/UUID normalization.

Before publishing a working Debian release: capture the failed unit/logs, fix automatic loading, then confirm cold-boot DHCP and SSH without a manual command. Record results in one current status table rather than accumulating contradictory README notes.

## Known SHA256 values

```text
e9c5b585374b0d2cd32c471eb171ed7fce46d5f2f689248d79ba281bc8cc1a44  KM6-QTT2.200903.001-V4.20201026.img
e32dcbf6a485f0985a1119831289954b65b88496c684a48a8e69deab1c389f8b  V3_setup_V3.1.6.exe
876c03ae71454c9981b8c75b0dc581f275ce6f99e09c4e1303d78308385a65a7  modified-km6.img
399e3e4ac2cf5ff7416a1ef6940beb364d7b408a69626e25a59fe9c5d2f8219d  Devmfc_Debian-Trixie_6.18.49-meson64_Minimal-26.09.02.img.xz
```
