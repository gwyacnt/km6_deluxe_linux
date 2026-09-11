#!/usr/bin/env python3
"""Build an experimental DTB and HDMI-routing module in the ignored workspace."""
from pathlib import Path
import hashlib, os, shutil, subprocess
src = Path(__file__).resolve().parent
root = src.parents[2]
workspace = Path(os.environ.get('KM6_WORKDIR', root / 'build')).resolve()
w = workspace / 'output/audio-investigation/playback-test'
w.mkdir(parents=True, exist_ok=True)
base = w.parent / 'baseline.dtb'
assert hashlib.sha256(base.read_bytes()).hexdigest() == '4367630e405611b1bc895ecb5a408723c714c0f956de363032fbf0971344aff7'
tools = workspace / 'output/tools/dtc-local/usr/bin'
for path, value in [('/soc/bus@fe000000/clock-controller@0', '6'),
                    ('/soc/bus@fe000000/clock-controller@8000', '3'),
                    ('/soc/bus@fe000000/reset-controller@2000', '9'),
                    ('/secure-monitor/power-controller', '10')]:
    assert subprocess.check_output([str(tools/'fdtget'), '-tx', str(base), path, 'phandle'], text=True).strip() == value
result = subprocess.run([str(tools/'dtc'), '-I', 'dtb', '-O', 'dts', str(base)], capture_output=True, text=True, check=True)
(w/'candidate.dts').write_text(result.stdout + '\n' + (src/'playback-test.dtsi').read_text())
result = subprocess.run([str(tools/'dtc'), '-I', 'dts', '-O', 'dtb', '-o', str(w/'km6-sc2-audio-test.dtb'), str(w/'candidate.dts')], capture_output=True, text=True)
(w/'dtc.log').write_text(result.stdout+result.stderr)
assert result.returncode == 0, result.stderr
for name in ('Makefile','sc2-tohdmitx.c','meson-codec-glue.h','sc2-card.c','axg-tdm.h','meson-card.h'):
    shutil.copy2(src/name, w/name)
h = workspace / 'output/debian-ethernet/maxio'
t = h/'toolchain/usr'
result = subprocess.run(['make','-C',str(h/'headers/usr/src/linux-headers-6.18.49-meson64'),
    'M='+str(w),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','CC=aarch64-linux-gnu-gcc-14','modules'],
    env={**os.environ,'PATH':str(t/'bin')+':'+os.environ['PATH'], 'LD_LIBRARY_PATH':str(t/'lib/x86_64-linux-gnu')},capture_output=True,text=True)
(w/'build.log').write_text(result.stdout+result.stderr)
print(result.stdout+result.stderr)
assert result.returncode == 0
for name in ('km6-sc2-audio-test.dtb','km6_sc2_tohdmitx.ko','km6_sc2_card.ko'):
    p=w/name; print(hashlib.sha256(p.read_bytes()).hexdigest(),name)
