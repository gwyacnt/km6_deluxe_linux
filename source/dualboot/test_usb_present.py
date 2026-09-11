#!/usr/bin/env python3
"""Exercise USB selection without touching USB devices or boot settings."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('usb-present')


class UsbDetection(unittest.TestCase):
    def test_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def detect():
                return subprocess.run(['sh', str(SCRIPT), str(root)], capture_output=True, text=True)

            self.assertEqual(detect().returncode, 1)
            for name in ['usb1', 'usb2', '1-0:1.0']:
                (root / name).mkdir()
                (root / name / 'idVendor').write_text('1d6b\n')
            self.assertEqual(detect().returncode, 1, 'Root hubs/interfaces must not select Debian')
            # No storage driver, filesystem or device class is required.
            for name, vendor in [('1-1', '046d'), ('2-3', '1234'), ('1-2.4', 'abcd')]:
                (root / name).mkdir()
                (root / name / 'idVendor').write_text(vendor + '\n')
                result = detect()
                self.assertEqual((result.returncode, result.stdout.strip()), (0, name))
                (root / name / 'idVendor').unlink()
                (root / name).rmdir()
            self.assertEqual(detect().returncode, 1)


if __name__ == '__main__':
    unittest.main()
