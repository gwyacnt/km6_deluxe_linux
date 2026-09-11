#!/usr/bin/env python3
"""Build a sanitized installation USB image from the working internal KM6 OS.

Run on the KM6 as root with --bundle pointing to a prepared release bundle.
Writes only a new build directory and loop devices backed by its regular image.
The running system and eMMC partition contents are never modified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zlib


def run(*args):
    subprocess.run([str(x) for x in args], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--output', type=Path, default=Path('/var/lib/km6-image-build'))
    a = p.parse_args()
    if os.geteuid() or a.output.exists():
        raise SystemExit('Run as root and choose a nonexistent output directory.')
    if subprocess.check_output(['findmnt', '-nro', 'SOURCE', '/'], text=True).strip() != '/dev/mapper/km6-linuxroot':
        raise SystemExit('Expected the tested internal Debian installation.')
    # Keep the build under an excluded path even when an alternate output is used.
    a.output = a.output.resolve()
    if not a.output.is_relative_to('/var/lib'):
        raise SystemExit('Output must be under /var/lib, which is excluded from the root copy.')
    a.output.mkdir(mode=0o700)
    stage = a.output / 'root'
    stage.mkdir()
    excluded = ['boot', 'home', 'root', 'dev', 'proc', 'sys', 'run', 'tmp', 'mnt', 'media',
                'var/lib', 'var/log', 'var/cache', 'var/tmp', 'lost+found']
    run('rsync', '-aHAXSx', *('--exclude=/' + x + '/***' for x in excluded), '/', str(stage) + '/')
    for name in excluded:
        (stage / name).mkdir(parents=True, exist_ok=True)
    for name in ['apt', 'dpkg', 'alsa', 'ucf', 'python', 'xfonts', 'xkb', 'pam']:
        src = Path('/var/lib') / name
        if src.exists():
            run('rsync', '-aHAXS', src, str(stage / 'var/lib') + '/')
    for name in ['tmp', 'var/tmp']:
        (stage / name).chmod(0o1777)
    for pattern in ['etc/ssh/ssh_host_*', 'etc/NetworkManager/system-connections/*',
                    'etc/wpa_supplicant/*.conf', 'etc/*-', 'etc/ssl/private/*',
                    'etc/apt/auth.conf', 'etc/apt/auth.conf.d/*', 'etc/credstore/*',
                    'etc/credstore.encrypted/*']:
        for path in stage.glob(pattern):
            if path.is_file() or path.is_symlink():
                path.unlink()
    # No existing home directories, private service state, journal, caches or keys.
    for name in ['etc/machine-id', 'etc/subuid', 'etc/subgid']:
        (stage / name).write_text('')
    passwd = (stage / 'etc/passwd').read_text().splitlines()
    users = {line.split(':')[0] for line in passwd if int(line.split(':')[2]) >= 1000} | {'root'}
    shadow = []
    for line in (stage / 'etc/shadow').read_text().splitlines():
        fields = line.split(':')
        if fields[0] in users:
            fields[1] = '!'
        shadow.append(':'.join(fields))
    (stage / 'etc/shadow').write_text('\n'.join(shadow) + '\n')
    (stage / 'etc/shadow').chmod(0o640)
    home = stage / 'home/samer'
    shutil.copytree(stage / 'etc/skel', home, symlinks=True)
    run('chown', '-R', '1000:1000', home)
    (stage / 'root').chmod(0o700)
    (stage / 'etc/hostname').write_text('km6-deluxe\n')
    (stage / 'etc/fstab').write_text('/dev/sda2 / ext4 defaults,noatime,errors=remount-ro 0 1\n/dev/sda1 /boot vfat nosuid,nodev,noexec,umask=177 0 2\n')
    for name in ['km6-vnc.service', 'km6-vnc-lan.socket', 'km6-vnc-lan.service']:
        for link in (stage / 'etc/systemd/system').glob('*.wants/' + name):
            link.unlink()
    # Preserve package installation state, not the personal Tailscale identity.
    (stage / 'var/lib/dbus').mkdir(exist_ok=True)
    (stage / 'var/lib/dbus/machine-id').symlink_to('/etc/machine-id')
    bundle = stage / 'usr/local/share/km6-installer'
    shutil.copytree(a.bundle, bundle)
    # Preserve the running boot policy even when the metadata bundle originated
    # from an earlier checkpoint. copy_debian.py uses this payload internally.
    ramdisk = Path('/boot/uInitrd-km6-menu.img').read_bytes()
    if (len(ramdisk) < 64 or struct.unpack_from('>I', ramdisk)[0] != 0x27051956 or
            struct.unpack_from('>I', ramdisk, 12)[0] != len(ramdisk) - 64 or
            struct.unpack_from('>I', ramdisk, 24)[0] != zlib.crc32(ramdisk[64:])):
        raise RuntimeError('Current boot ramdisk failed size/CRC validation')
    (bundle / 'internal.initrd').write_bytes(ramdisk[64:])
    for installed, name in [('/etc/initramfs-tools/hooks/km6-menu', 'initramfs-hook'),
                            ('/etc/initramfs-tools/scripts/local-premount/km6-menu', 'initramfs-menu')]:
        shutil.copy2(installed, bundle / name)
    shutil.copy2(bundle / 'first_boot.py', stage / 'usr/local/sbin/km6-first-boot')
    (stage / 'usr/local/sbin/km6-first-boot').chmod(0o755)
    shutil.copy2(bundle / 'install_from_release.py', stage / 'usr/local/sbin/km6-install-internal')
    (stage / 'usr/local/sbin/km6-install-internal').chmod(0o755)
    shutil.copy2(bundle / 'km6-first-boot.service', stage / 'etc/systemd/system/km6-first-boot.service')
    (stage / 'etc/systemd/system/multi-user.target.wants/km6-first-boot.service').symlink_to('../km6-first-boot.service')
    boot = a.output / 'boot'
    boot.mkdir()
    run('rsync', '-rt', '--exclude=DEB*.BIN', '--exclude=*.before*', '--exclude=*.bak',
        '--exclude=*-report.txt', '/boot/', str(boot) + '/')
    config = '\n'.join(x for x in (boot / 'boot.config').read_text().splitlines()
                       if not x.startswith(('root=', 'rd_img=', 'bootargs15=')))
    (boot / 'boot.config').write_text(config + '\nroot=/dev/sda2\nrd_img=uInitrd-km6-menu.img\nbootargs15=km6_menu=repair panic=10\n')
    # This same script supports FAT over USB and eMMC; omit historical debug writes.
    run('mkimage', '-C', 'none', '-A', 'arm', '-T', 'script', '-d', bundle / 'internal-bootscript.src', boot / 'bootscript')
    with (a.output / 'packages.tsv').open('w') as f:
        subprocess.run(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\n'], stdout=f, check=True)
    # Audit the staging tree before any distributable archive is created.
    assert not any((stage / 'root').iterdir())
    assert not list(stage.glob('etc/ssh/ssh_host_*'))
    assert not (stage / 'var/lib/tailscale').exists()
    assert not (home / '.mozilla').exists()
    assert all(line.split(':')[1] in ('!', '*', '!*', '!!') for line in (stage / 'etc/shadow').read_text().splitlines())
    print('Sanitized filesystem staged; constructing regular USB image.', flush=True)
    image = a.output / 'km6-debian-desktop-installer.img'
    start, boot_sectors, root_sectors = 2048, 524288, 12582912
    total = start + boot_sectors + root_sectors
    with image.open('wb') as f:
        f.truncate(total * 512)
        mbr = bytearray(512)
        for i, (kind, offset, length) in enumerate([(0x0c, start, boot_sectors), (0x83, start + boot_sectors, root_sectors)]):
            struct.pack_into('<B3sB3sII', mbr, 446 + i * 16, 0, b'\xfe\xff\xff', kind, b'\xfe\xff\xff', offset, length)
        mbr[510:] = b'\x55\xaa'
        f.write(mbr)
    loops = []
    mount = a.output / 'fat-mount'
    mount.mkdir()
    try:
        for offset, length in [(start, boot_sectors), (start + boot_sectors, root_sectors)]:
            loops.append(subprocess.check_output(['losetup', '--find', '--show', '--offset', str(offset * 512), '--sizelimit', str(length * 512), str(image)], text=True).strip())
        run('mkfs.vfat', '-F', '32', '-n', 'KM6USB', loops[0])
        run('mkfs.ext4', '-F', '-L', 'KM6USBROOT', '-m', '1', '-d', stage, loops[1])
        run('mount', loops[0], mount)
        run('rsync', '-rt', str(boot) + '/', str(mount) + '/')
        run('umount', mount)
        run('fsck.vfat', '-n', loops[0])
        run('e2fsck', '-f', '-n', loops[1])
    finally:
        if os.path.ismount(mount):
            run('umount', mount)
        for loop in loops:
            run('losetup', '-d', loop)
    run('xz', '-T2', '-1', str(image))
    compressed = image.with_suffix('.img.xz')
    with compressed.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    (a.output / 'SHA256SUMS').write_text(digest + '  ' + compressed.name + '\n')
    print('Release candidate built and filesystems checked:', compressed, flush=True)


if __name__ == '__main__':
    main()
