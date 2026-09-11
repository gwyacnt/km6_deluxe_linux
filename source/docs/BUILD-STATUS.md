# Build and restore status

For the current hardware state and next work, read [HANDOFF.md](HANDOFF.md).
For a fresh-checkout binary restore, follow the [root README](../../README.md).
The recipe below is the historical local driver/image build and needs ignored
working dependencies; it is not the release restoration procedure.

# Current local build recipe

Run from the KM6 workspace, using preserved dependencies under `archive/`:

```sh
python3 source/drivers/maxio/build.py
python3 source/usb/integrate.py
```

The driver build copies maintained source into the ignored `archive/output/debian-ethernet/maxio/module-v2/` build directory and uses the matching prepared kernel headers and cross-toolchain. Integration extracts the original complete kernel module tree from `archive/output/debian-usb/rootfs.ext4`, builds the SC2 audio modules and device tree from maintained source, adds `km6_maxio.ko`, `km6_sc2_tohdmitx.ko` and `km6_sc2_card.ko`, runs depmod and creates `archive/output/debian-usb/autoload-v3/debian-km6-network-audio-v3.img`. It preserves earlier images. `KM6_WORKDIR` overrides the archive location.

Integration requires the verified boot-compatible baseline `archive/output/debian-usb/debian.img`, original extracted root filesystem and local mcopy. It also requires the original generic Gigabit DTB at `archive/output/audio-investigation/baseline.dtb` (hash checked by the audio builder). It adds the files in `usb/rootfs/` and `drivers/sc2-audio/rootfs/`, enables the automatic report and audio-routing services, selects the audio DTB in FAT boot.config while retaining a rollback copy, copies a report helper into FAT, verifies all installed file contents and checks filesystem consistency. It operates on regular files only and does not write a USB device. The retained firmware builder and USB baseline preparation script remain available separately.

The source now drives module building and image integration, but an independent fresh-checkout build still needs dependency downloads, exact header host-tool preparation and baseline extraction automated. The cross-compiler differs from the upstream kernel compiler (GCC 14.2 versus 13.3); matching kernel headers and vermagic were verified.

Historical reports in archive and the original project plan may contain superseded status statements and old absolute paths. See DEBIAN-CHANGES.md and the maintained README for current status.

Ethernet automatic startup and HDMI stereo listening were verified on the physical KM6 with these module/DTB versions. The newly assembled revision 3 image passes offline checks but has not itself been flashed and cold-booted. No diagnostic overlay/module or test tone is installed in normal images.
