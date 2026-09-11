# Desktop performance checkpoint

Measured on the internal Debian installation, 2026-09-09:

- Panfrost Mali-G31 acceleration and Firefox WebRender are active.
- No hardware video decoder is exposed; Firefox reports hardware decoding unavailable.
- Samples showed no storage I/O waiting and over 2 GiB available memory.
- The current CPU device tree has no CPU-frequency policy. A governor setting would not change it.

The local 160-element animation benchmark recorded 98 frames in its measured
ten seconds with 1080p/compositing, 131 and 136 at 1080p without compositing,
and 170 at 720p without compositing. Median frame intervals were approximately
100, 67 and 50 ms respectively. This is a synthetic rendering comparison,
not a claim that every website or YouTube video is that much faster. Firefox
was also open in another profile, so these are practical samples, not isolated
laboratory measurements. Raw summaries are in `measurements-2026-09-09.json`.

An eight-second synthetic 1080p30 clip decoded four times with FFmpeg reached
80 fps for H.264 and 71 fps for VP9, using software decoding. Encoding settings
and workloads differ; the result supports preferring H.264 on this setup, not
a universal codec comparison.

`km6-desktop-mode` runs at Xfce login. Its default `fast` setting uses 720p60
and disables Xfce compositing. Run `km6-desktop-mode sharp` for 1080p60, or
`km6-desktop-mode fast` to return to 720p. The choice persists per user. VNC
keeps its own geometry. Lower resolution trades detail for less rendering work.

Firefox keeps GPU rendering, disables AV1 and uses a modest persistent disk
cache on eMMC. The policy installs signed uBlock Origin and enhanced-h264ify
packages from local files; both remain removable. Enhanced-h264ify selects
H.264 on YouTube. Its default does not block 60 fps; that is an optional setting
in the add-on. Prefer 720p30 when playback remains slow.

Sources: [Mozilla performance settings](https://support.mozilla.org/en-US/kb/performance-settings),
[enhanced-h264ify source](https://github.com/alextrv/enhanced-h264ify),
[uBlock Origin source](https://github.com/gorhill/uBlock).
Pinned add-on versions and hashes accompany this directory. Firefox ESR 140
can continue allowing VP9 despite its preference being disabled when hardware
decoding is unavailable; a preference-only VP9 change was therefore not used.

The kernel/driver limitation remains: these adjustments do not add hardware
video decoding or establish Android-equivalent playback performance.
