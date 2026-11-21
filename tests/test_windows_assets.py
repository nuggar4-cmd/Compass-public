from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlsplit

from compass.windows_assets import serve_windows_assets


class WindowsAssetTests(unittest.TestCase):
    def setUp(self):
        work = self.enterContext(TemporaryDirectory())
        self.ui = Path(work) / 'Compass # test %20' / '_internal' / 'ui'
        self.ui.mkdir(parents=True)
        self.assets = {
            'index.html': b'<!doctype html><title>Test</title>',
            'styles.css': b'body {}',
            'catalog.js': b'/* packaged catalog */',
            'app.js': b'/* packaged app */',
        }
        for name, contents in self.assets.items():
            (self.ui / name).write_bytes(contents)
        (self.ui / 'extra.txt').write_text('Not a renderer asset', encoding='utf-8')

    @staticmethod
    def request(endpoint, target, method='GET', headers=None):
        connection = HTTPConnection(endpoint.hostname, endpoint.port, timeout=2)
        try:
            connection.request(method, target, headers=headers or {})
            response = connection.getresponse()
            return response.status, response.headers, response.read()
        finally:
            connection.close()

    def test_reads_exact_assets_from_a_folder_with_hash_and_percent_signs(self):
        with serve_windows_assets(self.ui) as url:
            endpoint = urlsplit(url)
            self.assertEqual(endpoint.hostname, '127.0.0.1')
            self.assertEqual(endpoint.query, 'desktop=1')
            cases = (
                (f'{endpoint.path}?{endpoint.query}', 'index.html', 'text/html'),
                ('/styles.css', 'styles.css', 'text/css'),
                ('/catalog.js', 'catalog.js', 'text/javascript'),
                ('/app.js', 'app.js', 'text/javascript'),
            )
            for route, name, media_type in cases:
                with self.subTest(route=route):
                    status, headers, body = self.request(endpoint, route)
                    self.assertEqual(status, 200)
                    self.assertEqual(headers.get_content_type(), media_type)
                    self.assertEqual(headers['Cache-Control'], 'no-store')
                    self.assertEqual(headers['Content-Security-Policy'], "frame-ancestors 'none'")
                    self.assertEqual(body, self.assets[name])

    def test_unlisted_files_and_mismatched_host_do_not_return_assets(self):
        with serve_windows_assets(self.ui) as url:
            endpoint = urlsplit(url)
            for route in ('/', '/extra.txt', '/js_api/'):
                with self.subTest(route=route):
                    status, _, body = self.request(endpoint, route)
                    self.assertEqual((status, body), (404, b''))

            status, _, body = self.request(endpoint, '/styles.css', headers={'Host': 'localhost'})
            self.assertEqual((status, body), (400, b''))
            status, _, body = self.request(endpoint, '/styles.css', method='POST')
            self.assertGreaterEqual(status, 400)
            self.assertNotEqual(body, self.assets['styles.css'])

    def test_loopback_listener_ends_with_context(self):
        with serve_windows_assets(self.ui) as url:
            endpoint = urlsplit(url)
            self.assertEqual(self.request(endpoint, '/styles.css')[0], 200)

        with self.assertRaises((ConnectionRefusedError, TimeoutError)):
            self.request(endpoint, '/styles.css')
