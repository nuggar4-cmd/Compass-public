"""Store catalog IDs on this device without involving the renderer origin."""

from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys

from .catalog import BY_ID


def favorites_path():
    if sys.platform == 'win32':
        root = Path(os.environ.get('LOCALAPPDATA', ''))
        if not root.is_absolute():
            root = Path.home() / 'AppData' / 'Local'
        return root / 'Compass' / 'favorites.sqlite3'

    root = Path(os.environ.get('XDG_DATA_HOME', ''))
    if not root.is_absolute():
        root = Path.home() / '.local' / 'share'
    return root / 'io.github.nuggar4_cmd.Compass' / 'favorites.sqlite3'


class Favorites:
    def __init__(self, path=None):
        self._path = path if path is not None else favorites_path()

    def list_favorites(self):
        try:
            self._path.stat()
        except FileNotFoundError:
            return {'ok': True, 'ids': []}
        except OSError:
            return {'ok': False}

        try:
            # An existing database may need to roll back an interrupted write.
            uri = self._path.as_uri() + '?mode=rw'
            with closing(sqlite3.connect(uri, uri=True, timeout=0.5)) as database:
                schema = database.execute(
                    "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = 'favorites'"
                ).fetchone()
                if schema is None:
                    return {'ok': True, 'ids': []}
                rows = database.execute('SELECT app_id FROM favorites ORDER BY app_id')
                return {'ok': True, 'ids': [app_id for app_id, in rows if app_id in BY_ID]}
        except (OSError, sqlite3.Error):
            return {'ok': False}

    def set_favorite(self, app_id, saved):
        if type(app_id) is not str or app_id not in BY_ID or type(saved) is not bool:
            return {'ok': False}
        try:
            self._path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with closing(sqlite3.connect(self._path, timeout=0.5)) as database, database:
                database.execute('BEGIN IMMEDIATE')
                database.execute('CREATE TABLE IF NOT EXISTS favorites (app_id TEXT PRIMARY KEY NOT NULL)')
                if saved:
                    database.execute('INSERT OR IGNORE INTO favorites (app_id) VALUES (?)', (app_id,))
                else:
                    database.execute('DELETE FROM favorites WHERE app_id = ?', (app_id,))
        except (OSError, sqlite3.Error):
            return {'ok': False}
        return {'ok': True, 'saved': saved}
