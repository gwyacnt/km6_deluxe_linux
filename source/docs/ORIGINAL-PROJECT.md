# Mecool KM6 Deluxe Rev2 firmware investigation

Goal:
Create a modified Amlogic firmware image for my Mecool KM6 Deluxe that preserves compatibility with my exact hardware but enables external USB/microSD Linux/CoreELEC boot.

Hardware:
- Mecool KM6 Deluxe
- Amlogic S905X4
- 4 GB RAM
- 64 GB eMMC
- Gigabit Ethernet
- newer hardware revision
- "HDMI" is printed on the device chassis

Known behavior:
- Stock Android firmware:
  KM6-QTT2.200903.001-V4.20201026.img
  successfully flashes using Amlogic USB Burning Tool 3.1.6.

- Device enters Amlogic DNL mode successfully over black USB 2.0 port.
- USB ID in DNL mode:
  1b8e:c004 Amlogic Inc DNL

- Debian-on-amlogic USB does NOT boot.
- CoreELEC USB does NOT boot.
- Holding AV reset at boot always enters Android Recovery.

CoreELEC USB preparation:
- CoreELEC 21.3 Omega Amlogic-ne Generic
- device tree:
  sc2_s905x4_4g_1gbit.dtb
- copied to boot partition as dtb.img

Third-party images tested:
1. sbx_mecool_km6_atv_11_45.img
   -> Amlogic USB Burning Tool fails at 5%
   -> [flow]oemcmd[disk_initial 0]=[Failed at check dts]

2. X96_X4_Pro1_20220305-1204.img
   -> same failure at 5%
   -> Failed at check dts

3. SC-Tanix_X4-S905X4_DEBUG-NORMAL-v1.0_20220615-BETA
   -> same failure at 5%
   -> Failed at check dts

- Holding reset throughout flashing made no difference.
- External DC power made no difference.
- Stock KM6 image burns successfully to 100%.

Important:
Do NOT modify stock-working.img.
Do NOT access /dev/sdX.
Do NOT flash hardware.
Do NOT interact with USB devices.
Do NOT erase disks.
All generated firmware must go in ./output.

Task:
1. Research the structure of these Amlogic S905X4 burn images.
2. Find open-source tools capable of unpacking/repacking them.
3. Extract and compare:
   - partition tables
   - DTBs / DTS
   - U-Boot / bootloader
   - boot partition
   - environment/configuration
   - aml_sdc_burn / aml_autoscript / recovery-related components
4. Determine why stock-working.img passes "check dts" while the reference images fail.
5. Determine which component(s) in the X96/Tanix firmware enable external multiboot/CoreELEC.
6. Preserve the KM6 stock DTB, partition layout and board-specific hardware configuration wherever possible.
7. Create the smallest possible modification to the stock firmware that enables external USB/microSD boot.
8. Prefer modifying only bootloader/environment/multiboot-related components rather than transplanting an entire foreign firmware.
9. Produce:
   - ./output/modified-km6.img
   - ./output/REPORT.md
   - ./output/BUILD.md with exact reproducible commands
   - checksums for original and generated files

Safety:
- Never write directly to a block device.
- Never run dd with an of=/dev/... destination.
- Never call fastboot, adb flash, Amlogic flashing utilities, or USB-burning tools.
- Work only on regular files under this project directory.