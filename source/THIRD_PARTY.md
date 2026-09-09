# Third-party provenance

- Debian image and boot scripts/configuration: https://github.com/devmfc/debian-on-amlogic , release v6.18.49. Preserve upstream licensing. Some upstream OS/kernel build sources are not published.
- Maxio driver: community TOX3 attachment discussed at https://github.com/devmfc/debian-on-amlogic/discussions/25 ; attachment https://github.com/user-attachments/files/22662989/tox3.zip . Original source retained in drivers/maxio/upstream/maxio.c. Driver carries SPDX-License-Identifier: GPL-2.0; preserve that license and attribution in derivatives.
- Stock KM6 firmware and USB Burning Tool are third-party binaries. This repository does not assert ownership of them or apply a project source license to them. Modified firmware is derived from the identified stock binary; proprietary firmware source is not supplied.

No blanket license has been assigned to all contents. Keep component license notices intact.

- SC2 audio adaptations derive from Linux v6.18 `sound/soc/meson/{axg-card.c,g12a-tohdmitx.c,axg-tdm.h,meson-card.h,meson-codec-glue.h}` and Amlogic device trees: https://github.com/torvalds/linux/tree/v6.18/sound/soc/meson . Original SPDX and BayLibre/Jerome Brunet attribution are retained. SC2 register behavior was checked against https://github.com/CoreELEC/common_drivers/tree/5.15.196_20260225/sound/soc/amlogic/auge . See drivers/sc2-audio/README.md for details.
