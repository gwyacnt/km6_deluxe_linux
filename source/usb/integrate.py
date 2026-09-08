from pathlib import Path
import hashlib,subprocess,shutil,json,os
r=Path(os.environ.get('KM6_WORKDIR', Path(__file__).resolve().parents[2]/'archive')).resolve()/'output/debian-usb/autoload'
project=r.parents[2]
base=r.parent/'debian.img'
assert hashlib.file_digest(base.open('rb'),'sha256').hexdigest()=='d859c942bbf60275584e79929b7ab09a456af470256f3e7918ef94b845698af8'
fs=r/'rootfs-with-maxio.ext4';shutil.copy2(r.parent/'rootfs.ext4',fs)
module=project/'output/debian-ethernet/maxio/module/maxio.ko'
config=r/'km6-maxio.conf';config.write_text('# KM6 Ethernet PHY driver, built for Linux 6.18.49-meson64\nmaxio\n')
k='6.18.49-meson64';prefix=f'/usr/lib/modules/{k}'
files={f'{prefix}/extra/maxio.ko':module,'/etc/modules-load.d/km6-maxio.conf':config}
for n in ['modules.dep','modules.dep.bin','modules.alias','modules.alias.bin','modules.symbols','modules.symbols.bin','modules.softdep','modules.devname','modules.builtin.bin','modules.builtin.alias.bin']:
 files[f'{prefix}/{n}']=r/'staging/lib/modules'/k/n
cmds=[f'mkdir {prefix}/extra']
for dest,src in files.items():
 if dest.startswith(prefix+'/modules.'):
  cmds.append(f'rm {dest}')
 cmds += [f'write {src} {dest}',f'set_inode_field {dest} uid 0',f'set_inode_field {dest} gid 0',f'set_inode_field {dest} mode 0100644']
script=r/'debugfs-commands.txt';script.write_text('\n'.join(cmds)+'\n')
p=subprocess.run(['/usr/sbin/debugfs','-w','-f',str(script),str(fs)],capture_output=True,text=True)
(r/'debugfs.log').write_text(p.stdout+p.stderr)
assert p.returncode==0
verify=r/'verify';verify.mkdir(exist_ok=True)
for dest,src in files.items():
 out=verify/src.name
 subprocess.run(['/usr/sbin/debugfs','-R',f'dump {dest} {out}',str(fs)],check=True,capture_output=True)
 assert out.read_bytes()==src.read_bytes(),dest
check=subprocess.run(['/usr/sbin/e2fsck','-fn',str(fs)],capture_output=True,text=True)
(r/'filesystem-check.log').write_text(check.stdout+check.stderr)
assert check.returncode==0,check.stdout+check.stderr
out=r.parent/'debian-km6-network.img';shutil.copy2(base,out)
with out.open('r+b') as b,fs.open('rb') as a:
 b.seek(557056*512);shutil.copyfileobj(a,b)
# Verify unchanged MBR/boot partition and installed root filesystem.
with base.open('rb') as a,out.open('rb') as b:
 remain=557056*512
 while remain:
  size=min(remain,4*1024*1024);assert a.read(size)==b.read(size);remain-=size
 with fs.open('rb') as a:
  while c:=a.read(4*1024*1024):assert c==b.read(len(c))
manifest={'image':str(out),'sha256':hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),'size':out.stat().st_size,'module':hashlib.file_digest(module.open('rb'),'sha256').hexdigest(),'files':list(files),'filesystem_check_passed':True,'boot_partition_unchanged':True,'automatic_boot_test':'pending'}
(r/'integration.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
