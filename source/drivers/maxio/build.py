#!/usr/bin/env python3
"""Build into the ignored workspace using its prepared kernel headers/toolchain."""
import os
from pathlib import Path
import shutil
import subprocess

source = Path(__file__).resolve().parent
workspace = Path(os.environ.get('KM6_WORKDIR', source.parents[2] / 'build')).resolve()
work = workspace / 'output/debian-ethernet/maxio'
build = work / 'module-v2'
build.mkdir(parents=True, exist_ok=True)
for name in ('maxio.c', 'Makefile'):
    shutil.copy2(source / name, build / name)
toolchain = work / 'toolchain/usr'
env = dict(os.environ, PATH=str(toolchain / 'bin') + ':' + os.environ['PATH'],
           LD_LIBRARY_PATH=str(toolchain / 'lib/x86_64-linux-gnu'))
result = subprocess.run([
    'make', '-C', str(work / 'headers/usr/src/linux-headers-6.18.49-meson64'),
    'M=' + str(build), 'ARCH=arm64', 'CROSS_COMPILE=aarch64-linux-gnu-',
    'CC=aarch64-linux-gnu-gcc-14', 'modules',
], env=env, capture_output=True, text=True)
(build / 'build.log').write_text(result.stdout + result.stderr)
print(result.stdout + result.stderr, end='')
raise SystemExit(result.returncode)
