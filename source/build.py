#!/usr/bin/env python3
"""Rebuild maintained KM6 components using bootstrap_build.py's isolated inputs."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

source = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--workspace', type=Path, default=source.parent / 'build')
p.add_argument('--target', action='append', choices=['drivers', 'tools', 'layout', 'firmware', 'legacy-usb'])
a = p.parse_args()
w = a.workspace.resolve()
if not (w / 'prepared-inputs.json').is_file():
    p.error('Run source/bootstrap_build.py first.')
targets = a.target or ['drivers', 'tools', 'layout', 'firmware', 'legacy-usb']
env = {**os.environ, 'KM6_WORKDIR': str(w)}
recipes = {
    'drivers': ['drivers/maxio/build.py', 'drivers/sc2-audio/build.py'],
    'tools': ['dualboot/build_tools.py'],
    'layout': ['dualboot/build_layout.py', 'dualboot/make_install_manifest.py'],
    'firmware': ['firmware/build_modified.py'],
    'legacy-usb': ['drivers/maxio/build.py', 'usb/integrate.py'],
}
for target in targets:
    print('Building:', target, flush=True)
    for script in recipes[target]:
        subprocess.run([sys.executable, str(source / script)], env=env, check=True)
print('Build completed under', w, flush=True)
