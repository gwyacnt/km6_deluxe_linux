#!/usr/bin/env python3
"""Check layout invariants against a local, private table backup."""
import sys
from pathlib import Path
from plan_storage import DEVICE_SIZE, MIB, parse_mpt, propose, validate

blob = Path(sys.argv[1]).read_bytes()[:1304]
parts = parse_mpt(blob, DEVICE_SIZE)
new = propose(parts, DEVICE_SIZE)
assert new[:-3] == parts[:-1], 'Android system partitions moved'
assert new[-3]['offset'] == parts[-1]['offset']
assert new[-3]['size'] == 32 * 1024 * MIB
assert new[-1]['offset'] + new[-1]['size'] == DEVICE_SIZE


def rejects(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return
    raise AssertionError('Invalid input was accepted')


bad = bytearray(blob)
bad[20] ^= 1
rejects(parse_mpt, bad, DEVICE_SIZE)
rejects(propose, parts, DEVICE_SIZE // 2)
overlap = [dict(p) for p in new]
overlap[-1]['offset'] = overlap[-2]['offset']
rejects(validate, overlap, DEVICE_SIZE)
oversize = [dict(p) for p in new]
oversize[-1]['size'] += 512
rejects(validate, oversize, DEVICE_SIZE)
print('PASS: checksum, geometry, preservation, alignment, overlap and device bounds')
