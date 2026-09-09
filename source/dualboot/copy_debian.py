#!/usr/bin/env python3
"""Copy the tested USB system to freshly formatted, validated internal mappings."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

WORK = Path('/root/km6-internal-work')
TARGET = Path('/mnt/km6-internal')


def run(*args, allowed=(0,)):
    result = subprocess.run([str(a) for a in args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end='', flush=True)
    if result.returncode not in allowed:
        raise RuntimeError('Command failed: ' + str(args[0]))
    return result.stdout.strip()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()


def main():
    require(os.geteuid() == 0, 'Run on the KM6 as root')
    require(run('findmnt', '-nro', 'SOURCE', '/') == '/dev/sda2', 'Expected USB source root')
    run('/usr/local/lib/km6-dualboot/km6-mpt-map')
    for name, sectors, start in [('linuxboot', 524288, 72830976), ('linuxroot', 48787456, 73371648)]:
        dev = os.stat('/dev/mmcblk1').st_rdev
        expected = '0 %d linear %d:%d %d' % (sectors, os.major(dev), os.minor(dev), start)
        require(run('dmsetup', 'table', 'km6-' + name) == expected, 'Unexpected mapper backing device')
    require(run('blkid', '-s', 'LABEL', '-o', 'value', '/dev/mapper/km6-linuxroot') == 'KM6DEBIAN', 'Wrong target root label')
    require(run('blkid', '-s', 'LABEL', '-o', 'value', '/dev/mapper/km6-linuxboot') == 'KM6BOOT', 'Wrong target boot label')
    TARGET.mkdir(parents=True, exist_ok=True)
    if os.path.ismount(TARGET):
        require(run('findmnt', '-nro', 'SOURCE', str(TARGET)) == '/dev/mapper/km6-linuxroot', 'Wrong mounted target')
    else:
        run('mount', '/dev/mapper/km6-linuxroot', TARGET)
    marker = TARGET / '.km6-copy-incomplete'
    require(marker.exists() or set(p.name for p in TARGET.iterdir()) <= {'lost+found'}, 'Target is not empty and has no incomplete-copy marker')
    marker.write_text('Copy from this KM6 USB root is incomplete.\n')
    (TARGET / 'boot').mkdir(exist_ok=True)
    if os.path.ismount(TARGET / 'boot'):
        require(run('findmnt', '-nro', 'SOURCE', str(TARGET / 'boot')) == '/dev/mapper/km6-linuxboot', 'Wrong mounted boot target')
    else:
        run('mount', '/dev/mapper/km6-linuxboot', TARGET / 'boot')
    # Stop applications so their user state is consistent during the copy.
    run('systemctl', 'stop', 'lightdm', 'km6-vnc.service', 'tailscaled')
    excludes = ['/boot/***', '/dev/***', '/proc/***', '/sys/***', '/run/***', '/tmp/***', '/mnt/***', '/media/***',
                '/lost+found', '/root/km6-internal-work/***', '/var/tmp/km6-*']
    run('rsync', '-aHAXSx', '--numeric-ids', '--stats', *('--exclude=' + x for x in excludes), '/', str(TARGET) + '/')
    for name in ('dev', 'proc', 'sys', 'run', 'tmp', 'mnt', 'media'):
        (TARGET / name).mkdir(exist_ok=True)
    (TARGET / 'tmp').chmod(0o1777)
    run('rsync', '-rt', '--modify-window=1', '--exclude=uInitrd-km6-menu.before*', '--exclude=DEB*.BIN', '/boot/', str(TARGET / 'boot') + '/')
    fstab = (TARGET / 'etc/fstab').read_text()
    lines = []
    for line in fstab.splitlines():
        fields = line.split()
        if fields and not line.lstrip().startswith('#') and len(fields) >= 2:
            if fields[1] == '/':
                line = '/dev/mapper/km6-linuxroot / ext4 defaults,noatime,commit=5,errors=remount-ro 0 1'
            elif fields[1] == '/boot':
                line = '/dev/mapper/km6-linuxboot /boot vfat nosuid,nodev,noexec,uid=0,gid=0,umask=177 0 2'
        lines.append(line)
    (TARGET / 'etc/fstab').write_text('\n'.join(lines) + '\n')
    config = (TARGET / 'boot/boot.config').read_text()
    config = '\n'.join(line for line in config.splitlines() if not line.startswith(('root=', 'rd_img=', 'bootargs15=')))
    config += '\nroot=/dev/mapper/km6-linuxroot\nrd_img=uInitrd-km6-menu.img\nbootargs15=km6_menu=enabled panic=10\n'
    (TARGET / 'boot/boot.config').write_text(config)
    run('mkimage', '-A', 'arm64', '-O', 'linux', '-T', 'ramdisk', '-C', 'none', '-n', 'KM6 internal boot menu',
        '-d', WORK / 'internal.initrd', TARGET / 'boot/uInitrd-km6-menu.img')
    run('mkimage', '-C', 'none', '-A', 'arm', '-T', 'script', '-d', WORK / 'internal-bootscript.src', TARGET / 'boot/bootscript')
    critical = [Path('/boot/vmlinuz-6.18.49-meson64'), Path('/boot/km6-sc2-audio-test.dtb')]
    critical += list(Path('/lib/modules/6.18.49-meson64').rglob('km6*.ko'))
    require(len(critical) >= 5, 'Expected Ethernet and both HDMI audio modules')
    hashes = {}
    for path in critical:
        target = TARGET / str(path).lstrip('/')
        hashes[str(path)] = sha(path)
        require(sha(target) == hashes[str(path)], 'Critical file copy mismatch: ' + str(path))
    (WORK / 'copy-verification.json').write_text(json.dumps(hashes, indent=2) + '\n')
    marker.unlink()
    os.sync()
    run('umount', TARGET / 'boot')
    run('umount', TARGET)
    run('fsck.vfat', '-n', '/dev/mapper/km6-linuxboot')
    run('e2fsck', '-f', '-n', '/dev/mapper/km6-linuxroot')
    print('Debian copy complete; critical drivers verified and both target filesystems checked.', flush=True)
    print('Persistent boot command has not been changed by this script.', flush=True)


if __name__ == '__main__':
    main()
