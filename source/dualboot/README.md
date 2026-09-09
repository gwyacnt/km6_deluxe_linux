# Internal dual boot — work in progress

Target: a timed HDMI menu on every normal power-on, defaulting to Android,
with Debian as the second choice. Both systems will use separate areas of
internal eMMC. The final system must not require a USB stick or the reset button.

**This is not an installer yet. No internal-storage installation has been tested.**

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
at init-bottom when `km6_menu=enabled` is on the kernel command line. It uses
a 15-second timeout during hardware testing. The kbd `openvt` executable is
copied under a unique path so the BusyBox hook cannot replace it.

`bootcmd-usb-test.txt` is the proposed U-Boot command for the first real handoff
test. It arms an Android fallback before attempting the existing external boot
commands. A subsequent boot consumes that flag and runs Android's `storeboot`.
The initramfs clears the flag only when Debian is selected. If reset-held USB
recovery bypasses this boot command, the initramfs skips the menu and continues
into Debian. These actual boot transitions still require hardware testing.

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
before Android. The handoff, recovery behavior and cold boot are not tested.

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
