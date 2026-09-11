#!/usr/bin/env python3
"""Build static AArch64 chooser and read-only MPT mapper with preserved tools."""
import os
from pathlib import Path
import struct
import subprocess

src = Path(__file__).resolve().parent
workspace = Path(os.environ.get('KM6_WORKDIR', src.parents[1] / 'build')).resolve()
work = workspace / 'output/dualboot'
toolchain = workspace / 'output/debian-ethernet/maxio/toolchain/usr'
deps = work / 'deps'
work.mkdir(parents=True, exist_ok=True)
env = {**os.environ, 'PATH': str(toolchain / 'bin') + ':' + os.environ['PATH'],
       'LD_LIBRARY_PATH': str(toolchain / 'lib/x86_64-linux-gnu')}
for name, source in [('km6-menu', 'menu.c'), ('km6-mpt-map', 'mpt-map.c')]:
    out = work / name
    subprocess.run([str(toolchain / 'bin/aarch64-linux-gnu-gcc-14'),
                    '-static', '-O2', '-Wall', '-Wextra', '-Werror',
                    '--sysroot=' + str(deps), '-isystem', str(deps / 'usr/aarch64-linux-gnu/include'),
                    '-B' + str(deps / 'usr/aarch64-linux-gnu/lib'),
                    '-L' + str(deps / 'usr/aarch64-linux-gnu/lib'), str(src / source), '-o', str(out)],
                   env=env, check=True)
    data = out.read_bytes()
    assert data[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', data, 18)[0] == 183
    phoff = struct.unpack_from('<Q', data, 32)[0]
    phsize, phnum = struct.unpack_from('<HH', data, 54)
    assert all(struct.unpack_from('<I', data, phoff + i * phsize)[0] != 3 for i in range(phnum))
    print('Static AArch64:', out)
