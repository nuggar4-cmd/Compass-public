"""Exercise the desktop UI and Windows native confirmation without opening a browser."""
from pathlib import Path
from unittest.mock import patch
import json
import os
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import webview
import main
from compass.catalog import CATALOG, destination

result_path = ROOT / 'desktop-smoke.json'
SUGGESTION_URL = 'https://github.com/nuggar4-cmd/Compass-public/issues/new?template=catalog-suggestion.yml'
completed = threading.Event()
original_create = webview.create_window
opened = []
on_windows = sys.platform == 'win32'

SCRIPT = r"""
(async () => {
  if (!document.getElementById('app-version') || window.compassSmokeStarted) return;
  window.compassSmokeStarted = true;
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
  try {
    for (let i = 0; i < 100 && !document.getElementById('app-version').textContent; i++) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    check('desktop entry point', new URLSearchParams(location.search).get('desktop') === '1');
    check('only explicit bridge methods', Object.keys(window.pywebview.api).sort().join(',') ===
      'app_info,catalog,explain_link,inspect_link,open_official,smoke_choose_confirmation,smoke_report,suggest_link');
    const catalog = await window.pywebview.api.catalog();
    check('actual bridge catalog', catalog.length === expectedCount);
    const {version} = await window.pywebview.api.app_info();
    check('app version', Boolean(version) && document.getElementById('app-version').textContent.includes(version));
    check('rendered all catalog cards', document.querySelectorAll('.card').length === expectedCount);
    const language = document.getElementById('language');
    const selectLanguage = value => {
      language.value = value;
      language.dispatchEvent(new Event('change'));
    };
    selectLanguage('en');
    const search = document.getElementById('search');
    search.value = 'studio obsproject.com'; search.dispatchEvent(new Event('input'));
    check('search across name and publisher domain', document.querySelectorAll('.card').length === 1 &&
      document.querySelector('.card[data-app-id="obs"] .details-button'));
    document.querySelector('[data-view="library"]').click();
    check('library keeps the active search', search.value === 'studio obsproject.com' &&
      document.querySelectorAll('.card').length === 1);
    selectLanguage('tr');
    check('Turkish publisher badge and Education category',
      document.documentElement.lang === 'tr' &&
      document.querySelector('.card[data-app-id="obs"] .security-label--verified')?.textContent === 'Güvenli' &&
      document.querySelector('[data-category="Education"]')?.textContent.includes('Eğitim'));
    selectLanguage('en');
    search.value = ''; search.dispatchEvent(new Event('input'));
    document.querySelector('[data-category="Gaming"]').click();
    document.querySelector('.card[data-app-id="epic-games"] .details-button').click();
    check('verified publisher and preview caution',
      document.getElementById('detail-verification').textContent === 'Verified publisher' &&
      !document.getElementById('detail-notice').hidden &&
      document.getElementById('detail-notice').textContent.includes('preview') &&
      document.getElementById('detail-url').textContent === 'https://launcher.epicgames.com/');
    document.querySelector('.dialog-close').click();
    document.querySelector('[data-category="Utilities"]').click();
    const utilitiesCount = catalog.filter(app => app.category === 'Utilities').length;
    check('category', utilitiesCount > 0 && document.querySelectorAll('.card').length === utilitiesCount);
    document.querySelector('.card[data-app-id="7zip"] .details-button').click();
    check('details dialog', document.getElementById('app-dialog').open);
    check('exact destination', document.getElementById('detail-url').textContent === 'https://www.7-zip.org/');
    check('native bridge ready', !document.getElementById('open-official').disabled);
    document.querySelector('.dialog-close').click();
    document.getElementById('trust-details').click();
    check('privacy navigation', !document.getElementById('privacy-page').hidden);
    if (window.pywebview.api.smoke_choose_confirmation) {
      const confirmationCases = [
        [false, false, 'Opening cancelled.', 'native confirmation cancels'],
        [true, false, 'Could not open your browser. Please try again.', 'Windows Shell failure can be retried'],
        [true, true, 'Sent the official 7-Zip link to your browser.', 'native confirmation accepts on retry'],
      ];
      for (const [approve, ok, message, label] of confirmationCases) {
        const [chosen, result] = await Promise.all([
          window.pywebview.api.smoke_choose_confirmation(approve),
          window.pywebview.api.open_official('7zip'),
        ]);
        check(label, chosen && result.ok === ok && result.message === message);
      }
      checks.push('native confirmation defaults to Cancel');
    }
    document.querySelector('[data-view="discover"]').click();
    document.querySelector('[data-view="checker"]').click();
    const address = document.getElementById('link-address');
    const checker = document.getElementById('link-check-form');
    const badge = document.getElementById('link-check-badge');
    address.value = 'https://www.7-zip.org/';
    checker.requestSubmit();
    check('exact publisher address verified in the desktop checker', await waitFor(() => badge.textContent === 'Safe'));
    const unlisted = await window.pywebview.api.inspect_link('https://www.microsoft.com/support/');
    const insecure = await window.pywebview.api.inspect_link('http://www.7-zip.org/');
    check('unlisted and insecure addresses never get a Safe verdict', unlisted.status === 'unverified' && insecure.status === 'blocked');
    document.querySelector('[data-view="discover"]').click();
    const suggest = document.getElementById('suggest-link');
    check('suggestion button is available', suggest && suggest.getClientRects().length > 0 && !suggest.disabled);
    for (const [approve, message, label] of [
      [false, 'Opening cancelled.', 'native suggestion confirmation cancels'],
      [true, 'Opened the GitHub suggestion form.', 'native suggestion confirmation accepts'],
    ]) {
      const chosen = window.pywebview.api.smoke_choose_confirmation(approve, true);
      suggest.click();
      check(label, await chosen && await waitFor(() => document.getElementById('toast').textContent === message));
    }
    const start = location.href;
    window.open('about:blank', '_blank');
    await new Promise(resolve => setTimeout(resolve, 250));
    check('popup keeps Compass on the bundled UI', location.href === start);
    location.assign('about:blank');
    await new Promise(resolve => setTimeout(resolve, 250));
    check('unapproved renderer navigation blocked', location.href === start);
    await window.pywebview.api.smoke_report({ok: true, checks});
  } catch (error) {
    await window.pywebview.api.smoke_report({ok: false, checks, error: String(error)});
  }
})();
""".replace('EXPECTED_CATALOG_COUNT', str(len(CATALOG)))


def smoke_choose_confirmation(approve, suggestion=False):
    from ctypes import POINTER, WinDLL, byref, c_int
    from ctypes.wintypes import BOOL, DWORD, HWND, LPARAM, LPCWSTR, UINT, WPARAM

    user32 = WinDLL('user32')
    user32.FindWindowW.argtypes = [LPCWSTR, LPCWSTR]
    user32.FindWindowW.restype = HWND
    user32.GetWindowThreadProcessId.argtypes = [HWND, POINTER(DWORD)]
    user32.GetWindowThreadProcessId.restype = DWORD
    user32.GetDlgItem.argtypes = [HWND, c_int]
    user32.GetDlgItem.restype = HWND
    user32.PostMessageW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    user32.PostMessageW.restype = BOOL
    user32.SendMessageW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    user32.SendMessageW.restype = LPARAM
    button_id = 1 if approve else 2  # IDOK or IDCANCEL
    title = 'Open the GitHub suggestion form?' if suggestion else 'Open official website?'

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        dialog = user32.FindWindowW('#32770', title)
        pid = DWORD()
        if dialog:
            user32.GetWindowThreadProcessId(dialog, byref(pid))
            if pid.value == os.getpid():
                button = user32.GetDlgItem(dialog, button_id)
                if button:
                    default = user32.SendMessageW(dialog, 0x0400, 0, 0)  # DM_GETDEFID
                    posted = user32.PostMessageW(dialog, 0x0111, button_id, button)  # WM_COMMAND
                    return bool(posted) and default == 0x534B0002  # DC_HASDEFID and IDCANCEL
        time.sleep(0.05)
    return False


def create(*args, **kwargs):
    window = original_create(*args, **kwargs)

    def smoke_report(result):
        if result.get('ok') and on_windows:
            if webview.renderer != 'edgechromium' or opened != [destination('7zip')] * 2 + [SUGGESTION_URL]:
                result.update(ok=False, error='Unexpected Windows renderer or browser destination')
            else:
                result['checks'].extend(['Edge WebView2 renderer', 'exact approved browser destinations'])
        result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
        completed.set()
        window.destroy()
        return True

    window.expose(smoke_report, smoke_choose_confirmation)

    def loaded():
        window.run_js(SCRIPT)
    window.events.loaded += loaded
    return window

webview.create_window = create


def observe_browser_handoff(url):
    opened.append(url)
    if len(opened) == 1:
        raise OSError('Simulated Windows Shell failure')

def watchdog():
    if not completed.wait(75):
        print('FAIL: desktop smoke test timed out', flush=True)
        os._exit(1)


result_path.unlink(missing_ok=True)
threading.Thread(target=watchdog, daemon=True).start()
with patch.object(os, 'startfile', side_effect=observe_browser_handoff, create=True), patch(
    'webbrowser.open', side_effect=AssertionError('The Windows smoke test must use the Shell launcher.'),
):
    main.main()
if not result_path.exists():
    raise SystemExit('FAIL: no desktop result')
result = json.loads(result_path.read_text(encoding='utf-8'))
print(json.dumps(result, indent=2))
raise SystemExit(0 if result.get('ok') else 1)
