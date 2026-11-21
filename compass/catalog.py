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
    notice: str | None = None

CATALOG = (
    App('firefox', 'Firefox', 'Browsers', 'A fresh perspective on the web. Browse, explore and make it yours.', 'https://www.firefox.com/en-US/', 'www.firefox.com', '#ff9862', 'F', ('browser', 'web', 'mozilla')),
    App('vscode', 'Visual Studio Code', 'Development', 'A focused space for your next idea. Write code and build something new.', 'https://code.visualstudio.com/', 'code.visualstudio.com', '#63b4ff', '</>', ('editor', 'code', 'programming')),
    App('obs', 'OBS Studio', 'Creative', 'Bring your screen to life with video recording and live streaming.', 'https://obsproject.com/', 'obsproject.com', '#c7cbd8', '◉', ('video', 'streaming', 'recording')),
    App('7zip', '7-Zip', 'Utilities', 'Less space, more possibilities. Pack and unpack your files.', 'https://www.7-zip.org/', 'www.7-zip.org', '#9bdab4', '7z', ('archive', 'zip', 'files')),
    App(
        id='vlc', name='VLC media player', category='Media',
        description='Play video and audio files, discs, and network streams.',
        url='https://www.videolan.org/vlc/', host='www.videolan.org',
        color='#f6ad68', glyph='V', tags=('player', 'video', 'audio', 'videolan'),
    ),
    App(
        id='gimp', name='GIMP', category='Creative',
        description='Retouch photos, edit layered images, and create graphics.',
        url='https://www.gimp.org/downloads/', host='www.gimp.org',
        color='#d2b2a3', glyph='G', tags=('photo', 'image', 'graphics', 'layers'),
    ),
    App(
        id='audacity', name='Audacity', category='Creative',
        description='Edit sound, clean up audio, and mix multiple tracks.',
        url='https://www.audacityteam.org/download/', host='www.audacityteam.org',
        color='#b5a5ff', glyph='A', tags=('audio', 'sound', 'podcast', 'editor'),
    ),
    App(
        id='libreoffice', name='LibreOffice', category='Productivity',
        description='Create and edit documents, spreadsheets, and presentations.',
        url='https://www.libreoffice.org/download/', host='www.libreoffice.org',
        color='#a3df9e', glyph='L', tags=('office', 'documents', 'spreadsheet', 'presentation'),
    ),
    App(
        id='keepassxc', name='KeePassXC', category='Utilities',
        description='Store and organize passwords in an encrypted database on your device.',
        url='https://keepassxc.org/download/', host='keepassxc.org',
        color='#a3e2b8', glyph='K', tags=('password', 'vault', 'credentials', 'offline'),
    ),
    App(
        id='thunderbird', name='Thunderbird', category='Productivity',
        description='Manage email accounts, contacts, and calendars in one desktop client.',
        url='https://www.thunderbird.net/en-US/thunderbird/all/', host='www.thunderbird.net',
        color='#8cccff', glyph='T', tags=('email', 'mail', 'calendar', 'contacts'),
    ),
    App(
        id='git', name='Git', category='Development',
        description='Track file changes, branch projects, and collaborate through version control.',
        url='https://git-scm.com/install/', host='git-scm.com',
        color='#ff9e88', glyph='Gi', tags=('version control', 'repository', 'code', 'terminal'),
    ),
    App(
        id='notepad-plus-plus', name='Notepad++', category='Development',
        description='Edit text and source code in a tabbed Windows editor.',
        url='https://notepad-plus-plus.org/downloads/', host='notepad-plus-plus.org',
        color='#bde69d', glyph='N+', tags=('text', 'code', 'editor', 'windows'),
    ),
    App(
        id='brave', name='Brave', category='Browsers',
        description='Browse the web with built-in ad and tracker blocking.',
        url='https://brave.com/download/', host='brave.com',
        color='#ff9c7d', glyph='B', tags=('browser', 'web', 'privacy', 'chromium'),
    ),
    App(
        id='vivaldi', name='Vivaldi', category='Browsers',
        description='Browse the web with customizable tabs, shortcuts, and layouts.',
        url='https://vivaldi.com/download/', host='vivaldi.com',
        color='#f499a7', glyph='Vi', tags=('browser', 'web', 'tabs', 'customization'),
    ),
    App(
        id='shotcut', name='Shotcut', category='Creative',
        description='Trim clips, edit video and audio, and apply filters on a timeline.',
        url='https://shotcut.org/download/', host='shotcut.org',
        color='#83c6ec', glyph='Sh', tags=('video', 'editor', 'audio', 'filters'),
    ),
    App(
        id='krita', name='Krita', category='Creative',
        description='Paint and draw digitally with configurable brushes and layers.',
        url='https://krita.org/en/download/', host='krita.org',
        color='#e6a6df', glyph='Kr', tags=('painting', 'drawing', 'brush', 'illustration'),
    ),
    App(
        id='handbrake', name='HandBrake', category='Media',
        description='Convert video files and adjust compression, resolution, and format.',
        url='https://handbrake.fr/downloads.php', host='handbrake.fr',
        color='#e9c280', glyph='H', tags=('video', 'transcoder', 'encoder', 'convert'),
    ),
    App(
        id='kdenlive', name='Kdenlive', category='Creative',
        description='Edit video on a multitrack timeline with titles, transitions, and effects.',
        url='https://kdenlive.org/download/', host='kdenlive.org',
        color='#9bb7f3', glyph='Kd', tags=('video', 'editor', 'timeline', 'kde'),
    ),
    App(
        id='joplin', name='Joplin', category='Productivity',
        description='Write notes and to-do lists, then organize them into notebooks.',
        url='https://joplinapp.org/help/install/', host='joplinapp.org',
        color='#9dc5ff', glyph='J', tags=('notes', 'markdown', 'notebooks', 'tasks'),
    ),
    App(
        id='zotero', name='Zotero', category='Productivity',
        description='Collect research sources, annotate papers, and generate citations.',
        url='https://www.zotero.org/download/', host='www.zotero.org',
        color='#f9aca7', glyph='Z', tags=('research', 'citations', 'references', 'pdf'),
    ),
    App(
        id='calibre', name='Calibre', category='Productivity',
        description='Organize an ebook library and convert books between supported formats.',
        url='https://calibre-ebook.com/download', host='calibre-ebook.com',
        color='#e7ae92', glyph='C', tags=('ebooks', 'reader', 'library', 'epub'),
    ),
    App(
        id='sumatra-pdf', name='Sumatra PDF', category='Productivity',
        description='Read PDFs, ebooks, and comic book files on Windows.',
        url='https://www.sumatrapdfreader.org/download-free-pdf-viewer', host='www.sumatrapdfreader.org',
        color='#f5d480', glyph='SP', tags=('pdf', 'reader', 'documents', 'windows'),
    ),
    App(
        id='localsend', name='LocalSend', category='Utilities',
        description='Send files to nearby devices on your local network.',
        url='https://localsend.org/download', host='localsend.org',
        color='#96e2cf', glyph='LS', tags=('file transfer', 'sharing', 'local network', 'lan'),
    ),
    App(
        id='syncthing', name='Syncthing', category='Utilities',
        description='Keep folders in sync directly between devices you choose.',
        url='https://syncthing.net/downloads/', host='syncthing.net',
        color='#8edcea', glyph='S', tags=('sync', 'folders', 'files', 'peer to peer'),
    ),
    App(
        id='python', name='Python', category='Development',
        description='Run Python programs and write scripts for automation and development.',
        url='https://www.python.org/downloads/', host='www.python.org',
        color='#a6c6f2', glyph='Py', tags=('language', 'interpreter', 'programming', 'scripting'),
    ),
    App(
        id='sqlitebrowser', name='DB Browser for SQLite', category='Development',
        description='Browse, query, and edit SQLite databases through a graphical interface.',
        url='https://sqlitebrowser.org/dl/', host='sqlitebrowser.org',
        color='#a1cfe8', glyph='DB', tags=('sqlite', 'database', 'sql', 'editor'),
    ),
    App(
        id='steam', name='Steam', category='Gaming',
        description='Browse the Steam store and install the client for your game library.',
        url='https://store.steampowered.com/about/', host='store.steampowered.com',
        color='#9fc8f1', glyph='St', tags=('games', 'store', 'launcher', 'valve'),
    ),
    App(
        id='epic-games', name='Epic Games Launcher', category='Gaming',
        description='Get the Epic Games client for the store and your game library.',
        url='https://launcher.epicgames.com/', host='launcher.epicgames.com',
        color='#d2d6e2', glyph='Ep', tags=('games', 'store', 'launcher', 'epic'),
        notice='Epic currently offers this launcher as a preview. Some features may change or be unavailable.',
    ),
    App(
        id='gog-galaxy', name='GOG GALAXY', category='Gaming',
        description='Manage your GOG library and connect supported game accounts.',
        url='https://www.gog.com/galaxy', host='www.gog.com',
        color='#c6a6f1', glyph='Go', tags=('games', 'store', 'launcher', 'library'),
    ),
    App(
        id='itch-io', name='itch.io app', category='Gaming',
        description='Find independent games and manage your itch.io library.',
        url='https://itch.io/app', host='itch.io',
        color='#f4a0ab', glyph='It', tags=('games', 'indie', 'store', 'launcher'),
    ),
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
                 tags=list(app.tags), notice=app.notice) for app in CATALOG]
