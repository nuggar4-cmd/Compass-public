from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import main


class MainStartupTests(unittest.TestCase):
    def test_rejects_missing_or_damaged_version_before_launch(self):
        for version in (None, b'invalid', b'\xff\x00'):
            with self.subTest(version=version), TemporaryDirectory() as temporary:
                base = Path(temporary)
                if version is not None:
                    (base / 'VERSION').write_bytes(version)
                with (
                    patch.object(sys, '_MEIPASS', temporary, create=True),
                    patch.object(sys, 'platform', 'linux'),
                    patch('compass.linux.run') as run,
                    patch('compass.linux.show_startup_error') as notice,
                    self.assertRaisesRegex(SystemExit, 'files are missing or damaged'),
                ):
                    main.main()
                run.assert_not_called()
                notice.assert_called_once()

    def test_webview_start_error_gets_native_guidance(self):
        class WebViewException(Exception):
            pass

        winreg = SimpleNamespace()
        webview = SimpleNamespace(WebViewException=WebViewException)
        with (
            patch.object(sys, 'platform', 'win32'),
            patch.dict(sys.modules, {'winreg': winreg, 'webview': webview}),
            patch.object(main, 'startup_issue', return_value=None),
            patch.object(main, 'start_webview', side_effect=WebViewException),
            patch.object(main, 'show_startup_error') as notice,
            self.assertRaisesRegex(SystemExit, 'could not start its Windows interface'),
        ):
            main.main()
        notice.assert_called_once()
        self.assertIn('WebView2', notice.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
