# Experimental KM6 SC2 HDMI audio

Stereo HDMI playback is confirmed on the tested KM6 Deluxe Rev2: 48 kHz, S16_LE, two channels. This remains a limited SC2 adaptation; other formats and long-term stability are untested.

The stock board uses the SM1 audio clock register layout at 0xfe330000, TM2-revB FRDDR/TDM components, and TDM C for HDMI. Source inspection identified a concrete HDMI routing difference: SC2 has separate clock/data enables at bits 28/29, while the G12A mainline driver uses bit 31. The experimental module retains the mainline ASoC routing interfaces, changes to a unique SC2-only compatible/name, uses bit 29 for the DAPM data gate, and initializes the clock gate and TDM C MCLK selection from vendor i2s_to_hdmitx_ctrl. Stereo TDM C is the only intended test route.

`playback-test.dtsi` adds the clock provider, arbitration reset, FRDDR A, TDMOUT C, logical TDM interface, HDMI routing component and sound card. Reuse of the related SM1 playback components is a hypothesis under test, not a declaration of full SC2 compatibility. Stereo routing, PCM transfer and audible playback passed the tests recorded below.

`clock-test.dts` and `overlay-loader.c` are a first-stage, live-only experiment. The clock controller successfully bound to axg-audio-clkc and registered its SM1 reset provider on the physical KM6. The loader deliberately has no unload entry because re-registering the clock driver's static data in the same boot is unsafe. Reboot removes this temporary overlay. Compile without `-@`: the deployed base tree lacks a symbols node. Numeric baseline references must be verified before applying.

Build the playback candidate from the repository's enclosing workspace:

```sh
python3 source/drivers/sc2-audio/build.py
```

Dependencies are provided by `source/bootstrap_build.py`: the pinned compiler/headers, dtc tools and exact original generic Gigabit DTB under `build/output/audio-investigation/baseline.dtb`. The script checks its SHA256 and clock/reset/power references. Artifacts go into `build/output/audio-investigation/playback-test/`. The module compiled against 6.18.49-meson64; all 677 properties of the original DTB were compared and retained. New audio nodes and an HDMI phandle are additions.

## Current device state

The candidate is staged on the running USB:

- `/boot/km6-sc2-audio-test.dtb`
- `/usr/lib/modules/6.18.49-meson64/extra/km6_sc2_tohdmitx.ko`
- `/usr/lib/modules/6.18.49-meson64/extra/km6_sc2_card.ko`
- `/etc/modules-load.d/km6-sc2-audio-test.conf`
- `/boot/boot.config` now selects the candidate with `dtb_img=km6-sc2-audio-test.dtb`.
- The prior config is `/boot/boot.config.before-km6-audio`; its exact copy and checksums are in the local ignored archive.

The full tree registers a playback card and reads valid HDMI ELD. Silent playback opens after the first route correction, but DMA stalls after filling its FIFO. The latest candidate below requires a fresh reset-held USB boot; audible playback passed the attended test below. Ethernet remains available.

## Rollback

Restore `/boot/boot.config.before-km6-audio` to `/boot/boot.config`, remove `/etc/modules-load.d/km6-sc2-audio-test.conf`, sync and reboot. If Linux cannot boot, restore `boot.config` from the backup using a PC's FAT partition mount. The original DTB is retained at its original path. No firmware reflash is required.

## Sources and licensing

- `sc2-tohdmitx.c` and `meson-codec-glue.h`: Linux v6.18, sound/soc/meson, GPL-2.0, original BayLibre/Jerome Brunet attribution retained.
- Audio description based on Linux v6.18 meson-sm1.dtsi and meson-g12a-u200.dts (Amlogic/BayLibre; GPL-2.0+ OR MIT).
- Vendor register evidence: CoreELEC/common_drivers branch `5.15.196_20260225`, sound/soc/amlogic/auge/{regs.h,tdm_hw.c,tdm_match_table.h,ddr_mngr.c,clks/clk-sm1.c}.
- Board wiring/interrupts from the confirmed stock KM6 4 GB device tree.

Raw downloaded references and live logs are retained under the ignored archive. This experiment does not claim to rebuild the exact Devmfc kernel from source.

## First playback boot and route correction

The first full boot registered KM6-SC2-HDMI-TEST with a playback PCM and valid HDMI ELD from the display. All intended audio components bound. Silent PCM open then returned EINVAL with `no backend DAIs enabled`: the board description omitted the `TDM_C Playback` <- `TDMOUT_C OUT` route. That route is now included in playback-test.dtsi and the staged DTB.

Attempting a live card unbind to reload routing triggered a kernel NULL dereference in `meson_card_clean_references` (snd_soc_meson_card_utils). Do not unbind/rebind this card with the current kernel. The overlay route fix was not applied because the preceding unbind failed. Subsequent testing must use a fresh boot; this fault is not evidence of successful or failed PCM hardware transfer.

The rootfs files in this directory add km6-audio-route.service to configure the card's mixer switches automatically after boot. The service is staged and enabled on USB. No manual setup and no playback are part of the service. On rollback, also disable km6-audio-route.service. Audible stereo playback was subsequently confirmed; see below.

## Second boot: stalled DMA and card recognition fix

With automatic mixer routing successful, a 48 kHz stereo S16_LE silent transfer opened but returned EIO. The read-only `audio-diag.c` module showed FRDDR_A started, filled 1024 bytes and stopped progressing without interrupts. TDMOUT_C registers and output clocks stayed off. Its DAPM graph showed the HDMI link connected in the capture direction and no powered playback path.

Two source-level causes were identified and corrected in the next staged candidate:

1. The inherited HDMI component probe overwrote the whole control register after platform probe, erasing the SC2 static clock bits. Initialization now happens in component probe.
2. The AXG card recognizes codec-to-codec links by specific DT compatible strings. Our unique SC2 compatible was missing from that list. `sc2-card.c` is a Linux v6.18 AXG card adaptation with a unique card compatible and explicit SC2 codec recognition. It preserves the codec-to-codec setup required for the output link, without allowing the unmodified G12A driver to bind to SC2 hardware.

Both modules compiled against the matching kernel headers; depmod resolved their dependencies, and staged hashes were verified over SSH. This candidate passed silent PCM transfer after a fresh boot (see below). Audible stereo sound was subsequently confirmed. `sc2-card.c`, `axg-tdm.h` and `meson-card.h` retain their upstream licensing and attribution.

Read-only diagnostic logs and candidate checksums are in `archive/output/audio-investigation/{diag,playback-test}/`. Do not unbind the running card to install changes; use a fresh boot because the kernel's card removal path has already faulted once.

## Third boot: successful silent PCM transfer

On 2026-09-09, both custom modules and km6-audio-route.service loaded automatically. SSH/Ethernet remained available and systemd reported no failed units. Two 48 kHz stereo S16_LE silent playback runs completed with exit status 0. During playback, FRDDR interrupts advanced, the PCM hardware pointer reached 47104 frames after approximately one second, and TDMOUT_C was enabled. Output bit/frame clocks reported 3071976 Hz / 48000 Hz, and TOHDMITX control was 0x301a22a8, retaining the SC2 gates and MCLK settings.

This confirms the previously stalled PCM path now transfers data. It does not yet confirm audible HDMI output, channel assignment, other sample formats/rates or long-duration stability. A quiet five-second WAV has been prepared for an attended listening test; it is not played automatically at boot.

## Confirmed listening test and default image integration

The user confirmed both tones played correctly after the five-second, 48 kHz S16_LE stereo WAV test completed with exit status 0. The left channel played 440 Hz, then the right channel 660 Hz, with short fades and a low digital amplitude.

`source/usb/integrate.py` now builds this source and includes both modules, the additive DTB, module autoload configuration and enabled mixer service in revision 3 by default. No manual script or diagnostic module is required. The exact module/DTB bytes match the tested device. The rebuilt full image still needs its own fresh-flash boot test.
