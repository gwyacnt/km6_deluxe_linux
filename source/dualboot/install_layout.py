#!/usr/bin/env python3
"""Board-specific layout transaction. Defaults to validation; --apply shrinks/formats eMMC."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
from plan_storage import DEVICE_SIZE, MIB, parse_mpt, propose

DEVICE = '/dev/mmcblk1'
WORK = Path('/root/km6-internal-work')


def command(*args, allowed=(0,)):
    result = subprocess.run([str(a) for a in args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end='', flush=True)
    if result.returncode not in allowed:
        raise RuntimeError('Command failed: ' + str(args[0]))
    return result.stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_region(offset, size):
    with open(DEVICE, 'rb', buffering=0) as f:
        f.seek(offset)
        data = f.read(size)
    require(len(data) == size, 'Short eMMC read')
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    require(os.geteuid() == 0, 'Run on the KM6 as root')
    size = int(Path('/sys/class/block/mmcblk1/size').read_text()) * 512
    require(size == DEVICE_SIZE, 'Wrong eMMC size')
    require(Path('/sys/class/block/mmcblk1/device/name').read_text().strip() == 'A1511X', 'Wrong eMMC model')
    root = subprocess.check_output(['findmnt', '-nro', 'SOURCE', '/'], text=True).strip()
    require(root == '/dev/sda2', 'This transaction must run from the tested USB root')
    root_options = subprocess.check_output(['findmnt', '-nro', 'OPTIONS', '/'], text=True).strip().split(',')
    require('rw' in root_options and 'emergency_ro' not in root_options, 'USB root is not writable')
    manifest = json.loads((WORK / 'install-manifest.json').read_text())
    for name, digest in manifest['candidate_files'].items():
        require(sha((WORK / name).read_bytes()) == digest, 'Candidate hash mismatch: ' + name)
    old = {}
    for name, region in manifest['original_regions'].items():
        data = read_region(region['offset'], region['size'])
        require(sha(data) == region['sha256'], 'Original region changed: ' + name)
        old[name] = data
    parts = parse_mpt(old['mpt'], size)
    expected = propose(parts, size)
    require(parse_mpt((WORK / 'mpt.bin').read_bytes(), size) == expected, 'Candidate geometry mismatch')
    mounts = subprocess.check_output(['lsblk', '-nrpo', 'NAME,MOUNTPOINTS', DEVICE], text=True)
    require(all(len(line.split()) == 1 for line in mounts.splitlines()), 'An eMMC filesystem is mounted')
    print('Validated original eMMC metadata and signed candidates.', flush=True)
    print('Android data: 32 GiB; Linux boot: 256 MiB; Linux root: %.2f GiB.' % (expected[-1]['size'] / 2**30), flush=True)
    if not args.apply:
        print('Validation only. No writes performed.')
        return

    backups = WORK / 'backups'
    backups.mkdir(mode=0o700, exist_ok=True)
    for name, data in old.items():
        path = backups / (name + '.bin')
        require(not path.exists(), 'Existing transaction backup; inspect previous attempt before retrying')
        path.write_bytes(data)
        path.chmod(0o600)
    os.sync()
    loops = json.loads(subprocess.check_output(['losetup', '--json', '-j', DEVICE], text=True))['loopdevices']
    for loop in loops:
        require(loop['ro'] and int(loop['offset']) == parts[-1]['offset'], 'Unexpected existing loop mapping')
        command('losetup', '-d', loop['name'])
    android = command('losetup', '--find', '--show', '--offset', parts[-1]['offset'], '--sizelimit', parts[-1]['size'], DEVICE)
    try:
        command('e2fsck', '-f', '-y', android, allowed=(0, 1))
        command('resize2fs', android, '32G')
        command('e2fsck', '-f', '-n', android)
        with open(android, 'rb', buffering=0) as f:
            f.seek(1024)
            superblock = f.read(1024)
        require(struct.unpack_from('<I', superblock, 4)[0] == 8388608 and
                struct.unpack_from('<I', superblock, 24)[0] == 2, 'Unexpected resized Android filesystem geometry')
    finally:
        command('losetup', '-d', android)
    print('Android data filesystem shrunk and checked.', flush=True)

    def write_region(offset, data):
        require(offset % 512 == 0 and len(data) % 512 == 0, 'Unaligned metadata write')
        fd = os.open(DEVICE, os.O_RDWR | os.O_SYNC)
        try:
            done = 0
            while done < len(data):
                n = os.pwrite(fd, data[done:], offset + done)
                require(n > 0, 'Short metadata write')
                done += n
            os.fsync(fd)
        finally:
            os.close(fd)
        require(read_region(offset, len(data)) == data, 'Metadata read-back mismatch')

    # No bootloader writes. These regions are all backed up above.
    write_region(1168 * MIB, (WORK / 'PARTITION.vbmeta').read_bytes().ljust(4096, b'\0'))
    slot = (WORK / 'dtb-slot.bin').read_bytes()
    write_region(40 * MIB, slot)
    write_region(40 * MIB + 262144, slot)
    mpt = (WORK / 'mpt.bin').read_bytes()
    write_region(36 * MIB, mpt + read_region(36 * MIB + len(mpt), 1536 - len(mpt)))
    print('Both DTB copies, AVB metadata and MPT installed and verified.', flush=True)
    command('modprobe', 'dm_mod')
    mappings = command('/usr/local/lib/km6-dualboot/km6-mpt-map')
    for line in mappings.splitlines():
        name, table = line.split(' ', 1)
        command('dmsetup', 'create', name, '--table', table)
    command('dmsetup', 'mknodes')
    command('mkfs.vfat', '-F', '32', '-n', 'KM6BOOT', '/dev/mapper/km6-linuxboot')
    command('mkfs.ext4', '-L', 'KM6DEBIAN', '-m', '1', '-E', 'lazy_itable_init=0,lazy_journal_init=0', '/dev/mapper/km6-linuxroot')
    os.sync()
    print('Internal filesystems created. Debian copy and boot-command installation are still required.', flush=True)


if __name__ == '__main__':
    main()
