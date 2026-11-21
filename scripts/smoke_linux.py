"""Exercise the native WebKitGTK UI without visiting an external site."""

from pathlib import Path
import sys
from unittest.mock import patch

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gio, GLib, Gtk, WebKit2

source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(source))
import main
from compass.linux import START_URI

APPROVED_URL = 'https://www.7-zip.org/'
SCRIPT = """
const $ = id => document.getElementById(id);
const checks = [];
function check(name, condition) {
  if (!condition) throw new Error(name);
  checks.push(name);
}
async function waitFor(condition) {
  for (let i = 0; i < 100; i++) {
    if (condition()) return true;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  return false;
}
check('native catalog and version', await waitFor(() =>
  document.querySelectorAll('.card').length === 4 && $('app-version').textContent));
const api = window.pywebview.api;
check('unknown app ID rejected', !(await api.open_official('unlisted')).ok);
$('search').value = 'recording';
$('search').dispatchEvent(new Event('input'));
check('search', document.querySelectorAll('.card').length === 1 && $('cards').textContent.includes('OBS Studio'));
$('search').value = '';
$('search').dispatchEvent(new Event('input'));
document.querySelector('[data-category="Utilities"]').click();
document.querySelector('.details-button').click();
check('exact publisher address', $('detail-url').textContent === 'https://www.7-zip.org/');
$('open-official').click();
check('cancellation stays in Compass', await waitFor(() => $('dialog-status').textContent === 'Opening cancelled.'));
$('open-official').click();
check('approval closes details', await waitFor(() => !$('app-dialog').open));
return checks;
"""


def smoke():
    results = []
    errors = []
    opened = []
    choices = iter((Gtk.ResponseType.CANCEL, Gtk.ResponseType.OK))
    original_main = Gtk.main

    def drive_window():
        window, = Gtk.Window.list_toplevels()
        view = window.get_child()

        def handle_confirmation():
            for dialog in Gtk.Window.list_toplevels():
                if isinstance(dialog, Gtk.MessageDialog) and dialog.get_visible():
                    choice = next(choices, Gtk.ResponseType.CANCEL)
                    if dialog.props.secondary_text.split('\n')[2] != APPROVED_URL:
                        errors.append('Native confirmation displays a different destination')
                    if dialog.get_response_for_widget(dialog.get_default_widget()) != Gtk.ResponseType.CANCEL:
                        errors.append('Native confirmation does not default to Cancel')
                    if choice == Gtk.ResponseType.CANCEL and opened:
                        errors.append('Browser opened before approval')
                    dialog.response(choice)
            return GLib.SOURCE_CONTINUE

        def finish_navigation_check():
            if view.get_uri() != START_URI:
                errors.append('External renderer navigation was allowed')
            else:
                results.append('unapproved renderer navigation blocked')
            window.destroy()
            return GLib.SOURCE_REMOVE

        def finish_script(webview, response, _data):
            try:
                value = webview.call_async_javascript_function_finish(response)
                for index in range(6):
                    results.append(value.object_get_property_at_index(index).to_string())
                if opened != [APPROVED_URL]:
                    errors.append(f'Unexpected browser launcher calls: {opened}')
                else:
                    results.append('native confirmation and exact browser handoff')
                webview.load_uri('about:blank')
                GLib.timeout_add(300, finish_navigation_check)
            except (GLib.Error, TypeError) as error:
                errors.append(str(error))
                window.destroy()

        def loaded(webview, event):
            if event == WebKit2.LoadEvent.FINISHED and webview.get_uri() == START_URI and not results:
                webview.call_async_javascript_function(SCRIPT, -1, None, None, None, None, finish_script, None)

        def timed_out():
            errors.append('Compass Linux smoke test timed out')
            window.destroy()
            return GLib.SOURCE_REMOVE

        view.connect('load-changed', loaded)
        GLib.timeout_add(50, handle_confirmation)
        GLib.timeout_add_seconds(20, timed_out)
        original_main()

    with patch.object(Gtk, 'main', drive_window), patch.object(
        Gio.AppInfo, 'launch_default_for_uri', lambda url, _context: opened.append(url) or True,
    ):
        main.main()
    for result in results:
        print(f'PASS: {result}')
    if errors or len(results) != 8:
        raise SystemExit('\n'.join(errors) or 'Missing Linux smoke results')


if __name__ == '__main__':
    smoke()
