#!/usr/bin/env python3
"""Build public installer metadata; device-specific originals are read at install time."""
import hashlib
import json
import os
from pathlib import Path

src = Path(__file__).resolve().parent
work = Path(os.environ.get('KM6_WORKDIR', src.parents[1] / 'build')).resolve() / 'output/dualboot'
spec = json.loads((src / 'stock-layout.json').read_text())
spec['candidate_files'] = {
    name: hashlib.sha256((work / 'layout-candidate' / name).read_bytes()).hexdigest()
    for name in ('mpt.bin', 'dtb-slot.bin', 'PARTITION.vbmeta')
}
# install_from_release.py validates board metadata and captures the actual
# device's footer/DTB slot hashes before calling install_layout.py.
(work / 'release-layout.json').write_text(json.dumps(spec, indent=2) + '\n')
print('Wrote public release-layout.json; no private backups or devices read.')
