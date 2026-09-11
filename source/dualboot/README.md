# Internal dual boot

Current behavior: both systems use separate areas of internal eMMC. Any
external USB peripheral selects Debian automatically; without USB, the timed
HDMI menu defaults to Android after 15 seconds. Normal operation requires
neither a USB storage stick nor the reset button. Earlier prototype steps
below are retained as implementation history.

**Android TV and internal Debian desktop boot are confirmed. Debian was tested
with the USB stick removed. The clean release installer remains a candidate
until its separate fresh-media installation test.**

## Menu prototype

`menu.c` is a small terminal chooser intended for an early Linux initramfs.
It returns 0 for Android, 10 for Debian, or 2 on an error. It does not reboot,
change boot settings, or write storage. The default timeout is eight seconds.
Arrow keys or 1/2 select an entry and pause the timeout; Enter accepts it.
The initial input method is a USB keyboard. Remote-control input is untested.

Build and exercise the terminal input handling on a development machine:

```sh
cc -O2 -Wall -Wextra -Werror menu.c -o /tmp/km6-menu
python3 test_menu.py /tmp/km6-menu
```

For the initramfs, build a static AArch64 executable with an AArch64 Linux
toolchain and matching libc development files. Merely installing this binary
does not enable dual boot.

`preview.sh /absolute/path/to/km6-menu`, run as root on the box, temporarily
switches to virtual console 8 and restores the previous console afterward.
It allows 150 seconds for a choice and has an overall 180-second limit.
The result is saved to `/run/km6-menu-result`; neither choice boots an OS.
The ARM64 binary passes the same pseudo-terminal tests as the host build.
Console-memory inspection confirms that the corrected preview draws both
choices and its countdown. The user confirmed that the preview works on HDMI.

## Staged USB boot test

`initramfs-hook` installs the menu, console tools and U-Boot environment tools
into an initramfs built with Debian's initramfs-tools. `initramfs-menu` runs
at local-premount when `km6_menu=enabled` is on the kernel command line. It uses
a 15-second timeout during hardware testing. The kbd `openvt` executable is
copied under a unique path so the BusyBox hook cannot replace it.

`bootcmd-usb-test.txt` is the proposed U-Boot command for the first real handoff
test. It arms an Android fallback before attempting the existing external boot
commands. A subsequent boot consumes that flag and runs Android's `storeboot`.
The initramfs clears the flag only when Debian is selected. If reset-held USB
recovery bypasses this boot command, the initramfs skips the menu and continues
into Debian.

On 2026-09-09 the user confirmed that the countdown booted Android TV. A normal
power cycle followed by Debian selection brought SSH back; the recorded choice
was 10 and the Android fallback flag was cleared. This test still used USB.
The Debian desktop failed because ext4 detected invalid inode checksums and
remounted the USB root filesystem read-only. A private backup was saved and an
offline filesystem repair restored writable storage and the working desktop.
The chooser was moved from
init-bottom to local-premount so choosing Android no longer mounts Debian's
filesystem. The later internal-storage and USB-selector tests below validate this placement.

The test needs a U-Boot ramdisk wrapper around the generated initramfs, a
`rd_img` entry selecting that wrapper in the USB `boot.config`, and
`bootargs15=km6_menu=enabled panic=10`. Save the previous boot configuration
and the full CRC-valid environment before enabling it. Backups belong outside
Git. Restore the previous `bootcmd` and USB configuration to remove the test.

## Boot design under investigation

The installed U-Boot command table has no `bootmenu` command. A Linux initramfs
could provide HDMI output and keyboard input using the already working kernel.
Choosing Debian would continue into its internal root filesystem. Choosing
Android would reboot through a one-shot U-Boot environment flag into the
existing Android boot sequence. This adds an initial Linux startup and reboot
before Android. The handoff was tested with USB; internal boot and recovery
behavior remain untested.

Before launching the chooser, U-Boot would arm an Android fallback. Debian
selection would clear that flag before continuing; Android selection would
leave it armed and reboot. Environment writes require a verified configuration:
the tested device has a CRC-valid 64 KiB environment at byte offset 0x39400000
in the eMMC user area. The base image's environment configuration is incorrect
for this unit. Do not apply that offset to another model without checking it.

## Storage investigation, 2026-09-09

The tested 64 GB unit has 62,545,461,248 bytes of eMMC user storage and an
Amlogic MPT v1 table at 36 MiB. Android `data` starts at 2,786 MiB and occupies
the remainder. A proposed allocation is 32 GiB for Android data, 256 MiB for
Linux boot files, and approximately 23 GiB for Debian. Existing Android system
partition offsets must stay unchanged. The Android filesystem must be resized
or recreated to fit before assigning its former space to Linux.

The vendor bootloader compares its partition table against the partition
description in the stored Android device tree. Updating the table alone is
insufficient. Both redundant device-tree slots contain AVB metadata as well as
Amlogic slot checksums; changes need investigation before deployment.

A newer related vendor U-Boot source supports GPT priority, but that does not
prove the installed binary supports it. The device reports eMMC
`PARTITION_CONFIG=0x00`; backup bootloaders in boot0 and boot1 do not establish
that the ROM boots from those areas. Do not overwrite the user-area bootloader
with a GPT on that assumption.

`plan_storage.py` reads a regular backup file of the reserved region, validates
the MPT v1 checksum and partition bounds, and prints the proposed layout as
JSON. It cannot install that layout. `test_storage.py` exercises preservation
of the existing system partitions and rejection of malformed layouts using
the same private backup, which is intentionally not shipped in the repository.

Device-specific backups of the user-area bootloader, boot0, boot1, reserved,
environment, factory and misc regions have been saved outside Git with SHA-256
hashes. They can contain provisioning material and must remain private.

Before installation: verify the HDMI chooser, prove the Android one-shot
handoff while Debian remains recoverable on USB, validate coherent partition
and device-tree changes, and prepare an internal Debian copy containing the
tested Ethernet/audio configuration. Final acceptance requires both Android
timeout boot and selected Debian boot with the USB stick removed.

## Offline partition metadata builder

`build_layout.py` builds candidates in the ignored working directory. It does
not install them. It changes the data size and adds Linux boot/root entries in
each of the three original Android device trees, preserving every other
existing property. It also builds the matching MPT v1 table and redundant-DTB
slot payload, and regenerates Android AVB metadata with all non-DT descriptors
preserved. The stock vbmeta signature was verified and its embedded public key
matched AOSP's published RSA-2048 test key exactly. Candidate signatures and
the new DT hash were verified offline; Android boot with these new metadata
files is not yet tested.

The builder currently uses preserved stock inputs, the private table backup,
local dtc tools, and these upstream files downloaded under
`archive/output/dualboot/`:

- `avbtool.py`: [AOSP avbtool](https://android.googlesource.com/platform/external/avb/+/refs/heads/main/avbtool.py), SHA-256 `e5a664a38db623da00f080219bc0ee60a640a9dc4a872803616fae4938ac749b`.
- `aosp-public-testkey-rsa2048.pem`: [AOSP published test key](https://android.googlesource.com/platform/external/avb/+/refs/heads/main/test/data/testkey_rsa2048.pem), SHA-256 `f1d5765a2bdfb92fb08aee021107c7ac1a7a3f590dafd853771c85375ef0fbd7`.

These URLs follow upstream's main branch; the builder enforces the recorded
file hashes. The key is a publicly distributed test fixture, not a private
device or account credential.

## Linux view of internal partitions

The Debian kernel does not expose the vendor MPT entries as normal partition
devices. `mpt-map.c` reads and validates the eMMC table and emits two linear
device-mapper tables. It does not write storage. `initramfs-map`, installed as
a local-top script, creates `/dev/mapper/km6-linuxboot` and
`/dev/mapper/km6-linuxroot` only when the latter is the requested root device.
This maps dedicated physical regions; no Debian disk image is stored inside
Android's filesystem. The hook includes dmsetup and dm_mod when the mapper
binary is installed. Internal Debian boot with these mappings is confirmed.

`build_tools.py` builds static ARM64 menu and mapper executables with the
preserved GCC-14 toolchain and cross-libc files. `test_map.py` exercises the
mapper against the offline table candidate and rejects damaged headers,
checksums, partition overlaps and an incorrect Android data size.

## Internal installation status, 2026-09-09

The 64 GB test unit now has the proposed MPT layout installed. Android data
was shrunk to 32 GiB minus its 16 KiB footer reserve; the original footer was
relocated to the new partition end. Both Android device-tree slots, signed
vbmeta and the partition table were read back and verified. The user-area
bootloader and Android system partition offsets were preserved.

`make_install_manifest.py` records hashes of the original metadata and the
candidates. `install_layout.py` requires those exact inputs, checks the device,
backs up metadata, shrinks and checks Android data, installs the metadata and
formats the dedicated Linux regions. It is specific to this device and its
recorded starting state, not a general installer. Do not rerun it after the
layout is installed.

`copy_debian.py` copies the persistent USB installation while desktop, VNC and
Tailscale services are stopped. It preserves sparse files, ownership and ACLs,
installs the internal boot configuration, checks the kernel and custom driver
hashes, and checks both unmounted target filesystems. The existing user and
application configuration are included. One corrupt, implausibly large Firefox
internal data file was quarantined on the USB before copying; private backups
and the working directory are excluded from the internal installation.

`internal-load.txt` loads the boot script from the dedicated FAT partition.
The vendor partition index is zero-based and parsed as hexadecimal: Linux boot
is index 18 decimal, expressed as `mmc 1:12`. `bootcmd-internal.txt` tries that
loader, then the existing USB fallback, then Android. `activate_boot.py`
validates installed metadata and filesystems before changing the environment;
without `--apply` it only validates. Activation backs up the CRC-valid
environment and verifies that only `km6_internal` and `bootcmd` changed.

The internal root uses `/dev/mapper/km6-linuxroot`; its boot filesystem uses
`/dev/mapper/km6-linuxboot`. The user confirmed Android timeout boot after the layout change, then removed
the USB stick and confirmed Debian desktop boot. SSH verified the mapper root
and boot filesystems, no USB disk, and active LightDM and Tailscale. A later
power cycle also returned to the same internal Debian installation.

## USB selection after checkpoint v0.2.0-rc2

The early-boot selector now checks for any enumerated external USB device,
including the keyboard/mouse receiver and external hubs. Built-in USB root
hubs and interface entries do not count. It allows up to two additional
seconds for enumeration before opening the normal 15-second Android-default
menu when no external device is found.

When a device is found, it selects **internal Debian**, clears and verifies
the existing Android fallback flag, and skips the menu. It neither mounts nor
executes files from the USB device. `/run/km6-menu-trigger` records `usb:<port>`
or `menu`, and `/run/km6-menu-choice` retains the existing numeric result.
The Android fallback on errors and reset-held USB rescue path are preserved.
Devices must enumerate: a charge-only cable cannot serve as a selector.

`test_usb_present.py` checks empty buses, host hubs, interface entries and
external devices using fake sysfs directories. The pre-change release tag
v0.2.0-rc2 remains unchanged. Its downloadable installer uses the old menu
policy. New exports carry the installed initramfs into the internal installer
bundle so a subsequent installation retains the current selection policy.

## Final hardware check — September 11, 2026

After removing and reconnecting power with the receiver attached, SSH verified
`usb:1-1`, choice `10`, internal mapper root and active desktop/Tailscale.
The owner then confirmed that removing all USB devices restored the timed
Android-default menu and Android boot.

One preceding warm restart had unstable Ethernet carrier and repeated DHCP
lease loss. The cold boot restored networking; its cause remains unresolved.
See [HANDOFF.md](../docs/HANDOFF.md) for the driver-name difference and next
diagnostic steps. The published rc2 installer still predates USB selection. The rc3 release
packages the installed selector in a new sanitized installer and bundle.
