from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from compass.linux import START_URI, _load_assets


class LinuxAssetTests(unittest.TestCase):
    def setUp(self):
        self.ui = Path(self.enterContext(TemporaryDirectory()))
        for name in ('index.html', 'styles.css', 'catalog.js', 'app.js', 'compass-mark.png'):
            (self.ui / name).write_bytes(name.encode())

    def test_preloads_only_the_exact_renderer_addresses(self):
        assets = _load_assets(self.ui)
        (self.ui / 'app.js').write_bytes(b'replaced after load')

        self.assertEqual(assets, {
            START_URI: ('text/html; charset=utf-8', b'index.html'),
            'compass://ui/styles.css': ('text/css; charset=utf-8', b'styles.css'),
            'compass://ui/catalog.js': ('text/javascript; charset=utf-8', b'catalog.js'),
            'compass://ui/app.js': ('text/javascript; charset=utf-8', b'app.js'),
            'compass://ui/compass-mark.png': ('image/png', b'compass-mark.png'),
        })

    def test_rejects_missing_or_empty_script(self):
        script = self.ui / 'app.js'

        script.unlink()
        with self.assertRaisesRegex(OSError, 'Unavailable bundled Compass asset: app.js'):
            _load_assets(self.ui)

        script.touch()
        with self.assertRaisesRegex(OSError, 'Empty bundled Compass asset: app.js'):
            _load_assets(self.ui)
