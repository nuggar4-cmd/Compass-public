"""Small desktop bridge: explicit confirmation is enforced in Python."""
from threading import Lock
import webbrowser
from .catalog import BY_ID, destination, public_catalog

SUGGESTION_URL = 'https://github.com/nuggar4-cmd/Compass-public/issues/new?template=catalog-suggestion.yml'

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
        try:
            url = destination(app_id)
        except ValueError:
            return {
                'ok': False,
                'status': 'blocked',
                'message': 'Compass blocked this address because it did not pass the catalog check.',
            }
        app = BY_ID[app_id]
        notice = f'\n\n{app.notice}' if app.notice else ''
        return self._open_confirmed(
            url, 'Open official website?',
            f'{app.name}\n\n{url}{notice}\n\nThis opens your default browser. '
            'Review redirects and downloads before continuing.',
            f'Sent the official {app.name} link to your browser.',
        )

    def suggest_link(self):
        return self._open_confirmed(
            SUGGESTION_URL, 'Open the GitHub suggestion form?',
            f'{SUGGESTION_URL}\n\nThis opens your default browser. You need a GitHub account to submit. '
            'Suggestions are posted publicly for review.',
            'Opened the GitHub suggestion form.',
        )

    def _open_confirmed(self, url, title, message, success_message):
        if not self._opening.acquire(blocking=False):
            return {'ok': False, 'message': 'A link request is already open.'}
        try:
            if not self._confirm(title, message):
                return {'ok': False, 'message': 'Opening cancelled.'}
            if not self._opener(url):
                return {'ok': False, 'message': 'Could not open your browser. Please try again.'}
            return {'ok': True, 'message': success_message}
        except Exception:
            return {'ok': False, 'message': 'Could not open the website. Please try again.'}
        finally:
            self._opening.release()
