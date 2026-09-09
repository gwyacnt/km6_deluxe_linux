#!/usr/bin/env python3
"""Check the early-boot mapper against valid and damaged candidate tables."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

binary, table = sys.argv[1:]
original = Path(table).read_bytes()
result = subprocess.run([binary, '--table-backup', table], capture_output=True, text=True, check=True)
assert result.stdout.splitlines() == [
    'km6-linuxboot 0 524288 linear /dev/mmcblk1 72830976',
    'km6-linuxroot 0 48787456 linear /dev/mmcblk1 73371648']
for offset, data in [(0, b'BAD!'), (20, b'\0' * 4),
                     (24 + 40 * 19 + 24, struct.pack('<Q', 0)),
                     (24 + 40 * 17 + 16, struct.pack('<Q', 1024))]:
    broken = bytearray(original)
    broken[offset:offset + len(data)] = data
    with tempfile.NamedTemporaryFile() as f:
        f.write(broken); f.flush()
        result = subprocess.run([binary, '--table-backup', f.name], capture_output=True)
        assert result.returncode != 0 and not result.stdout
print('PASS: exact mappings; malformed headers, checksum, overlap and data size rejected')
