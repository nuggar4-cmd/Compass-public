import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from compass.favorites import Favorites


class FavoritesTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory(prefix='compass-ü-'))
        self.path = Path(directory) / 'Compass test' / 'favorites.sqlite3'
        self.store = Favorites(self.path)

    def test_valid_favorites_are_idempotent_and_persist_across_instances(self):
        self.assertEqual(self.store.list_favorites(), {'ok': True, 'ids': []})
        self.assertFalse(self.path.parent.exists())
        for app_id in ('obs', 'obs', '7zip'):
            self.assertEqual(self.store.set_favorite(app_id, True), {'ok': True, 'saved': True})
        reopened = Favorites(self.path)
        self.assertEqual(reopened.list_favorites(), {'ok': True, 'ids': ['7zip', 'obs']})
        for _ in range(2):
            self.assertEqual(reopened.set_favorite('obs', False), {'ok': True, 'saved': False})
        self.assertEqual(self.store.list_favorites(), {'ok': True, 'ids': ['7zip']})

    def test_invalid_input_does_not_create_storage(self):
        for app_id, saved in (('https://www.7-zip.org/', True), ([], True), ('7zip', 1), ('7zip', 'true')):
            with self.subTest(app_id=app_id, saved=saved):
                self.assertEqual(self.store.set_favorite(app_id, saved), {'ok': False})
        self.assertFalse(self.path.parent.exists())

    def test_stale_catalog_ids_are_hidden(self):
        self.assertTrue(self.store.set_favorite('obs', True)['ok'])
        database = sqlite3.connect(self.path)
        self.addCleanup(database.close)
        with database:
            database.execute('INSERT INTO favorites VALUES (?)', ('removed-app',))
        self.assertEqual(self.store.list_favorites(), {'ok': True, 'ids': ['obs']})

    def test_damaged_store_returns_failure_without_overwriting_data(self):
        self.path.parent.mkdir()
        self.path.write_bytes(b'damaged')
        self.assertEqual(self.store.list_favorites(), {'ok': False})
        self.assertEqual(self.store.set_favorite('obs', True), {'ok': False})
        self.assertEqual(self.path.read_bytes(), b'damaged')

    def test_interrupted_first_save_can_be_retried(self):
        self.path.parent.mkdir()
        self.path.touch()
        self.assertEqual(self.store.list_favorites(), {'ok': True, 'ids': []})
        self.assertEqual(self.store.set_favorite('obs', True), {'ok': True, 'saved': True})
        self.assertEqual(Favorites(self.path).list_favorites(), {'ok': True, 'ids': ['obs']})
