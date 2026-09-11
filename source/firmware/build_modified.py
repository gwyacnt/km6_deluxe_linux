#!/usr/bin/env python3
"""Build the KM6 autoscr->source candidate using only regular project files.

Preserves the entire container except the installed bootloader's default command,
its BL33 SHA-256 trailer, the partition SHA-1 record, and container CRC32.
This performs no flashing and does not establish successful hardware boot.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import zlib

ROOT = Path(os.environ.get('KM6_WORKDIR', Path(__file__).resolve().parents[2] / 'build')).resolve()
STOCK = ROOT / 'Stock/KM6-QTT2.200903.001-V4.20201026.img'
EXPECTED = 'e9c5b585374b0d2cd32c471eb171ed7fce46d5f2f689248d79ba281bc8cc1a44'
OUT = ROOT / 'output'
(OUT / 'analysis').mkdir(parents=True, exist_ok=True)

def safe_regular(path, existing=True):
    assert path.resolve().is_relative_to(ROOT)
    assert not path.is_symlink(), path
    if existing or path.exists():
        assert stat.S_ISREG(path.stat().st_mode), path

def digest_file(path):
    safe_regular(path)
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def items(f):
    f.seek(0)
    header = f.read(64)
    crc, version, magic, size, align, count = struct.unpack_from('<IIIQII', header)
    assert version == 2 and magic == 0x27b51956 and align == 8 and count == 23
    result = []
    for i in range(count):
        d = f.read(576)
        ident, typ, cur, off, length = struct.unpack_from('<IIQQQ', d)
        assert ident == i and off + length <= size
        main, sub = [x.split(b'\0')[0].decode() for x in (d[32:288], d[288:544])]
        result.append(dict(id=i, main=main, sub=sub, offset=off, size=length))
    return result

def patch_bootloader(original):
    b = bytearray(original)
    assert len(b) == 3248128
    # Original SC2 manifest and standard FIP ToC establish the BL33 extent.
    assert b[0x3f880:0x3f884] == b'DEVF'
    fip_base, fip_size = struct.unpack_from('<II', b, 0x3f884)
    assert (fip_base, fip_size) == (0xa4000, 0x275000)
    assert struct.unpack_from('<I', b, fip_base + 16)[0] == 0xaa640001
    uuid, off, size, flags = struct.unpack_from('<16sQQQ', b, fip_base + 32 + 4*40)
    assert uuid.hex() == 'd6d0eea7fcead54b97829934f234b6e4'
    start, end = fip_base + off, fip_base + off + size
    assert (start, end) == (0x198000, 0x318260)
    assert hashlib.sha256(b[start:end-32]).digest() == b[end-32:end]
    # Preserve the stock certificate template, including its fixed header/tail.
    assert not any(b[fip_base+0x47e0:fip_base+0x4ee0])
    assert not any(b[fip_base+0x4f00:fip_base+0x5330])
    old = b'then autoscr ${loadaddr}; fi;'
    new = b'then source  ${loadaddr}; fi;'
    assert len(old) == len(new) and b.count(old) == 1
    location = b.index(old)
    assert location == 0x28d379 and start < location < end-32
    assert b.count(b'\0autoscr\0') == 0 and b.count(b'\0source\0') == 1
    b[location:location+len(old)] = new
    b[end-32:end] = hashlib.sha256(b[start:end-32]).digest()
    assert b[:start] == original[:start] and b[end:] == original[end:]
    return bytes(b), dict(command_offset=location+5, bl33_start=start, bl33_end=end,
                         bl33_sha256_offset=end-32, old=old.decode(), new=new.decode())

def build():
    assert digest_file(STOCK) == EXPECTED, 'Wrong stock image; refusing to build'
    target = OUT / 'modified-km6.img'
    temp = OUT / 'modified-km6.img.tmp'
    for path in (target, temp): safe_regular(path, existing=False)
    assert not temp.exists(), 'Remove an interrupted regular-file temporary output manually'
    with STOCK.open('rb') as f:
        rows = items(f)
        boot = next(x for x in rows if (x['main'],x['sub'])==('PARTITION','bootloader'))
        verify = next(x for x in rows if (x['main'],x['sub'])==('VERIFY','bootloader'))
        f.seek(boot['offset']); original = f.read(boot['size'])
        modified, details = patch_bootloader(original)
        record = b'sha1sum ' + hashlib.sha1(modified).hexdigest().encode()
        assert len(record) == verify['size'] == 48
        f.seek(0)
        with temp.open('xb') as w:
            while chunk := f.read(8*1024*1024): w.write(chunk)
    with temp.open('r+b') as w:
        w.seek(boot['offset']); w.write(modified)
        w.seek(verify['offset']); w.write(record)
        w.seek(4); crc = 0
        while chunk := w.read(8*1024*1024): crc = zlib.crc32(chunk,crc)
        w.seek(0); w.write(struct.pack('<I',crc ^ 0xffffffff))
    # Verify actual byte differences over the complete container, including super.
    allowed = [(0,4), (boot['offset']+details['command_offset'],boot['offset']+details['command_offset']+7),
               (boot['offset']+details['bl33_sha256_offset'],boot['offset']+details['bl33_sha256_offset']+32),
               (verify['offset']+8,verify['offset']+48)]
    ranges = []; count = 0
    with STOCK.open('rb') as a, temp.open('rb') as b:
        offset = 0
        while x := a.read(8*1024*1024):
            y = b.read(len(x)); assert len(x)==len(y)
            if x != y:
                for i,(v,w) in enumerate(zip(x,y)):
                    if v != w:
                        pos=offset+i; assert any(lo<=pos<hi for lo,hi in allowed), hex(pos)
                        count += 1
                        if ranges and ranges[-1][1]==pos: ranges[-1][1]=pos+1
                        else: ranges.append([pos,pos+1])
            offset += len(x)
        assert b.read(1)==b''
    checks=[]
    with temp.open('rb') as f:
        assert items(f)==rows
        for row in rows:
            f.seek(row['offset']); h=hashlib.sha1(); left=row['size']
            while left:
                chunk=f.read(min(left,8*1024*1024)); assert chunk
                h.update(chunk); left-=len(chunk)
            checks.append(dict(**row,sha1=h.hexdigest()))
        for row in checks:
            if row['main']=='VERIFY':
                f.seek(row['offset']); text=f.read(row['size'])
                p=next(p for p in checks if p['main']=='PARTITION' and p['sub']==row['sub'])
                assert text==b'sha1sum '+p['sha1'].encode()
        f.seek(boot['offset']); patched=f.read(boot['size'])
        assert patched==modified
        start,end=details['bl33_start'],details['bl33_end']
        assert hashlib.sha256(patched[start:end-32]).digest()==patched[end-32:end]
        f.seek(0); stored=struct.unpack('<I',f.read(4))[0];crc=0
        while chunk:=f.read(8*1024*1024):crc=zlib.crc32(chunk,crc)
        assert stored==crc^0xffffffff
    assert digest_file(STOCK)==EXPECTED
    os.replace(temp,target)
    result=dict(status='Rebuilt stock USB-loader patch; offline integrity verified; compare with the released modified firmware before flashing',
                source=str(STOCK.relative_to(ROOT)),source_sha256=EXPECTED,
                output=str(target.relative_to(ROOT)),output_sha256=digest_file(target),
                size=target.stat().st_size,changed_bytes=count,changed_ranges=ranges,
                allowed_ranges=allowed,patch=details,items=checks)
    report=OUT/'analysis/build-validation.json';safe_regular(report,existing=False)
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('items',)},indent=2))

if __name__=='__main__': build()
