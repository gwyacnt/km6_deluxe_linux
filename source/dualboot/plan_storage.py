#!/usr/bin/env python3
"""Validate a saved KM6 MPT v1 table and print a proposed layout; never write it."""
import argparse
import json
import stat
import struct
from pathlib import Path

MIB = 1024 * 1024
DEVICE_SIZE = 62545461248


def parse_mpt(blob, device_size):
    if len(blob) < 1304 or blob[:16] != b'MPT\0' + b'01.00.00' + b'\0' * 4:
        raise ValueError('Expected a saved Amlogic MPT v1 table at file offset zero')
    count, checksum = struct.unpack_from('<II', blob, 16)
    if not 1 <= count <= 32:
        raise ValueError('Invalid partition count')
    # Vendor v1 repeats the first entry in its checksum calculation.
    calculated = sum(struct.unpack_from('<10I', blob, 24)) * count & 0xffffffff
    if calculated != checksum:
        raise ValueError('MPT v1 checksum mismatch')
    parts = []
    for i in range(count):
        name, size, offset, flags, padding = struct.unpack_from('<16sQQII', blob, 24 + 40 * i)
        name = name.split(b'\0', 1)[0].decode('ascii')
        if padding:
            raise ValueError('Unexpected nonzero entry padding')
        parts.append(dict(name=name, offset=offset, size=size, flags=flags))
    validate(parts, device_size)
    return parts


def validate(parts, device_size):
    names = set()
    end = 0
    for p in parts:
        if not p['name'] or p['name'] in names or len(p['name']) > 15:
            raise ValueError('Invalid or duplicate partition name')
        names.add(p['name'])
        if p['size'] <= 0 or p['offset'] % 512 or p['size'] % 512:
            raise ValueError('Invalid size or sector alignment')
        if p['offset'] < end:
            raise ValueError('Partition overlap or unsorted table')
        end = p['offset'] + p['size']
        if end > device_size:
            raise ValueError('Partition extends beyond device')


def propose(parts, device_size):
    if device_size != DEVICE_SIZE:
        raise ValueError('This proposal is limited to the tested 64 GB KM6')
    if len(parts) != 18 or parts[-1]['name'] != 'data' or parts[-1]['offset'] != 2786 * MIB:
        raise ValueError('Unexpected Android layout; refuse to guess')
    if parts[-1]['offset'] + parts[-1]['size'] != device_size:
        raise ValueError('Unexpected end of Android data partition')
    proposed = [dict(p) for p in parts]
    proposed[-1]['size'] = 32768 * MIB
    offset = proposed[-1]['offset'] + proposed[-1]['size'] + 8 * MIB
    proposed.append(dict(name='linuxboot', offset=offset, size=256 * MIB, flags=0))
    offset += (256 + 8) * MIB
    proposed.append(dict(name='linuxroot', offset=offset, size=device_size - offset, flags=0))
    validate(proposed, device_size)
    return proposed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path, help='Regular file containing saved reserved region or MPT table')
    args = parser.parse_args()
    with args.backup.open('rb') as f:
        import os
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise ValueError('Read a backup file, not a live block device')
        parts = parse_mpt(f.read(1304), DEVICE_SIZE)
    print(json.dumps(dict(status='proposal only; device tree and filesystem migration still required',
                         device_size=DEVICE_SIZE, current=parts,
                         proposed=propose(parts, DEVICE_SIZE)), indent=2))


if __name__ == '__main__':
    main()
