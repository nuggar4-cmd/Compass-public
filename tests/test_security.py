import dataclasses
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from compass import catalog
from compass.bridge import Bridge

class SecurityTests(unittest.TestCase):
    def test_destinations_and_preview_catalog(self):
        self.assertEqual(len(catalog.BY_ID), len(catalog.CATALOG))
        for app in catalog.CATALOG:
            self.assertEqual(catalog.destination(app.id), app.url)
            self.assertTrue(app.url.startswith('https://' + app.host + '/'))
        source = (Path(__file__).resolve().parents[1] / 'ui' / 'catalog.js').read_text()
        self.assertEqual(json.loads(source.split('window.COMPASS_CATALOG = ', 1)[1].rstrip(';\n')), catalog.public_catalog())

    def test_untrusted_ids(self):
        for value in [None, [], {}, 1, True, '', 'FIREFOX', '../firefox', 'https://evil.test', 'javascript:alert(1)', 'firefox\n']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                catalog.destination(value)

    def test_unsafe_catalog_urls(self):
        app = catalog.BY_ID['firefox']
        for url in [
            'http://www.firefox.com/', 'https://www.firefox.com.evil.test/',
            'https://www.firefox.com@evil.test/', 'https://user@www.firefox.com/',
            'https://www.firefox.com:8443/', 'https://www.firefox.com/#',
            'https://www.firefox.com/\n', 'https://www.firefox.com/\\app',
            'https://www.firefox.com/\u202eapp', 'file:///etc/passwd', 'javascript:alert(1)',
        ]:
            with self.subTest(url=url), patch.dict(catalog.BY_ID, {'firefox': dataclasses.replace(app, url=url)}):
                with self.assertRaises(ValueError):
                    catalog.destination('firefox')

    def test_confirm_before_open(self):
        opened, messages = [], []
        def confirm(title, message):
            messages.append(message)
            return True
        result = Bridge(confirm, lambda url: opened.append(url) or True).open_official('firefox')
        self.assertTrue(result['ok'])
        self.assertEqual(opened, [catalog.destination('firefox')])
        self.assertIn(opened[0], messages[0])

    def test_cancel(self):
        opened = []
        self.assertFalse(Bridge(lambda *_: False, lambda url: opened.append(url)).open_official('obs')['ok'])
        self.assertEqual(opened, [])

    def test_unknown_id_never_opens(self):
        calls = []
        bridge = Bridge(lambda *_: calls.append('confirm'), lambda _: calls.append('open'))
        for value in ['https://evil.test', {}, None, 'invalid']:
            self.assertFalse(bridge.open_official(value)['ok'])
        self.assertEqual(calls, [])

    def test_browser_failure(self):
        self.assertFalse(Bridge(lambda *_: True, lambda _: False).open_official('obs')['ok'])

    def test_exceptions_release_lock(self):
        def fail(_):
            raise RuntimeError('sensitive details')
        bridge = Bridge(lambda *_: True, fail)
        result = bridge.open_official('obs')
        self.assertFalse(result['ok'])
        self.assertNotIn('sensitive', result['message'])
        self.assertTrue(bridge._opening.acquire(blocking=False))
        bridge._opening.release()

    def test_concurrent_request(self):
        bridge = Bridge(lambda *_: True, lambda _: True)
        bridge._opening.acquire()
        try:
            self.assertFalse(bridge.open_official('obs')['ok'])
        finally:
            bridge._opening.release()

if __name__ == '__main__':
    unittest.main()
