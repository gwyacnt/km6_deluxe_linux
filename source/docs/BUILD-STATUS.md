# Current local build recipe

Run from the KM6 workspace, using preserved dependencies under `archive/`:

```sh
python3 source/drivers/maxio/build.py
python3 source/usb/integrate.py
```

The driver build copies maintained source into the ignored `archive/output/debian-ethernet/maxio/module-v2/` build directory and uses the matching prepared kernel headers and cross-toolchain. Integration extracts the original complete kernel module tree from `archive/output/debian-usb/rootfs.ext4`, adds `km6_maxio.ko`, runs depmod and creates `archive/output/debian-usb/autoload-v2/debian-km6-network-v2.img`. It preserves earlier images. `KM6_WORKDIR` overrides the archive location.

Integration requires the verified boot-compatible baseline `archive/output/debian-usb/debian.img`, original extracted root filesystem and local mcopy. It adds the files in `usb/rootfs/`, enables the automatic report service, copies a report helper into FAT, verifies all installed file contents and checks filesystem consistency. It operates on regular files only and does not write a USB device. The retained firmware builder and USB baseline preparation script remain available separately.

The source now drives module building and image integration, but an independent fresh-checkout build still needs dependency downloads, exact header host-tool preparation and baseline extraction automated. The cross-compiler differs from the upstream kernel compiler (GCC 14.2 versus 13.3); matching kernel headers and vermagic were verified.

Historical reports in archive and the original project plan may contain superseded status statements and old absolute paths. See DEBIAN-CHANGES.md and the maintained README for current status.
