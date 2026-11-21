"""Start the Compass desktop window."""
from pathlib import Path
import sys
from compass.bridge import Bridge
from compass.windows import (
    WEBVIEW2_HELP, confirm_windows_link, install_windows_navigation_guard, launch_default_browser,
    show_startup_error, startup_issue,
)


def startup_failed(message):
    if sys.platform == 'win32':
        show_startup_error(message)
    raise SystemExit(message)


def main():
    on_windows = sys.platform == 'win32'
    on_linux = sys.platform.startswith('linux')
    if not on_windows and not on_linux:
        startup_failed('Compass Desktop supports Windows and Linux. Open ui/index.html for a catalog preview.')

    if on_windows:
        import winreg

        issue = startup_issue(winreg)
        if issue:
            startup_failed(issue)

    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    index = base / 'ui' / 'index.html'
    try:
        version = (base / 'VERSION').read_text(encoding='utf-8').strip()
        if not version or not index.is_file():
            raise OSError
    except OSError:
        if on_windows:
            startup_failed('Compass files are missing. Extract the whole archive again and keep the '
                           '_internal folder next to Compass.exe.')
        startup_failed('Compass files are missing. Reinstall the package or restore the source checkout.')

    if on_linux:
        from compass.linux import run

        run(index.parent, version)
        return

    try:
        import webview
    except ImportError:
        startup_failed('Compass is missing a desktop dependency. Extract the whole package again '
                       'and keep the _internal folder next to Compass.exe. For a source checkout, '
                       'follow the setup steps in the README.')

    from compass.windows_assets import serve_windows_assets

    try:
        with serve_windows_assets(index.parent) as url:
            start_webview(webview, url, version)
    except OSError:
        startup_failed('Compass could not load its bundled interface. Verify the extracted '
                       'files and try opening Compass again.')


def start_webview(webview, url, version):
    webview.settings.update({
        'ALLOW_DOWNLOADS': False,
        'IGNORE_SSL_ERRORS': False,
        'OPEN_EXTERNAL_LINKS_IN_BROWSER': False,
        'OPEN_DEVTOOLS_IN_DEBUG': False,
        'SHOW_DEFAULT_MENUS': False,
    })

    def confirm_link(title, message):
        return confirm_windows_link(window, title, message)

    bridge = Bridge(confirm_link, launch_default_browser, version=version)
    window = webview.create_window(
        'Compass', url,
        width=1100, height=740, min_size=(600, 480),
        background_color='#0b0e14', text_select=False,
    )
    window.expose(bridge.app_info, bridge.catalog, bridge.open_official, bridge.suggest_link)
    unsupported_renderer = False

    def verify_renderer(renderer):
        nonlocal unsupported_renderer
        if renderer != 'edgechromium':
            unsupported_renderer = True
            return False

    window.events.initialized += verify_renderer
    navigation_guard_failed = install_windows_navigation_guard(window)
    webview.start(gui='edgechromium', debug=False, private_mode=True)
    if unsupported_renderer:
        startup_failed(WEBVIEW2_HELP)
    if navigation_guard_failed():
        startup_failed('Compass could not initialize the protected WebView2 window.')


if __name__ == '__main__':
    main()
