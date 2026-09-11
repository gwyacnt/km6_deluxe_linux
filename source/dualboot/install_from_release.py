#!/usr/bin/env python3
"""Install the release USB system internally on the supported 64 GB KM6."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import struct

BUNDLE = Path('/usr/local/share/km6-installer')
WORK = Path('/root/km6-internal-work')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='shrink Android data and install Debian internally')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Run with sudo.')
    if subprocess.check_output(['findmnt', '-nro', 'SOURCE', '/'], text=True).strip() != '/dev/sda2':
        raise SystemExit('Boot the release USB with no other storage attached. Internal root is not an installation source.')
    spec = json.loads((BUNDLE / 'release-layout.json').read_text())
    original = {}
    with open('/dev/mmcblk1', 'rb', buffering=0) as f:
        for name, region in spec['original_regions'].items():
            f.seek(region['offset'])
            data = f.read(region['size'])
            digest = hashlib.sha256(data).hexdigest()
            if name.startswith('dtb_'):
                words = struct.unpack('<65536I', data)
                valid = words[-4] == 0x00447e41 and words[-3] == 1 and (sum(words[:-1]) & 0xffffffff) == words[-1]
                valid &= hashlib.sha256(data[:258048]).hexdigest() == spec['original_dtb_payload_sha256']
            else:
                valid = name == 'data_tail' or digest == region['sha256']
            if not valid:
                raise SystemExit('Unsupported or already modified Android metadata: ' + name)
            original[name] = {**region, 'sha256': digest}
    if WORK.exists():
        raise SystemExit('Existing installation work directory found. Preserve its backups and inspect before retrying.')
    WORK.mkdir(mode=0o700)
    for path in BUNDLE.iterdir():
        if path.is_file():
            shutil.copy2(path, WORK / path.name)
    manifest = {'original_regions': original, 'candidate_files': spec['candidate_files']}
    (WORK / 'install-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    try:
        subprocess.run(['python3', str(WORK / 'install_layout.py')] + (['--apply'] if args.apply else []), check=True)
        if not args.apply:
            print('Validation passed. Run again with --apply to install; no eMMC writes were performed.')
            shutil.rmtree(WORK)
            return
        subprocess.run(['python3', str(WORK / 'copy_debian.py')], check=True)
        subprocess.run(['python3', str(WORK / 'activate_boot.py'), '--apply'], check=True)
        print('Installation complete. Shut down, remove the USB stick and power on normally.')
        print('Android is the timed default; use the keyboard to choose Debian.')
    except Exception:
        print('Stopped. Keep the USB attached and preserve /root/km6-internal-work for recovery.')
        raise


if __name__ == '__main__':
    main()
