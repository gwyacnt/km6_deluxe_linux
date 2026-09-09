# KM6 driver checks — 2026-09-09

## Latest result

Ethernet starts automatically. Basic HDMI display output and Panfrost context creation passed. With the custom SC2 audio drivers and device tree, automatic routing and 48 kHz S16_LE stereo PCM transfers pass. The user confirmed both channel tones sounded clear. Revision 3 integration now includes these fixes by default. Other audio formats, hardware video decoding, remote control, Wi-Fi and Bluetooth remain unverified.

The sections below preserve the investigation history; earlier no-audio findings describe the original image.

## Baseline inspection

SSH inspection of the revision 2 USB system:

- HDMI connector is connected and offers 1920x1080 at 60 Hz, among other modes. Meson DRM and Panfrost initialize, and a render node exists. Actual rendering and hardware video decoding are not yet validated.
- ALSA reports no sound cards. HDMI codec modules are loaded, but there is no playback device. Upstream documents no sound for S905X4: https://github.com/devmfc/debian-on-amlogic .
- No video4linux/media, IR receiver, CEC, Wi-Fi or Bluetooth devices were exposed in this inspection. This does not establish that the hardware cannot be supported with other drivers or configuration.
- CPU and DDR temperatures were about 42 C at idle; sustained-load behavior is untested.
- The boot USB is connected at 480 Mbps. A 5000 Mbps USB root hub is present; SuperSpeed operation with an attached device is untested.

For the upcoming tests, Debian package indexes were refreshed and libdrm-tests, mesa-utils-bin, libegl1 and libgles2 (with dependencies) were installed on the running USB system. These diagnostic packages are not yet part of the generated image recipe. No kernel or DTB was replaced. Raw package and driver logs remain in the ignored archive.

The 1920x1080 at 60 Hz HDMI colour-pattern test completed with modetest exit status 0. The user confirmed seeing the pattern correctly (after correcting an initial report of seeing nothing). This verifies basic display scanout, not GPU rendering or hardware video decoding. No audio playback test was possible because no sound card was exposed.

## GPU context and audio investigation

Mesa eglinfo successfully creates GBM and surfaceless contexts on Mali-G31 (Panfrost), reporting OpenGL 3.1 and OpenGL ES 3.1. A separate software device (llvmpipe) is also enumerated. This confirms hardware context creation, not sustained rendering or video decode. X11/Wayland initialization fails because no display server is running.

The running DTB contains the HDMI DAI declaration but no sound-card, audio-controller, FRDDR or TDM audio nodes. ALSA still reports no sound cards. The matching kernel config includes common Meson/AXG/G12A audio modules; their availability does not provide an SC2 board audio path. The stock KM6 tree instead describes an audio bus at 0xfe330000, audio clocks, DDR manager and vendor SC2/TM2 audio interfaces. These depend on vendor bindings and cannot simply be copied into the mainline tree.

The inspected hkallweit SC2 source tree likewise provides no audio pipeline. The mainline TDMOUT driver matches AXG/G12A/SM1, while the inspected HDMI-routing driver matches G12A. No ready-to-apply SC2 audio fix was identified. The image maintainer explicitly reports that SC2 audio lacks driver support; subsequent S905X4 kernel-6.18 reports also show no sound card.

Audio remains unfixed. A native HDMI solution requires establishing compatible SC2 audio clock/DMA/TDM/routing support and a matching device tree, or using a kernel with a supported vendor audio stack. USB audio would be a separate output workaround, not a repair of HDMI audio. No speculative DTB or kernel replacement was applied.

Sources:
- https://github.com/devmfc/debian-on-amlogic/discussions/196
- https://github.com/devmfc/debian-on-amlogic/discussions/212
- https://github.com/hkallweit/linux-amlogic-sc2/blob/sc2/arch/arm64/boot/dts/amlogic/meson-sc2.dtsi
- https://github.com/torvalds/linux/blob/master/sound/soc/meson/axg-tdmout.c
- https://github.com/torvalds/linux/blob/master/sound/soc/meson/g12a-tohdmitx.c

## Experimental audio work started

The first live clock-controller overlay successfully bound on the KM6. A custom SC2 HDMI routing module and additive stereo playback DTB have been built and staged for the next boot. This supersedes the earlier investigation-only status; audio remains unverified. See ../drivers/sc2-audio/README.md for source, device state and rollback instructions.

## Confirmed HDMI audio

The corrected SC2 component initialization and codec-to-codec card recognition enabled TDM output clocks and DMA interrupts. The fresh boot loaded the modules and mixer routing automatically. Silent playback and the attended five-second left/right WAV test exited successfully; the user reported “works fine.” The generated revision 3 image embeds these tested module and DTB bytes.
