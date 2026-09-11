import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from bootstrap_build import extract_sdk


class SdkExtractionTests(unittest.TestCase):
    def test_rejects_traversal_and_external_symlinks(self):
        for name, link in [('output/../../escape', None), ('output/escape', '/etc/passwd')]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                archive = root / 'sdk.tar'
                with tarfile.open(archive, 'w') as t:
                    info = tarfile.TarInfo(name)
                    if link:
                        info.type = tarfile.SYMTYPE
                        info.linkname = link
                        t.addfile(info)
                    else:
                        info.size = 1
                        t.addfile(info, io.BytesIO(b'x'))
                with self.assertRaises((ValueError, tarfile.FilterError)):
                    extract_sdk(archive, root / 'dest')
                self.assertFalse((root / 'escape').exists())

    def test_keeps_relative_tool_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with tarfile.open(root / 'sdk.tar', 'w') as t:
                file = tarfile.TarInfo('output/bin/tool')
                file.size = 1
                file.mode = 0o755
                t.addfile(file, io.BytesIO(b'x'))
                link = tarfile.TarInfo('output/bin/alias')
                link.type = tarfile.SYMTYPE
                link.linkname = 'tool'
                t.addfile(link)
            extract_sdk(root / 'sdk.tar', root / 'dest')
            self.assertEqual((root / 'dest/output/bin/alias').read_bytes(), b'x')
            self.assertTrue((root / 'dest/output/bin/tool').stat().st_mode & 0o100)


if __name__ == '__main__':
    unittest.main()
