#!/usr/bin/env python3
"""Fetch this checkpoint's assets and optionally write its USB image on Linux."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import stat
import urllib.request

MANIFEST = Path(__file__).parent / 'manifests/checkpoint-assets.json'
CHUNK = 4 * 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(CHUNK), b''):
            h.update(b)
    return h.hexdigest()


def fetch(directory, tag, entry):
    path = directory / entry['name']
    if path.exists() and path.stat().st_size == entry['size'] and digest(path) == entry['sha256']:
        print('Verified cached:', path.name, flush=True)
        return path
    if path.is_symlink():
        raise RuntimeError('Refusing a symlink download destination')
    temporary = path.with_name(path.name + '.part')
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError('An incomplete download already exists: ' + str(temporary))
    url = 'https://github.com/gwyacnt/km6_deluxe_linux/releases/download/' + tag + '/' + entry['name']
    print('Downloading:', path.name, flush=True)
    h = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(url, timeout=60) as src, temporary.open('xb') as dst:
        for data in iter(lambda: src.read(CHUNK), b''):
            dst.write(data)
            h.update(data)
            size += len(data)
    if size != entry['size'] or h.hexdigest() != entry['sha256']:
        raise RuntimeError('Downloaded size/hash mismatch; retained ' + str(temporary))
    temporary.replace(path)
    return path


def validate_usb(path, minimum_size):
    path = path.resolve(strict=True)
    info = path.stat()
    if not stat.S_ISBLK(info.st_mode):
        raise RuntimeError('USB destination must be a block device')
    sysdev = Path('/sys/dev/block/%d:%d' % (os.major(info.st_rdev), os.minor(info.st_rdev))).resolve(strict=True)
    if (sysdev / 'partition').exists() or '/usb' not in str(sysdev):
        raise RuntimeError('Destination must be a whole USB disk; internal disks and partitions are refused')
    if int((sysdev / 'size').read_text()) * 512 < minimum_size:
        raise RuntimeError('USB stick is too small')
    devices = set()
    pending = [sysdev] + [p for p in sysdev.iterdir() if (p / 'partition').exists()]
    while pending:
        p = pending.pop()
        dev = (p / 'dev').read_text().strip()
        if dev in devices:
            continue
        devices.add(dev)
        pending.extend(x.resolve() for x in (p / 'holders').glob('*'))
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        if line.split()[2] in devices:
            raise RuntimeError('A destination partition is mounted. Unmount its partitions first.')
    for line in Path('/proc/swaps').read_text().splitlines()[1:]:
        swap = Path(line.split()[0])
        if swap.exists():
            s = swap.stat()
            device = s.st_rdev if stat.S_ISBLK(s.st_mode) else s.st_dev
            if '%d:%d' % (os.major(device), os.minor(device)) in devices:
                raise RuntimeError('Destination backs active swap')
    return path


def write_usb(image, target, raw_size):
    # Validate decompression and exact length before opening the disk for writing.
    size = 0
    h = hashlib.sha256()
    with lzma.open(image, 'rb') as src:
        for b in iter(lambda: src.read(CHUNK), b''):
            size += len(b)
            h.update(b)
    if size != raw_size:
        raise RuntimeError('Unexpected decompressed image size')
    expected = h.digest()
    target = validate_usb(target, raw_size)
    # O_EXCL also asks the kernel to refuse a busy block device.
    fd = os.open(target, os.O_WRONLY | os.O_EXCL)
    try:
        with lzma.open(image, 'rb') as src:
            for b in iter(lambda: src.read(CHUNK), b''):
                view = memoryview(b)
                while view:
                    count = os.write(fd, view)
                    if count <= 0:
                        raise RuntimeError('Short USB write')
                    view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    h = hashlib.sha256()
    with target.open('rb', buffering=0) as src:
        remaining = raw_size
        while remaining:
            b = src.read(min(CHUNK, remaining))
            if not b:
                raise RuntimeError('Short USB verification read')
            h.update(b)
            remaining -= len(b)
    if h.digest() != expected:
        raise RuntimeError('USB read-back verification failed')
    print('USB image written and verified. Safely remove the stick.', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--download-all', action='store_true', help='download every pinned release asset')
    p.add_argument('--usb', type=Path, help='whole USB disk, for example /dev/sdb')
    p.add_argument('--write', action='store_true', help='erase the specified USB disk and write/verify the image')
    p.add_argument('--directory', type=Path, help='download cache; default downloads/<tag>')
    args = p.parse_args()
    if not args.download_all and not args.usb:
        p.error('Use --download-all or --usb DEVICE')
    if args.write and not args.usb:
        p.error('--write requires --usb')
    spec = json.loads(MANIFEST.read_text())
    if args.usb:
        if args.write and os.geteuid() != 0:
            p.error('USB writing requires sudo/root')
        validate_usb(args.usb, spec['raw_image_size'])
    directory = args.directory or Path('downloads') / spec['tag']
    directory.mkdir(parents=True, exist_ok=True)
    image = None
    for entry in spec['assets']:
        is_image = entry['name'] == spec['usb_image']
        if args.download_all or is_image:
            path = fetch(directory, spec['tag'], entry)
            if is_image:
                image = path
    if args.write:
        print('Writing and verifying', args.usb, '— all previous contents will be replaced.', flush=True)
        write_usb(image, args.usb, spec['raw_image_size'])
    elif args.usb:
        print('USB and image validated. Add --write to erase/write the stick.')


if __name__ == '__main__':
    main()
