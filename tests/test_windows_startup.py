import unittest
from unittest.mock import MagicMock

from compass.windows import WEBVIEW2_CLIENT, WEBVIEW2_HELP, startup_issue


class WindowsStartupTests(unittest.TestCase):
    def setUp(self):
        self.registry = MagicMock()
        self.framework_key = (
            self.registry.HKEY_LOCAL_MACHINE,
            r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full',
        )
        self.user_key = (self.registry.HKEY_CURRENT_USER, rf'SOFTWARE\{WEBVIEW2_CLIENT}')
        self.machine_key = (
            self.registry.HKEY_LOCAL_MACHINE, rf'SOFTWARE\WOW6432Node\{WEBVIEW2_CLIENT}',
        )
        self.keys = {self.framework_key: {'Release': 533509}}

        def open_key(hive, path):
            if (hive, path) not in self.keys:
                raise FileNotFoundError(path)
            key = MagicMock()
            key.__enter__.return_value = self.keys[hive, path]
            return key

        def query_value(key, name):
            if name not in key:
                raise FileNotFoundError(name)
            return key[name], 0

        self.registry.OpenKey.side_effect = open_key
        self.registry.QueryValueEx.side_effect = query_value

    def test_accepts_per_machine_or_per_user_evergreen_runtime(self):
        for location in (self.machine_key, self.user_key):
            with self.subTest(location=location):
                self.keys[location] = {'pv': '142.0.3595.94'}
                self.assertIsNone(startup_issue(self.registry))
                del self.keys[location]

    def test_rejects_missing_or_invalid_runtime(self):
        self.assertEqual(startup_issue(self.registry), WEBVIEW2_HELP)
        for value in ('', '0.0.0.0', 'invalid', None):
            with self.subTest(value=value):
                self.keys[self.user_key] = {'pv': value}
                self.assertEqual(startup_issue(self.registry), WEBVIEW2_HELP)

    def test_reports_missing_framework_before_starting_webview(self):
        self.keys.pop(self.framework_key)
        self.keys[self.user_key] = {'pv': '142.0.3595.94'}
        self.assertIn('.NET Framework', startup_issue(self.registry))
