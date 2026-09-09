#!/usr/bin/env python3
"""Exercise timed default and keyboard choices through a real pseudo-terminal."""
import os, pty, select, subprocess, sys, time
binary = sys.argv[1]
def run(keys, expected):
    master, slave = pty.openpty()
    p = subprocess.Popen([binary, '--timeout', '1'], stdin=slave, stdout=slave, stderr=slave)
    os.close(slave)
    output = b''
    end = time.monotonic() + 5
    sent = False
    while time.monotonic() < end:
        if select.select([master], [], [], .1)[0]:
            try: output += os.read(master, 8192)
            except OSError: break
        if not sent and b'Choose an operating system' in output:
            if keys: os.write(master, keys)
            sent = True
        if p.poll() is not None: break
    try:
        p.wait(timeout=max(.1, end - time.monotonic()))
    except subprocess.TimeoutExpired:
        p.kill(); p.wait(); raise AssertionError('menu did not exit')
    os.close(master)
    assert p.returncode == expected, (keys, p.returncode, output)
    assert b'Android TV (default)' in output and b'Debian Linux' in output
for keys, expected in [(b'',0),(b'\r',0),(b'\x1b[B\r',10),(b'\x1b[B\x1b[A\r',0),(b'2\r',10)]:
    run(keys, expected)
print('PASS: timed Android default, Enter, arrows, numeric Debian selection')
