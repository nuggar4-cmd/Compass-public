"""Reviewed, bundled catalog. Never accept a destination from the renderer."""
from dataclasses import dataclass
from urllib.parse import urlsplit

@dataclass(frozen=True)
class App:
    id: str
    name: str
    category: str
    description: str
    url: str
    host: str
    color: str
    glyph: str
    tags: tuple[str, ...]

CATALOG = (
    App('firefox', 'Firefox', 'Browsers', 'A fresh perspective on the web. Browse, explore and make it yours.', 'https://www.firefox.com/en-US/', 'www.firefox.com', '#ff9862', 'F', ('browser', 'web', 'mozilla')),
    App('vscode', 'Visual Studio Code', 'Development', 'A focused space for your next idea. Write code and build something new.', 'https://code.visualstudio.com/', 'code.visualstudio.com', '#63b4ff', '</>', ('editor', 'code', 'programming')),
    App('obs', 'OBS Studio', 'Creative', 'Bring your screen to life with video recording and live streaming.', 'https://obsproject.com/', 'obsproject.com', '#c7cbd8', '◉', ('video', 'streaming', 'recording')),
    App('7zip', '7-Zip', 'Utilities', 'Less space, more possibilities. Pack and unpack your files.', 'https://www.7-zip.org/', 'www.7-zip.org', '#9bdab4', '7z', ('archive', 'zip', 'files')),
)
BY_ID = {app.id: app for app in CATALOG}

def destination(app_id: str) -> str:
    if type(app_id) is not str or app_id not in BY_ID:
        raise ValueError('This application is not in the Compass catalog.')
    app = BY_ID[app_id]
    parsed = urlsplit(app.url)
    if (parsed.scheme != 'https' or parsed.netloc not in (app.host, f'{app.host}:443')
            or not parsed.path.startswith('/') or '#' in app.url or '\\' in app.url
            or any(not 33 <= ord(char) <= 126 for char in app.url)):
        raise ValueError('The catalog destination failed validation.')
    return app.url

def public_catalog() -> list[dict]:
    return [dict(id=app.id, name=app.name, category=app.category,
                 description=app.description, url=destination(app.id),
                 host=app.host, color=app.color, glyph=app.glyph,
                 tags=list(app.tags)) for app in CATALOG]
