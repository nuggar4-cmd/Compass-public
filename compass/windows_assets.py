"""Serve the bundled Windows renderer assets on a private loopback address."""

from contextlib import contextmanager
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


ENTRY = '/index.html?desktop=1'
ASSETS = {
    ENTRY: ('index.html', 'text/html; charset=utf-8'),
    '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
    '/catalog.js': ('catalog.js', 'text/javascript; charset=utf-8'),
    '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
}


@contextmanager
def serve_windows_assets(ui_directory):
    root = ui_directory.resolve(strict=True)
    assets = {}
    for route, (name, media_type) in ASSETS.items():
        asset = root / name
        if asset.resolve(strict=True) != asset or not asset.is_file():
            raise OSError(f'Unavailable bundled Compass asset: {name}')
        assets[route] = (media_type, asset.read_bytes())

    class AssetHandler(BaseHTTPRequestHandler):
        timeout = 5

        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.headers.get_all('Host') != [authority]:
                self._respond(HTTPStatus.BAD_REQUEST)
                return
            asset = assets.get(self.path)
            if asset is None:
                self._respond(HTTPStatus.NOT_FOUND)
                return
            self._respond(HTTPStatus.OK, *asset)

        def _respond(self, status, media_type='text/plain; charset=utf-8', data=b''):
            self.send_response(status)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "frame-ancestors 'none'")
            self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Type', media_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            if data:
                self.wfile.write(data)

    with ThreadingHTTPServer(('127.0.0.1', 0), AssetHandler) as server:
        authority = f'127.0.0.1:{server.server_port}'
        thread = Thread(target=server.serve_forever, kwargs={'poll_interval': 0.1}, daemon=True)
        thread.start()
        try:
            yield f'http://{authority}{ENTRY}'
        finally:
            server.shutdown()
            thread.join()
