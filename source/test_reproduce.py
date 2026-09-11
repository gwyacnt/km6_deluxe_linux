#!/usr/bin/env python3
"""Check that restore failures are rejected before opening a destination disk."""
import io
import lzma
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import reproduce


class RestoreGuards(unittest.TestCase):
    def test_regular_file_is_not_a_disk(self):
        with tempfile.NamedTemporaryFile() as f:
            with self.assertRaisesRegex(RuntimeError, 'block device'):
                reproduce.validate_usb(Path(f.name), 1)

    def test_wrong_raw_size_never_opens_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'test.img.xz'
            image.write_bytes(lzma.compress(b'not the expected disk image'))
            with patch.object(reproduce, 'validate_usb') as validate:
                with self.assertRaisesRegex(RuntimeError, 'decompressed image size'):
                    reproduce.write_usb(image, Path('/dev/not-a-real-device'), 999)
                validate.assert_not_called()

    def test_corrupt_download_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as directory:
            entry = {'name': 'image.xz', 'size': 3, 'sha256': '0' * 64}
            with patch.object(reproduce.urllib.request, 'urlopen', return_value=io.BytesIO(b'bad')):
                with self.assertRaisesRegex(RuntimeError, 'size/hash mismatch'):
                    reproduce.fetch(Path(directory), 'test', entry)
            self.assertFalse((Path(directory) / 'image.xz').exists())


if __name__ == '__main__':
    unittest.main()
