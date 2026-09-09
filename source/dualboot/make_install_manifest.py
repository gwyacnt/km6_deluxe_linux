#!/usr/bin/env python3
"""Record the tested device's original-region and candidate hashes, without writes to devices."""
import hashlib
import json
import os
from pathlib import Path
from plan_storage import DEVICE_SIZE, MIB

src = Path(__file__).resolve().parent
archive = Path(os.environ.get('KM6_WORKDIR', src.parents[1] / 'archive')).resolve()
backup = archive / 'private/dualboot-backup'
reserved = (backup / 'reserved.bin').read_bytes()
footer = (backup / 'android-data-tail.bin').read_bytes()
if len(reserved) != 64 * MIB or len(footer) != 16384:
    raise ValueError('Unexpected backup sizes')
stock_vbmeta = (archive / 'output/extracted/stock/PARTITION.vbmeta').read_bytes()
if len(stock_vbmeta) != 4096:
    raise ValueError('Unexpected stock vbmeta size')
regions = {}
for name, offset, data in [
    ('mpt', 36 * MIB, reserved[:1304]),
    ('dtb_a', 40 * MIB, reserved[4 * MIB:4 * MIB + 262144]),
    ('dtb_b', 40 * MIB + 262144, reserved[4 * MIB + 262144:4 * MIB + 524288]),
    ('vbmeta', 1168 * MIB, stock_vbmeta),
    ('data_tail', DEVICE_SIZE - 16384, footer),
]:
    regions[name] = dict(offset=offset, size=len(data), sha256=hashlib.sha256(data).hexdigest())
work = archive / 'output/dualboot'
files = {name: hashlib.sha256((work / 'layout-candidate' / name).read_bytes()).hexdigest()
         for name in ('mpt.bin', 'dtb-slot.bin', 'PARTITION.vbmeta')}
(work / 'install-manifest.json').write_text(json.dumps(dict(original_regions=regions, candidate_files=files), indent=2) + '\n')
print('Recorded five original regions and three candidate hashes; no device access.')
