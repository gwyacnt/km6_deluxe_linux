# Continue the KM6 project with Codex

Last verified: September 11, 2026. Start here; the chat is historical evidence.

## Start on another machine

With Git and Codex already installed and authenticated:

```sh
git clone https://github.com/gwyacnt/km6_deluxe_linux.git
cd km6_deluxe_linux
codex
```

Paste this into Codex:

> Read AGENTS.md, README.md and source/docs/HANDOFF.md. Use
> source/docs/conversation/README.md and the dated transcripts for historical
> context as needed. Summarize the verified setup and unresolved work, inspect
> the current Git state, and wait for my next task before modifying a device.
> Do not assume the original developer's SSH access or local archive exists.

In the Codex desktop app or IDE extension, open this cloned repository and use
the same prompt in a new chat. No original account, local database or private
session file is needed to continue from these checked-in documents.

This starts a **new chat with the project's context**. Cloning does not import
the old chat into Codex's session picker. `codex resume` is for saved local
chats; use it later to resume your own new session. See the official
[CLI documentation](https://learn.chatgpt.com/docs/codex/cli) and
[AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
The command examples follow those docs; the CLI executable was not available
in the exporting agent's shell, so cross-machine session continuation has not
been tested here.

## Verified device state

- Mecool KM6 Deluxe Rev2, S905X4/SC2, 4 GB RAM, 64 GB A1511X eMMC.
- Android TV and Debian 13 / Devmfc kernel `6.18.49-meson64` use separate
  internal storage areas. Debian root is `/dev/mapper/km6-linuxroot`;
  boot is `/dev/mapper/km6-linuxboot`. This is persistent installed Debian.
- Any enumerated external USB peripheral (receiver included) automatically
  selects internal Debian. Host root hubs do not count. No files on attached
  USB media are executed by the selector.
- With no USB devices, a 15-second menu defaults to Android. The owner
  confirmed this final no-USB test and the receiver-connected cold boot.
- SSH after the receiver-connected cold boot confirmed `usb:1-1` in
  `/run/km6-menu-trigger`, choice `10`, the internal mapper root and active
  LightDM/Tailscale. Debian selection clears the Android fallback flag.
- HDMI Xfce desktop, Ethernet and stereo HDMI audio work. Firefox played
  YouTube with audio. Tailscale exit-node configuration is on the personal
  installation; a public restore must enroll its own identity.
- Personal user is `samer`, hostname `km6-deluxe`. Addresses can change;
  obtain current connection details and authorization from the device owner.
  Default passwords from early experiments are obsolete.

## Open issues and next work

1. **Warm-restart Ethernet reliability.** After installing the USB selector,
   one software reboot reached Debian but Ethernet repeatedly gained/lost
   carrier and its DHCP lease. Removing power restored stable LAN/SSH with
   the same boot image. The failed boot reported PHY driver
   `MAE0621A-Q2C Gigabit Ethernet`; the successful cold boot reported
   `MAE0621A Gigabit Ethernet`. This is a diagnostic clue, not a proven cause.
   Compare PHY IDs, bound driver/module, module load order and reset behavior
   across warm/cold boots and the saved previous initramfs. The selector
   changes boot timing; its involvement has not been ruled out. Do not call
   power cycling a permanent fix. Private captured logs on the original PC:
   `archive/output/usb-selector/cold-boot-previous-network.txt`.
2. **Restore validation.** The clean release installer passed offline checks,
   but has not completed a fresh-stick boot and end-to-end install test.
   Test on a recoverable device before calling it a stable restoration path.
3. **Validate the new release on hardware.** `v0.2.0-rc3` packages the installed
   USB selector in both the USB boot image and internal-install bundle. The
   old rc2 tag remains unchanged. Complete a fresh-media installation test
   before calling the new restore package stable.
4. **Performance.** Panfrost/WebRender already accelerates rendering; browser
   video decoding remains software-only. 720p/no Xfce compositor improves
   measured animation performance, but Android-like YouTube performance is
   not established. See `../performance/README.md`. Gigabit Ethernet and the
   infrared remote are unverified; current tested link is 100 Mbps/full duplex.

## Boot and recovery details

The vendor bootloader uses Amlogic MPT, not a standard GPT layout. Android data
is 32 GiB. Linux boot starts at 35562 MiB (256 MiB); Linux root starts at
35826 MiB (23822 MiB). Device eMMC was `/dev/mmcblk1`; verify before using it.
U-Boot loads the internal FAT partition as `mmc 1:12` (hexadecimal index).

`source/dualboot/bootcmd-internal.txt` arms an Android fallback before entering
the Linux early-boot menu. Android selection reboots into the stock boot path;
Debian selection clears the fallback and continues. A Linux startup precedes
the menu, so Android's path includes an extra reboot rather than a native GRUB
menu. Reset-held USB rescue remains available.

Live selector files:

```text
/usr/local/lib/km6-dualboot/usb-present
/etc/initramfs-tools/hooks/km6-menu
/etc/initramfs-tools/scripts/local-premount/km6-menu
/boot/uInitrd-km6-menu.img
```

The pre-selector hook, menu and wrapped initramfs are saved on the original
device under `/root/km6-usb-selector-backup/` as `hook`, `menu` and
`uInitrd-km6-menu.img`. Preserve these before any experiments. The environment
tools must use `-c /etc/km6-fw_env.config`; `/etc/fw_env.config` is unsuitable
for this installation. The Ethernet/audio fixes use `km6_maxio.ko`,
`km6_sc2_tohdmitx.ko`, `km6_sc2_card.ko` and `km6-sc2-audio-test.dtb`.

## Repository and releases

| Location | Purpose |
| --- | --- |
| Root README / AGENTS.md | Restore entry point and Codex guidance |
| `source/firmware/` | Stock firmware USB-boot patch source |
| `source/dualboot/` | Menu, USB detector, partition/install/activation tools |
| `source/drivers/` | Ethernet and HDMI audio customizations |
| `source/usb/` | USB integration and sanitized installer export |
| `source/performance/` | Desktop/browser defaults and measurements |
| `source/docs/conversation/` | Redacted user/assistant transcript by day |
| `archive/` (ignored) | Local investigation, dependencies, private backups |
| `releases/` (ignored) | Locally staged downloadable release assets |

`v0.2.0-rc2` at `35e2fda` is the immutable self-contained **pre-selector**
restore release. Its stock ROM, modified ROM, flasher and Debian installer are
all in that same GitHub release. Follow the root README for restoration.
`9a0bc1a` adds USB selection and refreshes future exports from the installed
initramfs. `v0.2.0-rc3` supplies a new sanitized export with this installed boot policy,
plus all required firmware/flasher assets in the same release. See its
`validation.json` and pinned `checkpoint-assets.json`.

A complete rebuild of an existing dual-boot device must first restore the
original Android partition layout by reflashing. `km6-install-internal` is a
fresh installer, not an update command. Do not run it merely to update a boot
script. Personal account state is excluded from public images.

The repository maintains customization source and binary restore snapshots;
it is not a full from-source distribution build. Historical build recipes
still need local dependencies absent from a fresh clone. The release-based
restore path does not need the original developer's private archive.

## Local checks

From the repository root, without a KM6 connected:

```sh
python3 source/dualboot/test_usb_present.py
python3 source/test_reproduce.py
cc -O2 -Wall -Wextra -Werror source/dualboot/menu.c -o /tmp/km6-menu
python3 source/dualboot/test_menu.py /tmp/km6-menu
git diff --check
```

These check selector cases, image-writer safeguards and terminal menu behavior;
they do not substitute for firmware/installer tests on hardware. Read scripts
before running other commands: some deliberately modify partitions or flash
images when `--apply` / `--write` is supplied.
