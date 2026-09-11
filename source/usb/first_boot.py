#!/usr/bin/env python3
"""Create fresh credentials on the physical console of a sanitized KM6 image."""
import getpass
from pathlib import Path
import subprocess

marker = Path('/var/lib/km6-first-boot.done')
if not marker.exists():
    print('\nKM6 Debian desktop setup\n')
    print('Set a new password for samer. This password also authorizes sudo.')
    while True:
        password = getpass.getpass('New password: ')
        confirmation = getpass.getpass('Repeat password: ')
        if password == confirmation and len(password) >= 8 and ':' not in password:
            break
        print('Use at least eight characters and enter the same password twice.')
    subprocess.run(['chpasswd'], input='samer:' + password + '\n', text=True, check=True)
    subprocess.run(['ssh-keygen', '-A'], check=True)
    marker.write_text('Fresh local credentials and SSH host keys created.\n')
    print('Setup complete. The desktop will start. Tailscale requires your own sign-in.')
