"""Small desktop bridge: explicit confirmation is enforced in Python."""
from threading import Lock
import webbrowser
from .catalog import BY_ID, destination, public_catalog

class Bridge:
    def __init__(self, confirm, opener=None, *, version=None):
        self._confirm = confirm
        self._opener = opener or (lambda url: webbrowser.open(url, new=2))
        self._opening = Lock()
        self._version = version

    def app_info(self):
        return {'version': self._version}

    def catalog(self):
        return public_catalog()

    def open_official(self, app_id):
        if not self._opening.acquire(blocking=False):
            return {'ok': False, 'message': 'A link request is already open.'}
        try:
            url = destination(app_id)
            app = BY_ID[app_id]
            approved = self._confirm('Open official website?',
                f'{app.name}\n\n{url}\n\nThis opens your default browser. '
                'The website has its own privacy policy. Compass cannot guarantee '
                'the safety of third-party websites or downloads.')
            if not approved:
                return {'ok': False, 'message': 'Opening cancelled.'}
            if not self._opener(url):
                return {'ok': False, 'message': 'Could not open your browser. Please try again.'}
            return {'ok': True, 'message': f'Opened the official {app.name} website.'}
        except ValueError:
            return {'ok': False, 'message': 'This destination is not allowed.'}
        except Exception:
            return {'ok': False, 'message': 'Could not open the website. Please try again.'}
        finally:
            self._opening.release()
