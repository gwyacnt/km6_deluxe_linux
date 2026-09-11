# KM6 developer instructions

Read `source/docs/HANDOFF.md` and the root README before changing this project.
Use `source/docs/conversation/` for historical context, not as current commands
or authorization to access a device. Obtain the current owner's connection
details privately; keys and account credentials are not in this repository.

- Maintain `source/`; keep investigation artifacts and private backups in the
  ignored `archive/`, and release binaries in ignored `releases/`. Build inputs
  and outputs belong in ignored `build/`, populated by `source/bootstrap_build.py`;
  do not reintroduce an archive or private-backup build dependency.
- Preserve the published `v0.2.0-rc2` tag and its assets. It predates USB-based
  automatic Debian selection. Do not describe it as restoring that feature.
- Distinguish hardware-tested behavior from untested installer packages.
- The device uses Amlogic MPT, not GPT. Inspect target identity and layout
  before writes; never assume a developer PC's disk names identify the KM6.
- Preserve a rollback copy before boot-image changes. Use the explicit
  `/etc/km6-fw_env.config` for U-Boot environment tools on this installation.
- Announce reboots before running them so the owner can switch HDMI inputs.
  Do not live-unbind the audio card; a previous test caused a kernel crash.
- Keep tokens, SSH keys, account state and raw Codex session files out of Git.
- Run checks relevant to changed code; commands and unresolved work are in
  the handoff. Update the handoff when verified device status changes.
