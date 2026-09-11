#!/usr/bin/env python3
"""Prepare an isolated build workspace from pinned public release assets."""
import argparse
import hashlib
import importlib.util
import json
import lzma
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import tarfile

from reproduce import fetch

SOURCE = Path(__file__).resolve().parent


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def extract_sdk(archive, destination):
    # The data filter refuses traversal and links escaping the destination.
    with tarfile.open(archive) as t:
        for member in t:
            if not member.name.startswith('output/'):
                raise ValueError('Unexpected SDK member: ' + member.name)
        t.extractall(destination, filter='data')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, default=SOURCE.parent / 'build')
    p.add_argument('--directory', type=Path, help='verified download cache')
    a = p.parse_args()
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise SystemExit('Prepared SDK requires an x86_64 Linux host; see BUILD-STATUS.md.')
    for tool in ('make', 'gcc', 'openssl', '/usr/sbin/debugfs', '/usr/sbin/e2fsck',
                 '/usr/sbin/depmod', '/usr/sbin/modinfo', '/usr/sbin/modprobe'):
        if not shutil.which(tool):
            raise SystemExit('Missing host tool: ' + tool + '; see BUILD-STATUS.md.')
    work = a.workspace.resolve()
    if work.exists():
        raise SystemExit('Choose a nonexistent build workspace; existing files are never overwritten.')
    spec = json.loads((SOURCE / 'manifests/build-inputs.json').read_text())
    cache = a.directory or SOURCE.parent / 'downloads' / spec['tag']
    cache.mkdir(parents=True, exist_ok=True)
    assets = {entry['name']: fetch(cache, spec['tag'], entry) for entry in spec['assets']}
    work.mkdir(parents=True)
    extract_sdk(assets['km6-build-sdk.tar.xz'], work)
    stock = work / 'Stock' / spec['stock_image']
    stock.parent.mkdir()
    shutil.copyfile(assets[spec['stock_image']], stock)
    # Extract only the public Android components required by the layout builder.
    # The builder resolves its output directories from KM6_WORKDIR at import time.
    os.environ['KM6_WORKDIR'] = str(work)
    modspec = importlib.util.spec_from_file_location('firmware_builder', SOURCE / 'firmware/build_modified.py')
    mod = importlib.util.module_from_spec(modspec)
    modspec.loader.exec_module(mod)
    out = work / 'output/extracted/stock'
    out.mkdir(parents=True)
    with stock.open('rb') as f:
        for row in mod.items(f):
            if row['main'] == 'PARTITION' and row['sub'] in ('_aml_dtb', 'vbmeta'):
                f.seek(row['offset'])
                (out / ('PARTITION.' + row['sub'])).write_bytes(f.read(row['size']))
    usb = work / 'output/debian-usb'
    usb.mkdir(parents=True)
    image = usb / 'debian.img'
    with lzma.open(assets[spec['upstream_image']], 'rb') as src, image.open('xb') as dst:
        shutil.copyfileobj(src, dst, 4 * 1024 * 1024)
    # Extract the original ext4 partition before applying FAT boot customizations.
    with image.open('rb') as f:
        mbr = f.read(512)
        assert mbr[510:] == b'\x55\xaa'
        offset, sectors = struct.unpack_from('<II', mbr, 446 + 16 + 8)
        assert offset == 557056 and sectors > 0
        assert (offset + sectors) * 512 <= image.stat().st_size
        f.seek(offset * 512)
        with (usb / 'rootfs.ext4').open('xb') as dst:
            left = sectors * 512
            while left:
                data = f.read(min(left, 4 * 1024 * 1024))
                if not data:
                    raise ValueError('Truncated root filesystem')
                dst.write(data)
                left -= len(data)
    shutil.copytree(SOURCE / 'usb/upstream-boot', usb / 'boot-original')
    env = {**os.environ, 'KM6_WORKDIR': str(work)}
    subprocess.run(['python3', str(SOURCE / 'usb/prepare.py')], env=env, check=True)
    report = {'release': spec['tag'], 'prepared_usb_sha256': digest(image),
              'rootfs_sha256': digest(usb / 'rootfs.ext4')}
    (work / 'prepared-inputs.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Build inputs ready:', work)


if __name__ == '__main__':
    main()
