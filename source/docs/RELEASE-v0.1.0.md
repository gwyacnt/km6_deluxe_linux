# v0.1.0 — KM6 Deluxe Rev2 USB boot firmware

Initial firmware release for the tested HDMI-marked Mecool KM6 Deluxe Rev2, S905X4, 4 GB RAM and 64 GB eMMC.

## Downloads

- `KM6-QTT2.200903.001-V4.20201026.img`: exact confirmed stock firmware, retained as the baseline/recovery image.
- `V3_setup_V3.1.6.exe`: Amlogic USB Burning Tool used for successful flashing.
- `modified-km6.img`: stock-derived firmware enabling execution of compatible external USB boot scripts.
- `SHA256SUMS`: SHA256 checksums for all three binaries.

The modification replaces a stock `autoscr` invocation with the supported `source` command and updates integrity fields. Only 81 actual bytes differ from stock; board configuration, partition layout and Android components are retained.

## Tested behavior

The modified image flashes successfully. Android works after recovery/factory reset, as with stock. Holding reset without USB reaches recovery. The customized Devmfc Debian USB image reaches an HDMI terminal.

Factory reset erases Android user data. Compatibility is established only for the tested hardware revision. Enabling USB script execution does not guarantee that every Linux image will boot.

## Current limitations

CoreELEC boot remains unresolved. The Debian Maxio driver obtained DHCP at 100 Mbps/full duplex when loaded manually, but the automatic-Ethernet candidate produced a reported failed boot step. No Debian image is included in this release. SSH, automatic Ethernet, Gigabit operation and Linux installation to internal storage are not validated.

Source and current documentation: [source/README.md](https://github.com/gwyacnt/km6_deluxe_linux/blob/v0.1.0/source/README.md). Build recipes currently depend on archived inputs; an independent fresh-checkout OS build is not yet available. Third-party binary ownership and component licenses remain with their respective authors.
