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
from compass.catalog import CATALOG
from compass.linux import START_URI

APPROVED_URL = 'https://www.7-zip.org/'
SUGGESTION_URL = 'https://github.com/nuggar4-cmd/Compass-public/issues/new?template=catalog-suggestion.yml'
SCRIPT = """
const $ = id => document.getElementById(id);
const details = id => document.querySelector(`.card[data-app-id="${id}"] .details-button`);
const checks = [];
const expectedCount = EXPECTED_CATALOG_COUNT;
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
const ready = await waitFor(() =>
  document.querySelectorAll('.card').length === expectedCount && $('app-version').textContent);
const api = window.pywebview.api;
check('native catalog and version', ready && (await api.catalog()).length === expectedCount);
check('unknown app ID rejected', !(await api.open_official('unlisted')).ok);
$('search').value = 'studio obsproject.com';
$('search').dispatchEvent(new Event('input'));
check('search across name and publisher domain', document.querySelectorAll('.card').length === 1 &&
  details('obs'));
$('search').value = '';
$('search').dispatchEvent(new Event('input'));
document.querySelector('[data-category="Gaming"]').click();
details('epic-games').click();
check('verified publisher and preview caution',
  $('detail-verification').textContent === 'Verified publisher' &&
  !$('detail-notice').hidden && $('detail-notice').textContent.includes('preview') &&
  $('detail-url').textContent === 'https://launcher.epicgames.com/');
document.querySelector('.dialog-close').click();
document.querySelector('[data-category="Utilities"]').click();
details('7zip').click();
check('exact publisher address', $('detail-url').textContent === 'https://www.7-zip.org/');
$('open-official').click();
check('cancellation stays in Compass', await waitFor(() => $('dialog-status').textContent === 'Opening cancelled.'));
$('open-official').click();
check('approval closes details', await waitFor(() => !$('app-dialog').open));
const suggest = $('suggest-link');
if (!suggest || !suggest.getClientRects().length || suggest.disabled) throw new Error('Suggestion button unavailable');
suggest.click();
check('native suggestion confirmation cancels', await waitFor(() => $('toast').textContent === 'Opening cancelled.'));
suggest.click();
check('native suggestion confirmation accepts', await waitFor(() => $('toast').textContent === 'Opened the GitHub suggestion form.'));
return checks;
""".replace('EXPECTED_CATALOG_COUNT', str(len(CATALOG)))


def smoke():
    results = []
    errors = []
    opened = []
    choices = iter((
        (Gtk.ResponseType.CANCEL, 'Open official website?', APPROVED_URL, 0),
        (Gtk.ResponseType.OK, 'Open official website?', APPROVED_URL, 0),
        (Gtk.ResponseType.CANCEL, 'Open the GitHub suggestion form?', SUGGESTION_URL, 1),
        (Gtk.ResponseType.OK, 'Open the GitHub suggestion form?', SUGGESTION_URL, 1),
    ))
    original_main = Gtk.main

    def drive_window():
        window, = Gtk.Window.list_toplevels()
        view = window.get_child()

        def handle_confirmation():
            for dialog in Gtk.Window.list_toplevels():
                if isinstance(dialog, Gtk.MessageDialog) and dialog.get_visible():
                    expected = next(choices, None)
                    if expected is None:
                        errors.append('Unexpected native confirmation')
                        dialog.response(Gtk.ResponseType.CANCEL)
                        continue
                    choice, title, url, previous_openings = expected
                    if dialog.props.text != title or url not in dialog.props.secondary_text.splitlines():
                        errors.append('Native confirmation displays a different title or destination')
                    if dialog.get_response_for_widget(dialog.get_default_widget()) != Gtk.ResponseType.CANCEL:
                        errors.append('Native confirmation does not default to Cancel')
                    if len(opened) != previous_openings:
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
                for index in range(9):
                    results.append(value.object_get_property_at_index(index).to_string())
                if opened != [APPROVED_URL, SUGGESTION_URL]:
                    errors.append(f'Unexpected browser launcher calls: {opened}')
                else:
                    results.append('native confirmations and exact browser handoffs')
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
    if errors or len(results) != 11:
        raise SystemExit('\n'.join(errors) or 'Missing Linux smoke results')


if __name__ == '__main__':
    smoke()
