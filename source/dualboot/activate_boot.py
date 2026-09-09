#!/usr/bin/env python3
"""Validate the completed internal copy, then optionally enable its boot command."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

WORK = Path('/root/km6-internal-work')
DEVICE = '/dev/mmcblk1'
ENV_OFFSET = 0x39400000


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(offset, size):
    with open(DEVICE, 'rb', buffering=0) as f:
        f.seek(offset)
        return f.read(size)


def environment():
    raw = read(ENV_OFFSET, 65536)
    require(len(raw) == 65536 and zlib.crc32(raw[4:]) == struct.unpack_from('<I', raw)[0], 'Invalid environment CRC')
    entries = raw[4:].split(b'\0\0', 1)[0].split(b'\0')
    return raw, dict(x.split(b'=', 1) for x in entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    require(os.geteuid() == 0, 'Run on the KM6 as root')
    require(not os.path.ismount('/mnt/km6-internal'), 'Copy target must be unmounted and checked first')
    require((WORK / 'copy-verification.json').exists(), 'Missing completed-copy verification')
    for name, offset, size in [('mpt.bin', 36 * 2**20, 1304),
                               ('dtb-slot.bin', 40 * 2**20, 262144),
                               ('dtb-slot.bin', 40 * 2**20 + 262144, 262144),
                               ('PARTITION.vbmeta', 1168 * 2**20, 4096)]:
        require(read(offset, size) == (WORK / name).read_bytes().ljust(size, b'\0'), 'Installed metadata differs: ' + name)
    subprocess.run(['/usr/local/lib/km6-dualboot/km6-mpt-map'], check=True)
    subprocess.run(['e2fsck', '-f', '-n', '/dev/mapper/km6-linuxroot'], check=True)
    subprocess.run(['fsck.vfat', '-n', '/dev/mapper/km6-linuxboot'], check=True)
    raw, before = environment()
    require(before.get(b'km6_next', b'') == b'', 'An Android one-shot boot is already armed')
    values = {b'km6_internal': (WORK / 'internal-load.txt').read_bytes().strip(),
              b'bootcmd': (WORK / 'bootcmd-internal.txt').read_bytes().strip()}
    require(all(values.values()), 'Empty boot command')
    if not args.apply:
        print('Internal metadata, filesystems and environment validated; no boot-setting writes.')
        return
    backup = WORK / 'env-before-internal.bin'
    require(not backup.exists(), 'Activation backup already exists; inspect before retrying')
    backup.write_bytes(raw)
    backup.chmod(0o600)
    os.sync()
    for name, value in values.items():
        subprocess.run(['fw_setenv', '-c', '/etc/km6-fw_env.config', name.decode(), value.decode()], check=True)
    after_raw, after = environment()
    expected = {**before, **values}
    require(after == expected, 'Environment read-back did not match the intended changes')
    (WORK / 'env-after-internal.bin').write_bytes(after_raw)
    os.sync()
    print('Internal boot enabled. Only km6_internal and bootcmd changed; Android is the timed default.')


if __name__ == '__main__':
    main()
