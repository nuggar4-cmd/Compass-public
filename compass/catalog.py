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
    App(
        id='chrome', name='Google Chrome', category='Browsers',
        description='Browse the web with Google\'s desktop browser.',
        url='https://www.google.com/chrome/', host='www.google.com',
        color='#9fc8f1', glyph='Ch', tags=('browser', 'web', 'google'),
    ),
    App(
        id='edge', name='Microsoft Edge', category='Browsers',
        description='Browse the web and use Microsoft\'s built-in reading tools.',
        url='https://explore.microsoft.com/en-us/edge/download?form=MA13FJ', host='explore.microsoft.com',
        color='#9fc8f1', glyph='Ed', tags=('browser', 'web', 'microsoft'),
    ),
    App(
        id='opera', name='Opera', category='Browsers',
        description='Browse the web with built-in sidebar tools.',
        url='https://www.opera.com/download', host='www.opera.com',
        color='#9fc8f1', glyph='Op', tags=('browser', 'web', 'sidebar'),
    ),
    App(
        id='tor-browser', name='Tor Browser', category='Browsers',
        description='Browse through the Tor network with the Tor Project\'s browser.',
        url='https://download.torproject.org/', host='download.torproject.org',
        color='#9fc8f1', glyph='To', tags=('browser', 'tor', 'privacy', 'web'),
    ),
    App(
        id='rust', name='Rust', category='Development',
        description='Set up the Rust toolchain for systems programming.',
        url='https://rust-lang.org/tools/install/', host='rust-lang.org',
        color='#c4b7f2', glyph='Rs', tags=('compiler', 'language', 'rustup'),
    ),
    App(
        id='go', name='Go', category='Development',
        description='Install the Go toolchain for building services and command-line programs.',
        url='https://go.dev/dl/', host='go.dev',
        color='#c4b7f2', glyph='Go', tags=('compiler', 'golang', 'language'),
    ),
    App(
        id='nodejs', name='Node.js', category='Development',
        description='Run JavaScript outside the browser and use npm tooling.',
        url='https://nodejs.org/en/download', host='nodejs.org',
        color='#c4b7f2', glyph='Js', tags=('javascript', 'runtime', 'npm'),
    ),
    App(
        id='github-desktop', name='GitHub Desktop', category='Development',
        description='Review changes, commit, and manage Git branches from a desktop app.',
        url='https://github.com/apps/desktop', host='github.com',
        color='#c4b7f2', glyph='Gh', tags=('git', 'repository', 'version control'),
    ),
    App(
        id='android-studio', name='Android Studio', category='Development',
        description='Build and debug Android apps with the SDK and emulator.',
        url='https://developer.android.com/studio?auto_signin=false', host='developer.android.com',
        color='#c4b7f2', glyph='An', tags=('android', 'ide', 'emulator', 'mobile'),
    ),
    App(
        id='eclipse', name='Eclipse IDE', category='Development',
        description='Develop and debug software with the Eclipse IDE and its plug-ins.',
        url='https://www.eclipse.org/downloads/', host='www.eclipse.org',
        color='#c4b7f2', glyph='Ec', tags=('ide', 'java', 'debugger'),
    ),
    App(
        id='jetbrains-toolbox', name='JetBrains Toolbox', category='Development',
        description='Install and manage JetBrains development tools from one app.',
        url='https://www.jetbrains.com/toolbox-app/', host='www.jetbrains.com',
        color='#c4b7f2', glyph='Jb', tags=('ide', 'tool manager'),
    ),
    App(
        id='docker-desktop', name='Docker Desktop', category='Development',
        description='Build and run containers in a local development environment.',
        url='https://www.docker.com/products/docker-desktop/', host='www.docker.com',
        color='#c4b7f2', glyph='Dd', tags=('containers', 'docker', 'development'),
    ),
    App(
        id='xbox-pc', name='Xbox PC app', category='Gaming',
        description='Browse the Xbox PC catalog and manage games on Windows.',
        url='https://www.xbox.com/en-US/apps/xbox-app-on-pc', host='www.xbox.com',
        color='#a9d7a4', glyph='Xb', tags=('xbox', 'game pass', 'launcher', 'windows'),
    ),
    App(
        id='ubisoft-connect', name='Ubisoft Connect', category='Gaming',
        description='Install Ubisoft\'s client and manage your game library.',
        url='https://www.ubisoft.com/en-us/ubisoft-connect', host='www.ubisoft.com',
        color='#a9d7a4', glyph='Ub', tags=('games', 'launcher', 'store'),
    ),
    App(
        id='ea-app', name='EA app', category='Gaming',
        description='Browse and manage your Electronic Arts game library.',
        url='https://www.ea.com/ea-app', host='www.ea.com',
        color='#a9d7a4', glyph='EA', tags=('games', 'launcher', 'store'),
    ),
    App(
        id='minecraft-launcher', name='Minecraft Launcher', category='Gaming',
        description='Download the official launcher for Minecraft editions on desktop.',
        url='https://www.minecraft.net/en-us/download', host='www.minecraft.net',
        color='#a9d7a4', glyph='Mc', tags=('minecraft', 'gaming', 'launcher'),
    ),
    App(
        id='nvidia-app', name='NVIDIA App', category='Gaming',
        description='Manage NVIDIA drivers and graphics settings, and capture gameplay.',
        url='https://www.nvidia.com/en-us/software/nvidia-app/', host='www.nvidia.com',
        color='#a9d7a4', glyph='Nv', tags=('graphics', 'drivers', 'gpu', 'gaming'),
    ),
    App(
        id='signal', name='Signal Desktop', category='Communication',
        description='Use Signal messaging and calls from a linked desktop.',
        url='https://signal.org/download/', host='signal.org',
        color='#9bdade', glyph='Si', tags=('messaging', 'calls', 'chat'),
    ),
    App(
        id='element', name='Element', category='Communication',
        description='Chat and join Matrix rooms in the Element desktop client.',
        url='https://element.io/en/download', host='element.io',
        color='#9bdade', glyph='El', tags=('matrix', 'messaging', 'chat'),
    ),
    App(
        id='zoom', name='Zoom Workplace', category='Communication',
        description='Join or host meetings and use desktop collaboration tools.',
        url='https://zoom.us/download', host='zoom.us',
        color='#9bdade', glyph='Zo', tags=('meetings', 'video', 'calls', 'conferencing'),
    ),
    App(
        id='slack', name='Slack', category='Communication',
        description='Access workspace conversations, channels, and files from a desktop app.',
        url='https://slack.com/downloads/other', host='slack.com',
        color='#9bdade', glyph='Sl', tags=('team', 'chat', 'workspace', 'messaging'),
    ),
    App(
        id='telegram', name='Telegram Desktop', category='Communication',
        description='Use Telegram chats and channels from a desktop client.',
        url='https://desktop.telegram.org/', host='desktop.telegram.org',
        color='#9bdade', glyph='Tg', tags=('messaging', 'channels', 'chat'),
    ),
    App(
        id='blender', name='Blender', category='Creative',
        description='Model, animate, and render 3D scenes. The official manual explains installation.',
        url='https://docs.blender.org/manual/en/latest/getting_started/installing/', host='docs.blender.org',
        color='#eac2a3', glyph='Bl', tags=('3d', 'animation', 'rendering', 'modeling'),
    ),
    App(
        id='darktable', name='darktable', category='Creative',
        description='Organize and develop RAW photos with a nondestructive workflow.',
        url='https://www.darktable.org/install/', host='www.darktable.org',
        color='#eac2a3', glyph='Dt', tags=('photo', 'raw', 'editing'),
    ),
    App(
        id='musescore', name='MuseScore Studio', category='Creative',
        description='Write, edit, and play back music notation.',
        url='https://musescore.org/en/download', host='musescore.org',
        color='#eac2a3', glyph='Ms', tags=('sheet music', 'score', 'notation'),
    ),
    App(
        id='blockbench', name='Blockbench', category='Creative',
        description='Create low-poly models, textures, and animations.',
        url='https://blockbench.net/', host='blockbench.net',
        color='#eac2a3', glyph='Bb', tags=('3d', 'modeling', 'textures'),
    ),
    App(
        id='freecad', name='FreeCAD', category='Creative',
        description='Build editable, parametric 3D designs for CAD projects.',
        url='https://www.freecad.org/downloads.php', host='www.freecad.org',
        color='#eac2a3', glyph='Fc', tags=('cad', '3d', 'engineering'),
    ),
    App(
        id='kicad', name='KiCad', category='Creative',
        description='Draw electronic schematics and design printed circuit boards.',
        url='https://www.kicad.org/download/', host='www.kicad.org',
        color='#eac2a3', glyph='Ki', tags=('pcb', 'electronics', 'schematic'),
    ),
    App(
        id='davinci-resolve', name='DaVinci Resolve', category='Creative',
        description='Edit video, grade color, mix audio, and create visual effects.',
        url='https://www.blackmagicdesign.com/products/davinciresolve', host='www.blackmagicdesign.com',
        color='#eac2a3', glyph='Dr', tags=('video', 'editing', 'color', 'grading', 'effects'),
    ),
    App(
        id='mpv', name='mpv', category='Media',
        description='Play local audio and video files in a lightweight media player.',
        url='https://mpv.io/installation/', host='mpv.io',
        color='#ddbae4', glyph='mp', tags=('video', 'audio', 'player'),
        notice='This page includes some builds maintained outside the mpv project. Check the source of the build you choose.',
    ),
    App(
        id='foobar2000', name='foobar2000', category='Media',
        description='Play music and organize an audio library on Windows.',
        url='https://www.foobar2000.org/windows', host='www.foobar2000.org',
        color='#ddbae4', glyph='fb', tags=('music', 'audio', 'player', 'windows'),
    ),
    App(
        id='picard', name='MusicBrainz Picard', category='Media',
        description='Identify recordings and write consistent tags to audio files.',
        url='https://picard.musicbrainz.org/downloads/', host='picard.musicbrainz.org',
        color='#ddbae4', glyph='Pi', tags=('music', 'metadata', 'tags'),
    ),
    App(
        id='losslesscut', name='LosslessCut', category='Media',
        description='Trim and join supported media formats without re-encoding.',
        url='https://losslesscut.app/', host='losslesscut.app',
        color='#ddbae4', glyph='Lc', tags=('video', 'audio', 'trim', 'cut'),
    ),
    App(
        id='obsidian', name='Obsidian', category='Productivity',
        description='Write and link notes in a local Markdown vault.',
        url='https://obsidian.md/download', host='obsidian.md',
        color='#9ec7ef', glyph='Ob', tags=('notes', 'markdown', 'knowledge'),
    ),
    App(
        id='onlyoffice', name='ONLYOFFICE Desktop Editors', category='Productivity',
        description='Edit office documents, spreadsheets, presentations, and PDFs.',
        url='https://www.onlyoffice.com/desktop', host='www.onlyoffice.com',
        color='#9ec7ef', glyph='Oo', tags=('office', 'documents', 'spreadsheet', 'presentation'),
    ),
    App(
        id='pdf24', name='PDF24 Creator', category='Productivity',
        description='Create, merge, and split PDFs on Windows.',
        url='https://tools.pdf24.org/en/creator', host='tools.pdf24.org',
        color='#9ec7ef', glyph='P2', tags=('pdf', 'merge', 'split', 'windows'),
    ),
    App(
        id='drawio', name='draw.io Desktop', category='Productivity',
        description='Create flowcharts and other diagrams offline.',
        url='https://www.drawio.com/docs/manual/editor/offline/', host='www.drawio.com',
        color='#9ec7ef', glyph='Di', tags=('diagram', 'flowchart', 'offline'),
    ),
    App(
        id='anki', name='Anki', category='Productivity',
        description='Study with flashcards scheduled by spaced repetition.',
        url='https://apps.ankiweb.net/', host='apps.ankiweb.net',
        color='#9ec7ef', glyph='Ak', tags=('study', 'flashcards', 'learning'),
    ),
    App(
        id='powertoys', name='Microsoft PowerToys', category='Utilities',
        description='Use Windows utilities for shortcuts, window layouts, and files.',
        url='https://learn.microsoft.com/en-us/windows/powertoys/install', host='learn.microsoft.com',
        color='#a4d9be', glyph='Pt', tags=('windows', 'keyboard', 'files', 'layouts'),
    ),
    App(
        id='winscp', name='WinSCP', category='Utilities',
        description='Transfer files using SFTP, SCP, and other supported protocols.',
        url='https://winscp.net/eng/download.php', host='winscp.net',
        color='#a4d9be', glyph='Ws', tags=('files', 'transfer', 'sftp', 'windows'),
    ),
    App(
        id='rufus', name='Rufus', category='Utilities',
        description='Create bootable USB drives from disk images on Windows.',
        url='https://rufus.ie/en/', host='rufus.ie',
        color='#a4d9be', glyph='Ru', tags=('usb', 'boot', 'disk', 'windows'),
    ),
    App(
        id='everything', name='Everything', category='Utilities',
        description='Find Windows files and folders by name.',
        url='https://www.voidtools.com/downloads/', host='www.voidtools.com',
        color='#a4d9be', glyph='Ev', tags=('files', 'windows', 'search', 'folders'),
    ),
    App(
        id='sharex', name='ShareX', category='Utilities',
        description='Capture and annotate screenshots or record your screen on Windows.',
        url='https://getsharex.com/', host='getsharex.com',
        color='#a4d9be', glyph='Sx', tags=('screenshots', 'capture', 'recording', 'windows'),
    ),
    App(
        id='windirstat', name='WinDirStat', category='Utilities',
        description='Visualize disk usage and see which files take up space.',
        url='https://windirstat.net/download.html', host='windirstat.net',
        color='#a4d9be', glyph='Wd', tags=('disk', 'storage', 'files', 'windows'),
    ),
    App(
        id='crystaldiskinfo', name='CrystalDiskInfo', category='Utilities',
        description='Read drive temperature and SMART health information.',
        url='https://crystalmark.info/en/software/crystaldiskinfo/', host='crystalmark.info',
        color='#a4d9be', glyph='Cd', tags=('disk', 'ssd', 'smart', 'windows'),
    ),
    App(
        id='kde-connect', name='KDE Connect', category='Utilities',
        description='Share files, notifications, and controls between a desktop and other devices.',
        url='https://kdeconnect.kde.org/download.html', host='kdeconnect.kde.org',
        color='#a4d9be', glyph='Kc', tags=('phone', 'files', 'sharing', 'notifications'),
    ),
    App(
        id='visual-studio-community', name='Visual Studio Community', category='Development',
        description='Build and debug Windows, web, and cross-platform projects in Microsoft’s IDE.',
        url='https://visualstudio.microsoft.com/vs/community/', host='visualstudio.microsoft.com',
        color='#c6aff4', glyph='VS', tags=('ide', 'microsoft', 'windows', 'dotnet', 'c++'),
    ),
    App(
        id='dotnet-sdk', name='.NET SDK', category='Development',
        description='Build, test, and publish .NET projects from the command line.',
        url='https://dotnet.microsoft.com/en-us/download', host='dotnet.microsoft.com',
        color='#c1b0ef', glyph='N', tags=('dotnet', 'microsoft', 'c#', 'sdk', 'programming'),
    ),
    App(
        id='eclipse-temurin', name='Eclipse Temurin', category='Development',
        description='Download the OpenJDK development kit or runtime for Java projects.',
        url='https://adoptium.net/temurin/releases/', host='adoptium.net',
        color='#b4c4f3', glyph='Jd', tags=('java', 'jdk', 'openjdk', 'runtime'),
    ),
    App(
        id='powershell', name='PowerShell', category='Development',
        description='Use a shell and scripting language for automation on Windows, macOS, and Linux.',
        url='https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell?view=powershell-7.6', host='learn.microsoft.com',
        color='#a3c7fa', glyph='Ps', tags=('shell', 'terminal', 'scripting', 'automation'),
    ),
    App(
        id='windows-terminal', name='Windows Terminal', category='Utilities',
        description='Open command-line tools in tabs and split panes on Windows.',
        url='https://learn.microsoft.com/en-us/windows/terminal/install', host='learn.microsoft.com',
        color='#b7d0e8', glyph='Wt', tags=('terminal', 'shell', 'tabs', 'windows'),
    ),
    App(
        id='postman', name='Postman', category='Development',
        description='Send API requests, organize collections, and test responses.',
        url='https://www.postman.com/downloads/', host='www.postman.com',
        color='#f6b596', glyph='Pn', tags=('api', 'http', 'rest', 'testing'),
    ),
    App(
        id='bruno', name='Bruno', category='Development',
        description='Keep API request collections as files you can track with Git.',
        url='https://www.usebruno.com/downloads', host='www.usebruno.com',
        color='#f6ca92', glyph='Bu', tags=('api', 'http', 'rest', 'git'),
    ),
    App(
        id='dbeaver', name='DBeaver Community', category='Development',
        description='Explore databases and edit SQL queries in a desktop client.',
        url='https://dbeaver.io/download/', host='dbeaver.io',
        color='#d0bdad', glyph='Dv', tags=('database', 'sql', 'postgresql', 'mysql'),
    ),
    App(
        id='postgresql', name='PostgreSQL', category='Development',
        description='Install the open source relational database server.',
        url='https://www.postgresql.org/download/', host='www.postgresql.org',
        color='#a8c5e9', glyph='Pg', tags=('database', 'sql', 'server', 'postgres'),
    ),
    App(
        id='github-cli', name='GitHub CLI', category='Development',
        description='Work with GitHub issues, pull requests, and releases from a terminal.',
        url='https://cli.github.com/', host='cli.github.com',
        color='#c9ccdf', glyph='gh', tags=('github', 'cli', 'terminal', 'git'),
    ),
    App(
        id='podman-desktop', name='Podman Desktop', category='Development',
        description='Build, run, and inspect containers with a graphical interface.',
        url='https://podman-desktop.io/downloads', host='podman-desktop.io',
        color='#c8b6f4', glyph='Pd', tags=('containers', 'images', 'kubernetes', 'podman'),
    ),
    App(
        id='neovim', name='Neovim', category='Development',
        description='Edit code and text in a terminal with Vim-style commands and plugins.',
        url='https://neovim.io/doc/install/', host='neovim.io',
        color='#b0d9a5', glyph='Nv', tags=('editor', 'vim', 'terminal', 'code'),
    ),
    App(
        id='sublime-text', name='Sublime Text', category='Development',
        description='Edit code and text with multi-selection and project-wide search.',
        url='https://www.sublimetext.com/download', host='www.sublimetext.com',
        color='#f6c48d', glyph='Su', tags=('editor', 'code', 'text', 'projects'),
    ),
    App(
        id='zed-editor', name='Zed', category='Development',
        description='Edit projects with language support and optional collaboration tools.',
        url='https://zed.dev/download', host='zed.dev',
        color='#b6caec', glyph='Zd', tags=('editor', 'code', 'language server', 'collaboration'),
    ),
    App(
        id='vscodium', name='VSCodium', category='Development',
        description='Install a community build of the open source Code - OSS editor.',
        url='https://vscodium.com/', host='vscodium.com',
        color='#a6caec', glyph='Vc', tags=('editor', 'code', 'oss', 'programming'),
    ),
    App(
        id='winmerge', name='WinMerge', category='Utilities',
        description='Compare and merge files and folders on Windows.',
        url='https://winmerge.org/downloads/', host='winmerge.org',
        color='#d6dba0', glyph='Wm', tags=('diff', 'compare', 'merge', 'windows'),
    ),
    App(
        id='tailscale', name='Tailscale', category='Utilities',
        description='Connect your authorized devices and services through a private network.',
        url='https://tailscale.com/download', host='tailscale.com',
        color='#cdd2e5', glyph='Ts', tags=('vpn', 'network', 'mesh', 'remote access'),
    ),
    App(
        id='wireguard', name='WireGuard', category='Utilities',
        description='Set up encrypted VPN connections between configured devices.',
        url='https://www.wireguard.com/install/', host='www.wireguard.com',
        color='#eaa9b5', glyph='Wg', tags=('vpn', 'network', 'tunnel', 'encryption'),
    ),
    App(
        id='putty', name='PuTTY', category='Utilities',
        description='Connect to servers you manage using SSH or a serial connection.',
        url='https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html', host='www.chiark.greenend.org.uk',
        color='#c4c4ef', glyph='Pu', tags=('ssh', 'serial', 'terminal', 'remote access'),
    ),
    App(
        id='bitwarden', name='Bitwarden', category='Utilities',
        description='Keep passwords and secure notes in a vault you can sync across devices.',
        url='https://bitwarden.com/download/', host='bitwarden.com',
        color='#a5c8fc', glyph='Bw', tags=('password', 'vault', 'credentials', 'sync'),
    ),
    App(
        id='pandoc', name='Pandoc', category='Productivity',
        description='Convert documents between Markdown, HTML, Word, and other formats.',
        url='https://pandoc.org/installing.html', host='pandoc.org',
        color='#e4b7ae', glyph='Pa', tags=('documents', 'markdown', 'conversion', 'cli'),
    ),
    App(
        id='naps2', name='NAPS2', category='Productivity',
        description='Scan documents and save searchable PDFs with optical character recognition.',
        url='https://www.naps2.com/download', host='www.naps2.com',
        color='#a5dbcb', glyph='Na', tags=('scanner', 'pdf', 'ocr', 'documents'),
    ),
    App(
        id='openshot', name='OpenShot', category='Creative',
        description='Cut and arrange video clips, titles, transitions, and audio on a timeline.',
        url='https://www.openshot.org/download/', host='www.openshot.org',
        color='#e6a6df', glyph='Os', tags=('video', 'editor', 'timeline', 'transitions'),
    ),
    App(
        id='reaper', name='REAPER', category='Creative',
        description='Record, edit, and mix audio and MIDI in a digital audio workstation.',
        url='https://www.reaper.fm/download.php', host='www.reaper.fm',
        color='#e6a6df', glyph='Re', tags=('daw', 'audio', 'studio', 'recording', 'midi'),
        notice='REAPER offers a 60-day evaluation. Continued use requires a license.',
    ),
    App(
        id='mixxx', name='Mixxx', category='Creative',
        description='Mix tracks live with virtual decks, beat sync, and DJ controller support.',
        url='https://mixxx.org/download/', host='mixxx.org',
        color='#e6a6df', glyph='Mx', tags=('audio', 'dj', 'music', 'mixing'),
    ),
    App(
        id='ardour', name='Ardour', category='Creative',
        description='Record and edit sessions with multitrack audio and MIDI.',
        url='https://community.ardour.org/download', host='community.ardour.org',
        color='#e6a6df', glyph='Ar', tags=('daw', 'audio', 'recording', 'mixing', 'midi'),
    ),
    App(
        id='nvda', name='NVDA', category='Utilities',
        description='Read Windows interfaces and documents with a screen reader.',
        url='https://www.nvaccess.org/download/', host='www.nvaccess.org',
        color='#a4d9be', glyph='Nv', tags=('accessibility', 'screen reader', 'speech', 'braille', 'windows'),
    ),
    App(
        id='okular', name='Okular', category='Productivity',
        description='Read and annotate PDFs and open other supported document formats.',
        url='https://okular.kde.org/download/', host='okular.kde.org',
        color='#f7ce9c', glyph='Ok', tags=('reader', 'documents', 'pdf', 'annotation'),
    ),
    App(
        id='stellarium', name='Stellarium', category='Education',
        description='Explore a simulated night sky and look up stars, planets, and constellations.',
        url='https://stellarium.org/', host='stellarium.org',
        color='#b8d9f4', glyph='Se', tags=('astronomy', 'science', 'planetarium', 'stars', 'space'),
    ),
    App(
        id='geogebra', name='GeoGebra', category='Education',
        description='Plot functions, explore geometric constructions, and work through algebra problems.',
        url='https://www.geogebra.org/download', host='www.geogebra.org',
        color='#b8d9f4', glyph='Ge', tags=('math', 'calculator', 'graphing', 'geometry', 'algebra'),
    ),
    App(
        id='scratch', name='Scratch', category='Education',
        description='Build interactive stories, animations, and games with visual programming blocks.',
        url='https://scratch.mit.edu/download', host='scratch.mit.edu',
        color='#b8d9f4', glyph='Sc', tags=('coding', 'programming', 'blocks', 'offline', 'learning'),
    ),
    App(
        id='tux-paint', name='Tux Paint', category='Education',
        description='Draw with simple brushes, stamps, and effects in an editor made for children.',
        url='https://tuxpaint.org/download/', host='tuxpaint.org',
        color='#b8d9f4', glyph='Tp', tags=('drawing', 'painting', 'kids', 'classroom', 'art'),
    ),
    App(
        id='pureref', name='PureRef', category='Creative',
        description='Arrange reference images into a board while working on a design or illustration.',
        url='https://www.pureref.com/download.php', host='www.pureref.com',
        color='#e6a6df', glyph='Pr', tags=('reference', 'images', 'mood board', 'design'),
    ),
    App(
        id='zettlr', name='Zettlr', category='Productivity',
        description='Write in Markdown and organize research notes, documents, and citations.',
        url='https://www.zettlr.com/download', host='www.zettlr.com',
        color='#f7ce9c', glyph='Ze', tags=('writing', 'markdown', 'research', 'citations'),
    ),
    App(
        id='lyx', name='LyX', category='Productivity',
        description='Write structured documents with equations and LaTeX typesetting.',
        url='https://www.lyx.org/Download', host='www.lyx.org',
        color='#f7ce9c', glyph='Ly', tags=('writing', 'latex', 'typesetting', 'academic', 'math'),
    ),
    App(
        id='sigil', name='Sigil', category='Productivity',
        description='Create and edit ebooks in EPUB format.',
        url='https://sigil-ebook.com/sigil/download/', host='sigil-ebook.com',
        color='#f7ce9c', glyph='Si', tags=('books', 'ebook', 'epub', 'editor', 'publishing'),
    ),
    App(
        id='audacious', name='Audacious', category='Media',
        description='Play local music, build playlists, and customize playback with plugins.',
        url='https://audacious-media-player.org/download', host='audacious-media-player.org',
        color='#f6ad68', glyph='Au', tags=('audio', 'music', 'player', 'playlists'),
    ),
    App(
        id='canva-windows', name='Canva for Windows', category='Creative',
        description='Create graphics, social posts, and presentations in the Canva desktop app.',
        url='https://www.canva.com/download/windows/', host='www.canva.com',
        color='#e6a6df', glyph='Ca', tags=('design', 'templates', 'presentation', 'graphics', 'windows'),
    ),
    App(
        id='lmms', name='LMMS', category='Creative',
        description='Compose tracks with software instruments, patterns, and a step sequencer.',
        url='https://docs.lmms.io/user-manual/getting-started/installation', host='docs.lmms.io',
        color='#e6a6df', glyph='Lm', tags=('daw', 'music', 'synthesizer', 'audio', 'sequencer'),
    ),
    App(
        id='battle-net', name='Battle.net', category='Gaming',
        description='Install and update games from Blizzard and Activision in the Battle.net desktop app.',
        url='https://download.battle.net/en-us/desktop', host='download.battle.net',
        color='#a2c5ff', glyph='Bn', tags=('blizzard', 'activision', 'game launcher', 'store'),
    ),
    App(
        id='heroic-games', name='Heroic Games Launcher', category='Gaming',
        description='Manage games from Epic Games, GOG, and Amazon Games in an open-source launcher.',
        url='https://heroicgameslauncher.com/', host='heroicgameslauncher.com',
        color='#a2c5ff', glyph='Hg', tags=('gaming', 'launcher', 'epic', 'gog', 'amazon', 'linux'),
    ),
    App(
        id='geforce-now', name='GeForce NOW', category='Gaming',
        description='Stream supported PC games from NVIDIA’s cloud gaming service.',
        url='https://www.nvidia.com/en-us/geforce-now/download/', host='www.nvidia.com',
        color='#a2c5ff', glyph='Gn', tags=('cloud gaming', 'streaming', 'nvidia', 'game client'),
    ),
    App(
        id='ps-remote-play', name='PS Remote Play', category='Gaming',
        description='Stream from a PlayStation 4 or PlayStation 5 console and play from a PC or Mac.',
        url='https://www.playstation.com/en-us/support/games/playstation-remote-play-on-pc-and-mac/', host='www.playstation.com',
        color='#a2c5ff', glyph='Ps', tags=('playstation', 'sony', 'ps4', 'ps5', 'streaming'),
    ),
    App(
        id='prism-launcher', name='Prism Launcher', category='Gaming',
        description='Manage separate Minecraft installations and their modpacks in a desktop launcher.',
        url='https://prismlauncher.org/download/', host='prismlauncher.org',
        color='#a2c5ff', glyph='Pl', tags=('minecraft', 'mods', 'modpacks', 'java', 'launcher'),
    ),
    App(
        id='moonlight', name='Moonlight Game Streaming', category='Gaming',
        description='Stream games from a compatible PC to another device on your network.',
        url='https://moonlight-stream.org/', host='moonlight-stream.org',
        color='#a2c5ff', glyph='Ml', tags=('game streaming', 'local network', 'remote play', 'sunshine'),
    ),
    App(
        id='modrinth', name='Modrinth App', category='Gaming',
        description='Install and manage Minecraft mods and modpacks in the desktop app.',
        url='https://modrinth.com/app', host='modrinth.com',
        color='#a2c5ff', glyph='Mr', tags=('minecraft', 'mods', 'modpacks', 'launcher'),
        notice='The publisher labels this app beta. Review each mod’s author separately before installing it.',
    ),
    App(
        id='playnite', name='Playnite', category='Gaming',
        description='Combine games from multiple stores into one library on Windows.',
        url='https://playnite.link/', host='playnite.link',
        color='#a2c5ff', glyph='Pt', tags=('windows', 'game library', 'launcher', 'store'),
    ),
    App(
        id='whatsapp-desktop', name='WhatsApp Desktop', category='Communication',
        description='Read chats, share files, and make calls from a linked Windows or Mac device.',
        url='https://www.whatsapp.com/download/desktop', host='www.whatsapp.com',
        color='#a5ddd1', glyph='Wa', tags=('chat', 'messaging', 'calls', 'meta'),
    ),
    App(
        id='mumble', name='Mumble', category='Communication',
        description='Join a low-latency voice chat server from an open-source desktop client.',
        url='https://www.mumble.info/downloads/', host='www.mumble.info',
        color='#a5ddd1', glyph='Mu', tags=('voice', 'chat', 'gaming', 'voip'),
    ),
    App(
        id='teamspeak', name='TeamSpeak', category='Communication',
        description='Use voice channels, text chat, and group communication from the desktop client.',
        url='https://www.teamspeak.com/en/downloads/', host='www.teamspeak.com',
        color='#a5ddd1', glyph='Ts', tags=('voice', 'chat', 'gaming', 'voip'),
    ),
    App(
        id='microsoft-teams', name='Microsoft Teams', category='Communication',
        description='Join meetings, chat with coworkers, and collaborate from the desktop app.',
        url='https://www.microsoft.com/en-us/microsoft-teams/download-app', host='www.microsoft.com',
        color='#a5ddd1', glyph='Mt', tags=('meetings', 'work', 'chat', 'video', 'microsoft'),
    ),
    App(
        id='session', name='Session', category='Communication',
        description='Send messages and participate in group conversations from the desktop client.',
        url='https://getsession.org/download', host='getsession.org',
        color='#a5ddd1', glyph='Se', tags=('messaging', 'group chat', 'privacy'),
    ),
    App(
        id='zulip', name='Zulip', category='Communication',
        description='Organize team conversations by topic in an open-source desktop app.',
        url='https://zulip.com/apps/', host='zulip.com',
        color='#a5ddd1', glyph='Zu', tags=('chat', 'teams', 'topics', 'collaboration'),
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
