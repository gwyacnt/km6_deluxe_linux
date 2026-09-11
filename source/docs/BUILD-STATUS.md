# Build maintained components from a fresh clone

The build workflow does **not** use `archive/`, a device backup, the original
PC, or SSH access to the KM6. Required binary inputs are pinned by SHA-256 in
`source/manifests/build-inputs.json` and attached to the same `v0.2.0-rc4`
release as the restore installer.

## Host and commands

Tested host: Debian 13 on x86_64, Python 3.13. Use Python 3.12 or newer for the
safe tar extraction filter. Allow 10 GB of working space, plus download cache.
The SDK supplies the cross-compiler, exact kernel headers, cross-libc, dtc,
mtools and AVB tools. Standard host packages are still prerequisites:

```sh
sudo apt-get install python3 build-essential e2fsprogs kmod openssl \
  libisl23 libmpc3 libmpfr6 libgmp10 libzstd1 zlib1g libyaml-0-2 libfdt1

git clone --branch v0.2.0-rc4 https://github.com/gwyacnt/km6_deluxe_linux.git
cd km6_deluxe_linux
python3 source/bootstrap_build.py
python3 source/build.py
```

The build commands run unprivileged and operate on regular files. They do not
flash a USB stick, connect to the KM6, or modify its eMMC. Only package
installation above needs sudo. Other host distributions/architectures have not
been validated with this prepared x86_64 SDK.

Bootstrap downloads three pinned inputs: the stock KM6 ROM, the original
Devmfc image, and `km6-build-sdk.tar.xz`. It extracts only the public Android
components needed by the layout builder, reconstructs the Linux baseline and
extracts its root filesystem. All generated files go under ignored `build/`.
An existing workspace is refused to avoid overwriting previous work. Choose
another directory with `--workspace /path/to/new-build` on **both** commands.
`--directory /path/to/cache` optionally selects a verified download cache.

The scripts in `source/drivers/`, `source/firmware/`, `source/dualboot/` and
`source/usb/` also default to `build/`; `KM6_WORKDIR` can override that location.
No specific developer username, absolute workspace path or private recovery
backup is required.

## Outputs and scope

| Target (`source/build.py --target NAME`) | Output under `build/output/` |
| --- | --- |
| `drivers` | Maxio Ethernet module, both SC2 HDMI audio modules and audio DTB |
| `tools` | Static AArch64 boot chooser and read-only MPT mapper |
| `layout` | Signed Android partition metadata, MPT/DTB slots and public installer layout manifest |
| `firmware` | `modified-km6.img`, verified against the stock container |
| `legacy-usb` | Original minimal Debian image with our Ethernet/audio integration; filesystem checked |

With no `--target`, all targets run. Targets can be repeated. The legacy USB
integration target rebuilds the earlier minimal driver-test image; **use the
release installer for the current Xfce desktop and USB-selection setup**.
The complete desktop is distributed as a sanitized binary snapshot, not
recreated by the legacy integration script.

To maintain that desktop snapshot, restore the release, customize Debian and
run the tagged `source/usb/export_installer.py` on the internal KM6 installation
with the release's extracted installer bundle. See [REPRODUCE.md](REPRODUCE.md).
The exporter now also handles installations that already contain a previous
public installer bundle and first-boot service link.

The original upstream Linux image, Android ROM and compiler/headers are binary
build inputs. We maintain the KM6 customization source, not unpublished
Android/kernel sources or a complete compiler/distribution build system.
Preserving these inputs in the release makes our component builds independent
of the original workspace without claiming a fully from-source OS build.

## Validation

A separate checkout was populated only with source and the pinned release
inputs. Bootstrap and **all five build targets passed** there on September 11,
2026. The rebuilt modified Android image matched the released SHA-256 exactly.
Audio DTB and both HDMI audio modules also matched the current installation.
The Maxio module passed name/vermagic checks but its binary hash differs from
the original build; byte-for-byte reproducibility of every compiler output is
not claimed. No rebuilt module was installed on the working KM6 during this
check. The legacy integrated image passed filesystem and content checks.

See `build-validation.json` in the release for the recorded results. These
are build/offline checks, not a fresh flash or end-to-end restore test.
The warm-restart Ethernet issue remains open as documented in HANDOFF.md.

`source/dualboot/stock-mpt.bin` contains only 1304 bytes of stock partition
names, offsets, sizes and checksum. It is not a reserved-partition dump or a
personal backup. `stock-layout.json` contains public layout/hash constraints.
Actual device-specific DTB slot hashes and Android footer data are captured
at installation time by `install_from_release.py`, not supplied by a developer.
