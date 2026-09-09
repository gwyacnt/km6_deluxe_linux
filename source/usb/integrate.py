#!/usr/bin/env python3
"""Build a regular-file USB image; never write directly to a block device."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

source = Path(__file__).resolve().parent
workspace = Path(os.environ.get('KM6_WORKDIR', source.parents[1] / 'archive')).resolve()
usb = workspace / 'output/debian-usb'
work = usb / 'autoload-v2'
work.mkdir(parents=True, exist_ok=True)
kernel = '6.18.49-meson64'
base = usb / 'debian.img'
module = workspace / 'output/debian-ethernet/maxio/module-v2/km6_maxio.ko'

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

assert base.is_file() and not base.is_symlink()
assert digest(base) == 'd859c942bbf60275584e79929b7ab09a456af470256f3e7918ef94b845698af8'
assert subprocess.check_output(['/usr/sbin/modinfo', '-F', 'name', str(module)], text=True).strip() == 'km6_maxio'
assert subprocess.check_output(['/usr/sbin/modinfo', '-F', 'vermagic', str(module)], text=True).startswith(kernel + ' ')

# Preserve the original complete module tree and rebuild all indexes.
staging = work / 'staging'
modules = staging / 'lib/modules' / kernel
modules.parent.mkdir(parents=True, exist_ok=True)
if modules.exists():
    shutil.rmtree(modules)
result = subprocess.run(['/usr/sbin/debugfs', '-R',
    f'rdump /usr/lib/modules/{kernel} {modules.parent}', str(usb / 'rootfs.ext4')],
    capture_output=True, text=True, check=True)
(work / 'module-extraction.log').write_text(result.stdout + result.stderr)
assert (modules / 'modules.builtin').is_file()
assert 'kernel/drivers/net/phy/maxio.ko' in (modules / 'modules.builtin').read_text()
assert 'km6_maxio' not in (modules / 'modules.builtin').read_text()
(modules / 'extra').mkdir(exist_ok=True)
shutil.copy2(module, modules / 'extra/km6_maxio.ko')
subprocess.run(['/usr/sbin/depmod', '-b', str(staging), kernel], check=True)
lookup = subprocess.check_output(['/usr/sbin/modprobe', '-d', str(staging), '-S', kernel,
    '--show-depends', 'km6_maxio'], text=True)
assert 'extra/km6_maxio.ko' in lookup

fs = work / 'rootfs.ext4'
shutil.copy2(usb / 'rootfs.ext4', fs)
prefix = f'/usr/lib/modules/{kernel}'
files = {f'{prefix}/extra/km6_maxio.ko': module}
for path in sorted((source / 'rootfs').rglob('*')):
    if path.is_file():
        files['/' + str(path.relative_to(source / 'rootfs'))] = path
for path in modules.glob('modules.*'):
    if path.name not in ('modules.builtin', 'modules.builtin.modinfo', 'modules.order'):
        files[f'{prefix}/{path.name}'] = path

# debugfs operates only on this disposable regular filesystem image.
# It may return success on a failed command, so every result is checked below.
commands = []
created = set()
def exists_in_base(path):
    result = subprocess.run(['/usr/sbin/debugfs', '-R', f'stat {path}',
                             str(usb / 'rootfs.ext4')], capture_output=True, text=True, check=True)
    return 'Inode:' in result.stdout

for dest, src in files.items():
    for parent in reversed(Path(dest).parents):
        if str(parent) != '/' and str(parent) not in created:
            if not exists_in_base(parent):
                commands.append(f'mkdir {parent}')
            created.add(str(parent))
    if exists_in_base(dest):
        commands.append(f'rm {dest}')
    commands += [f'write {src} {dest}',
                 f'set_inode_field {dest} uid 0', f'set_inode_field {dest} gid 0',
                 f'set_inode_field {dest} mode 0100644']
link = '/etc/systemd/system/multi-user.target.wants/km6-network-report.service'
commands.append(f'symlink {link} /etc/systemd/system/km6-network-report.service')
command_file = work / 'debugfs-commands.txt'
command_file.write_text('\n'.join(commands) + '\n')
result = subprocess.run(['/usr/sbin/debugfs', '-w', '-f', str(command_file), str(fs)],
                        capture_output=True, text=True, check=True)
(work / 'debugfs.log').write_text(result.stdout + result.stderr)
verify = work / 'verify'
verify.mkdir(exist_ok=True)
for dest, src in files.items():
    dumped = verify / dest.replace('/', '_')
    subprocess.run(['/usr/sbin/debugfs', '-R', f'dump {dest} {dumped}', str(fs)],
                   capture_output=True, check=True)
    assert dumped.read_bytes() == src.read_bytes(), dest
link_info = subprocess.check_output(['/usr/sbin/debugfs', '-R', f'stat {link}', str(fs)], text=True)
assert 'Type: symlink' in link_info and '/etc/systemd/system/km6-network-report.service' in link_info
check = subprocess.run(['/usr/sbin/e2fsck', '-fn', str(fs)], capture_output=True, text=True)
(work / 'filesystem-check.log').write_text(check.stdout + check.stderr)
assert check.returncode == 0, check.stdout + check.stderr

out = work / 'debian-km6-network-v2.img'
shutil.copy2(base, out)
root_offset = 557056 * 512
with out.open('r+b') as target, fs.open('rb') as stream:
    target.seek(root_offset)
    shutil.copyfileobj(stream, target)
# An optional report helper is visible on FAT; the service uses the rootfs copy.
mcopy = workspace / 'output/tools/usb-local/usr/bin/mcopy'
helper = source / 'rootfs/usr/local/sbin/km6-network-report'
subprocess.run([str(mcopy), '-o', '-i', str(out) + '@@16777216',
                str(helper), '::km6-network-report.sh'], check=True)
extracted = verify / 'km6-network-report.sh'
subprocess.run([str(mcopy), '-o', '-i', str(out) + '@@16777216',
                '::km6-network-report.sh', str(extracted)], check=True)
assert extracted.read_bytes() == helper.read_bytes()
with out.open('rb') as target, fs.open('rb') as stream:
    target.seek(root_offset)
    while data := stream.read(4 * 1024 * 1024):
        assert target.read(len(data)) == data
with out.open('rb') as target, base.open('rb') as stream:
    assert target.read(16777216) == stream.read(16777216)
manifest = {'image': str(out), 'sha256': digest(out), 'size': out.stat().st_size,
            'module_sha256': digest(module), 'module_name': 'km6_maxio',
            'files': {dest: digest(src) for dest, src in files.items()},
            'filesystem_check_passed': True, 'automatic_boot_test': 'pending'}
(work / 'integration.json').write_text(json.dumps(manifest, indent=2) + '\n')
(work / 'SHA256SUMS').write_text(manifest['sha256'] + '  ' + out.name + '\n')
print(json.dumps({key: value for key, value in manifest.items() if key != 'files'}, indent=2))
