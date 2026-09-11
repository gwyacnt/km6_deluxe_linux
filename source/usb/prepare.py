from pathlib import Path
import struct,zlib,subprocess,hashlib,json,os
r=Path(os.environ.get('KM6_WORKDIR', Path(__file__).resolve().parents[2]/'build')).resolve()/'output/debian-usb';o=r/'boot-original';p=r/'boot-prepared';p.mkdir(exist_ok=True)
def pack(n,txt,template):
 b=template.read_bytes();h=list(struct.unpack('>7I4B32s',b[:64]));t=txt.encode();data=struct.pack('>II',len(t),0)+t
 h[1]=0;h[3]=len(data);h[6]=zlib.crc32(data);h[1]=zlib.crc32(struct.pack('>7I4B32s',*h));out=struct.pack('>7I4B32s',*h)+data
 test=bytearray(out[:64]);test[4:8]=bytes(4);assert zlib.crc32(test)==h[1] and zlib.crc32(out[64:])==h[6]
 (p/n).write_bytes(out);(p/(n+'.src')).write_text(txt)
entry='''# KM6 USB-only Debian test. Uses source; no persistent environment changes.
usb start
setenv devtype usb
setenv devnum 0
setenv distro_bootpart 1
setenv cmd_read "fatload usb 0:1"
setenv loadaddr 0x08000000
setenv box s905x4_generic_gigabit
if fatload usb 0:1 ${loadaddr} bootscript; then
fatwrite usb 0:1 ${loadaddr} DEBENTRY.BIN 40
source ${loadaddr}
fi
'''
for n in ['aml_autoscript','cfgload','s905_autoscript']:pack(n,entry,o/'aml_autoscript')
b=(o/'bootscript').read_bytes()[72:].decode().replace('autoscr ${loadaddr}','source ${loadaddr}')
b=b.replace('run cmd_do_boot;','fatwrite usb 0:1 ${os_addr} DEBKERN.BIN 40\nfatwrite usb 0:1 ${dtb_addr} DEBDTB.BIN 40\nrun cmd_do_boot;')
pack('bootscript',b,o/'bootscript')
c=(o/'boot.config').read_text().replace('#box=s905x4_generic_gigabit','box=s905x4_generic_gigabit')
(p/'boot.config').write_text(c)
mtools=r.parent/'tools/usb-local/usr/bin/mcopy'
for n in ['aml_autoscript','cfgload','s905_autoscript','bootscript','boot.config']:
 subprocess.run([str(mtools),'-o','-i',str(r/'debian.img')+'@@16777216',str(p/n),'::'+n],check=True)
(r/'SHA256SUMS').write_text(''.join(hashlib.file_digest(f.open('rb'),'sha256').hexdigest()+'  '+str(f.relative_to(r))+'\n' for f in [r/'debian.img',*sorted(p.iterdir())]))
print('Prepared Debian image with source-compatible USB entry and generic S905X4/Gigabit config.')
