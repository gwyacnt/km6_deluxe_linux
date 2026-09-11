#!/usr/bin/env python3
"""Build and verify regular-file layout candidates. Never access a block device."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib
from plan_storage import DEVICE_SIZE, parse_mpt, propose


def properties(blob):
    header = struct.unpack_from('>10I', blob)
    assert header[0] == 0xd00dfeed
    pos, strings = header[2], header[3]
    nodes, result = [], {}
    while True:
        token, = struct.unpack_from('>I', blob, pos)
        pos += 4
        if token == 1:
            end = blob.index(0, pos)
            nodes.append(blob[pos:end].decode())
            pos = (end + 4) & ~3
        elif token == 2:
            nodes.pop()
        elif token == 3:
            length, offset = struct.unpack_from('>II', blob, pos)
            pos += 8
            end = blob.index(0, strings + offset)
            name = blob[strings + offset:end].decode()
            result[('/' + '/'.join(nodes[1:]), name)] = blob[pos:pos + length]
            pos = (pos + length + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            return result
        else:
            raise ValueError('Invalid FDT token')


def run(*args):
    return subprocess.check_output([str(x) for x in args], stderr=subprocess.STDOUT)


def main():
    root = Path(__file__).resolve().parents[2]
    workspace = Path(os.environ.get('KM6_WORKDIR', root / 'build')).resolve()
    stock = workspace / 'output/extracted/stock'
    work = workspace / 'output/dualboot'
    out = work / 'layout-candidate'
    out.mkdir(parents=True, exist_ok=True)
    tool = work / 'avbtool.py'
    key = work / 'aosp-public-testkey-rsa2048.pem'
    for path, digest in [(tool, 'e5a664a38db623da00f080219bc0ee60a640a9dc4a872803616fae4938ac749b'),
                         (key, 'f1d5765a2bdfb92fb08aee021107c7ac1a7a3f590dafd853771c85375ef0fbd7')]:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
    spec = importlib.util.spec_from_file_location('avbtool', tool)
    avb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(avb)
    original_vbmeta = (stock / 'PARTITION.vbmeta').read_bytes()
    header = avb.AvbVBMetaHeader(original_vbmeta[:256])
    assert avb.verify_vbmeta_signature(header, original_vbmeta)
    pubkey = out / 'test-key.avbpubkey'
    run(sys.executable, tool, 'extract_public_key', '--key', key, '--output', pubkey)
    offset = 256 + header.authentication_data_block_size + header.public_key_offset
    assert original_vbmeta[offset:offset + header.public_key_size] == pubkey.read_bytes()

    original_dt = (stock / 'PARTITION._aml_dtb').read_bytes()
    multi = bytearray(zlib.decompress(original_dt, 31))
    assert struct.unpack_from('<3I', multi) == (0x5f4c4d41, 2, 3)
    fdtput = workspace / 'output/tools/dtc-local/usr/bin/fdtput'
    checks = []
    for i in range(3):
        offset, allocated = struct.unpack_from('<II', multi, 12 + i * 56 + 48)
        before = properties(multi[offset:offset + allocated])
        assert before[('/partitions', 'parts')] == struct.pack('>I', 15)
        assert before[('/partitions/data', 'size')] == b'\xff' * 8
        phandle = max(int.from_bytes(v, 'big') for (_, n), v in before.items() if n == 'phandle') + 1
        candidate = out / ('android-%d.dtb' % i)
        candidate.write_bytes(multi[offset:offset + allocated])
        run(fdtput, '-t', 'x', candidate, '/partitions/data', 'size', '8', '0')
        run(fdtput, '-t', 'x', candidate, '/partitions', 'parts', '11')
        for j, (name, high, low) in enumerate([('linuxboot', 0, 0x10000000), ('linuxroot', 0xffffffff, 0xffffffff)]):
            node = '/partitions/' + name
            run(fdtput, '-c', candidate, node)
            run(fdtput, '-t', 's', candidate, node, 'pname', name)
            run(fdtput, '-t', 'x', candidate, node, 'size', format(high, 'x'), format(low, 'x'))
            run(fdtput, '-t', 'x', candidate, node, 'mask', '0')
            run(fdtput, '-t', 'x', candidate, node, 'phandle', format(phandle + j, 'x'))
            run(fdtput, '-t', 'x', candidate, '/partitions', 'part-%d' % (15 + j), format(phandle + j, 'x'))
        data = candidate.read_bytes()
        after = properties(data)
        changed = {k for k in before if before[k] != after.get(k)}
        assert changed == {('/partitions', 'parts'), ('/partitions/data', 'size')}
        assert len(data) <= allocated
        multi[offset:offset + allocated] = data.ljust(allocated, b'\0')
        checks.append(dict(index=i, preserved_properties=len(before) - 2, new_properties=len(after) - len(before)))

    dt = out / 'PARTITION._aml_dtb'
    dt.write_bytes(gzip.compress(bytes(multi), mtime=0))
    run(sys.executable, tool, 'add_hash_footer', '--image', dt,
        '--partition_name', 'dt', '--partition_size', len(original_dt), '--algorithm', 'NONE',
        '--salt', '9cec985d0e4a8cff55c70673d07ae822472baa457dd2f1ab685ba12696f2896f')
    vbmeta = out / 'PARTITION.vbmeta'
    run(sys.executable, tool, 'make_vbmeta_image', '--output', vbmeta,
        '--algorithm', 'SHA256_RSA2048', '--key', key, '--rollback_index', header.rollback_index,
        '--flags', header.flags, '--rollback_index_location', header.rollback_index_location,
        '--include_descriptors_from_image', stock / 'PARTITION.vbmeta',
        '--include_descriptors_from_image', dt)
    new_vbmeta = vbmeta.read_bytes()
    new_header = avb.AvbVBMetaHeader(new_vbmeta[:256])
    assert avb.verify_vbmeta_signature(new_header, new_vbmeta)
    def descriptors(path):
        return avb.Avb()._parse_image(avb.ImageHandler(str(path), read_only=True))[2]
    old_desc = {d.encode() for d in descriptors(stock / 'PARTITION.vbmeta') if getattr(d, 'partition_name', '') != 'dt'}
    new_desc = {d.encode() for d in descriptors(vbmeta) if getattr(d, 'partition_name', '') != 'dt'}
    assert old_desc == new_desc
    dt_desc = [d for d in descriptors(vbmeta) if getattr(d, 'partition_name', '') == 'dt']
    assert len(dt_desc) == 1
    d = dt_desc[0]
    assert hashlib.sha256(d.salt + dt.read_bytes()[:d.image_size]).digest() == d.digest

    table = (Path(__file__).parent / 'stock-mpt.bin').read_bytes()
    assert hashlib.sha256(table).hexdigest() == 'caa42f20264cd105a94f4866fd036643f9f787bdea6aa42c7a23aa3226e0c68d'
    parts = propose(parse_mpt(table, DEVICE_SIZE), DEVICE_SIZE)
    entries = b''.join(struct.pack('<16sQQII', p['name'].encode(), p['size'], p['offset'], p['flags'], 0) for p in parts)
    checksum = sum(struct.unpack_from('<10I', entries)) * len(parts) & 0xffffffff
    mpt = (table[:16] + struct.pack('<II', len(parts), checksum) + entries).ljust(1304, b'\0')
    assert parse_mpt(mpt, DEVICE_SIZE) == parts
    (out / 'mpt.bin').write_bytes(mpt)
    # Two copies of this slot belong at reserved+0x400000 and +0x440000.
    slot = bytearray(dt.read_bytes().ljust(262144, b'\0'))
    struct.pack_into('<III', slot, len(slot) - 16, 0x00447e41, 1, 5)
    checksum = sum(struct.unpack('<65535I', slot[:-4])) & 0xffffffff
    struct.pack_into('<I', slot, len(slot) - 4, checksum)
    (out / 'dtb-slot.bin').write_bytes(slot)
    report = dict(status='OFFLINE CANDIDATE ONLY: not installed or hardware-tested',
                  dtb_checks=checks, android_avb_signature_verified=True,
                  unchanged_non_dt_avb_descriptors=len(old_desc), partitions=parts,
                  files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [dt, vbmeta, out / 'mpt.bin', out / 'dtb-slot.bin']})
    (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'partitions'}, indent=2))


if __name__ == '__main__':
    main()
