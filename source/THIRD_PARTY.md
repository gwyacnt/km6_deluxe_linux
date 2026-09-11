# Third-party provenance

- Debian image and boot scripts/configuration: https://github.com/devmfc/debian-on-amlogic , release v6.18.49. Preserve upstream licensing. Some upstream OS/kernel build sources are not published.
- Maxio driver: community TOX3 attachment discussed at https://github.com/devmfc/debian-on-amlogic/discussions/25 ; attachment https://github.com/user-attachments/files/22662989/tox3.zip . Original source retained in drivers/maxio/upstream/maxio.c. Driver carries SPDX-License-Identifier: GPL-2.0; preserve that license and attribution in derivatives.
- Stock KM6 firmware and USB Burning Tool are third-party binaries. This repository does not assert ownership of them or apply a project source license to them. Modified firmware is derived from the identified stock binary; proprietary firmware source is not supplied.

No blanket license has been assigned to all contents. Keep component license notices intact.

- SC2 audio adaptations derive from Linux v6.18 `sound/soc/meson/{axg-card.c,g12a-tohdmitx.c,axg-tdm.h,meson-card.h,meson-codec-glue.h}` and Amlogic device trees: https://github.com/torvalds/linux/tree/v6.18/sound/soc/meson . Original SPDX and BayLibre/Jerome Brunet attribution are retained. SC2 register behavior was checked against https://github.com/CoreELEC/common_drivers/tree/5.15.196_20260225/sound/soc/amlogic/auge . See drivers/sc2-audio/README.md for details.

- Desktop release add-ons: enhanced-h264ify 2.2.1 (MIT), https://github.com/alextrv/enhanced-h264ify ; uBlock Origin 1.74.0 (GPL-3.0), https://github.com/gorhill/uBlock . The original signed XPI packages retain their license files. Versions and hashes are recorded under performance/.

- Build SDK (`km6-build-sdk.tar.xz`): prepared Devmfc 6.18.49 kernel headers
  including generated configuration/Module.symvers and host helpers; Debian
  GCC 14.2.0-19cross1, binutils 2.44-3, ARM64 glibc 2.41-11cross1,
  linux-libc-dev 6.12.38-1cross1, dtc 1.7.2 and mtools 4.0.48. Existing
  source/license notices and package documentation inside the selected tool
  trees are preserved. These are build dependencies, not project-owned code.
- The SDK also pins AOSP `avbtool.py` (MIT notice retained) and AOSP's openly
  published RSA-2048 test fixture key. See dualboot/README.md for provenance
  and hashes. This test key is not a personal/device credential.
- The SDK's baseline Gigabit device tree is from the original Devmfc image;
  its exact SHA-256 is enforced by the audio builder. No private reserved
  partition, firmware environment, SSH keys or account state is included.
