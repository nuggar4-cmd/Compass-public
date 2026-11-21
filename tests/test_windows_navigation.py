"""Exercise the WebView2 policy and startup ordering without a native window."""

import json
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from compass.windows import install_windows_navigation_guard


class Hooks(list):
    def __iadd__(self, callback):
        self.append(callback)
        return self

    def __isub__(self, callback):
        self.remove(callback)
        return self


class WindowsNavigationTests(unittest.TestCase):
    def setUp(self):
        self.url = 'http://127.0.0.1:8989/index.html?desktop=1'
        self.permission_state = SimpleNamespace(Default=object(), Deny=object())
        self.enterContext(patch.dict(sys.modules, {
            'Microsoft.Web.WebView2.Core': SimpleNamespace(CoreWebView2PermissionState=self.permission_state),
        }))
        self.core = SimpleNamespace(
            NewWindowRequested=Hooks(), LaunchingExternalUriScheme=Hooks(), FrameNavigationStarting=Hooks(),
            PermissionRequested=Hooks(),
        )
        self.control = SimpleNamespace(
            CoreWebView2=None, NavigationStarting=Hooks(), CoreWebView2InitializationCompleted=Hooks(),
            NavigationCompleted=Hooks(), WebMessageReceived=Hooks(), Source=self.url,
        )
        self.browser = SimpleNamespace(
            webview=self.control, load_url=Mock(), on_new_window_request=Mock(), on_script_notify=Mock(),
            on_navigation_completed=Mock(),
        )
        self.core.NewWindowRequested.append(self.browser.on_new_window_request)
        self.control.WebMessageReceived.append(self.browser.on_script_notify)
        self.control.NavigationCompleted.append(self.browser.on_navigation_completed)
        self.form = SimpleNamespace(browser=self.browser, Close=Mock(), IsDisposed=False, BeginInvoke=Mock())
        self.window = SimpleNamespace(
            native=self.form, real_url=self.url,
            events=SimpleNamespace(initialized=Hooks(), before_show=Hooks()),
            _functions={'catalog': Mock(), 'app_info': Mock(), 'open_official': Mock()},
        )
        self.failed = install_windows_navigation_guard(self.window)
        self.window.events.initialized[0]('edgechromium')
        with patch.dict(sys.modules, System=SimpleNamespace(Action=lambda callback: callback)):
            self.window.events.before_show[0]()

    def test_loads_local_page_only_after_native_guards_are_ready(self):
        self.assertIsNone(self.window.real_url)
        self.browser.load_url.assert_not_called()

        def check_permission_guard(_url):
            request = SimpleNamespace(State=self.permission_state.Default)
            self.core.PermissionRequested[0](self.core, request)
            self.assertIs(request.State, self.permission_state.Deny)

        self.browser.load_url.side_effect = check_permission_guard
        self.control.CoreWebView2 = self.core
        self.control.CoreWebView2InitializationCompleted[0](self.control, SimpleNamespace(IsSuccess=True))
        self.assertEqual(self.window.real_url, self.url)
        self.browser.load_url.assert_called_once_with(self.url)
        self.assertFalse(self.failed())

        for uri, blocked in (
            (self.url, False), (self.url + '#main-content', False),
            (self.url + '&other=1', True), (self.url.replace('8989', '8990'), True),
            (self.url.replace('index.html', 'catalog.js'), True), ('https://example.test/', True),
        ):
            with self.subTest(uri=uri):
                args = SimpleNamespace(Uri=uri, Cancel=False, NavigationId=1)
                self.control.NavigationStarting[0](self.control, args)
                self.assertIs(args.Cancel, blocked)

        self.assertNotIn(self.browser.on_new_window_request, self.core.NewWindowRequested)
        popup = SimpleNamespace(Handled=False)
        self.core.NewWindowRequested[0](self.core, popup)
        self.assertTrue(popup.Handled)
        for callback in (self.core.FrameNavigationStarting[0], self.core.LaunchingExternalUriScheme[0]):
            args = SimpleNamespace(Cancel=False)
            callback(self.core, args)
            self.assertTrue(args.Cancel)

    def test_core_setup_error_schedules_close_without_loading_content(self):
        self.control.CoreWebView2 = self.core
        self.core.NewWindowRequested.clear()
        with self.assertLogs(level='ERROR'):
            self.control.CoreWebView2InitializationCompleted[0](self.control, SimpleNamespace(IsSuccess=True))
        self.assertTrue(self.failed())
        self.assertIsNone(self.window.real_url)
        self.browser.load_url.assert_not_called()
        self.form.BeginInvoke.assert_called_once_with(self.form.Close)

    def test_only_completed_approved_navigation_injects_bridge(self):
        self.assertNotIn(self.browser.on_navigation_completed, self.control.NavigationCompleted)
        start = self.control.NavigationStarting[0]
        complete = self.control.NavigationCompleted[0]
        start(self.control, SimpleNamespace(Uri=self.url, Cancel=False, NavigationId=1))
        start(self.control, SimpleNamespace(Uri='about:blank', Cancel=False, NavigationId=2))
        complete(self.control, SimpleNamespace(IsSuccess=False, NavigationId=2))
        self.browser.on_navigation_completed.assert_not_called()

        success = SimpleNamespace(IsSuccess=True, NavigationId=1)
        self.control.Source = self.url + '#main-content'
        complete(self.control, success)
        complete(self.control, success)
        self.browser.on_navigation_completed.assert_called_once_with(self.control, success)

        self.browser.on_navigation_completed.reset_mock()
        for navigation_id, source, succeeded in (
            (3, 'about:blank', True), (4, self.url, False),
        ):
            start(self.control, SimpleNamespace(Uri=self.url, Cancel=False, NavigationId=navigation_id))
            self.control.Source = source
            complete(self.control, SimpleNamespace(IsSuccess=succeeded, NavigationId=navigation_id))
        self.browser.on_navigation_completed.assert_not_called()

    def test_forwards_only_authorized_messages_from_the_bundled_document(self):
        self.window._functions['sentinel'] = Mock()
        self.assertNotIn(self.browser.on_script_notify, self.control.WebMessageReceived)
        receive = self.control.WebMessageReceived[0]
        for url, payload, approved in (
            (self.url + '#main-content', ['catalog', '[]', '9768'], True),
            (self.url, ['app_info', '[]', '23829e-7'], True),
            (self.url, ['open_official', '["firefox"]', ''], True),
            (self.url, ['sentinel', '[]', '123'], False),
            ('https://example.test/', ['catalog', '[]', '123'], False),
            (self.url, ['catalog', '{}', '123'], False),
            (self.url, ['catalog', '[]', 'not-an-id'], False),
            (self.url, ['catalog', '[]'], False),
        ):
            with self.subTest(url=url, payload=payload):
                self.browser.on_script_notify.reset_mock()
                message = SimpleNamespace(Source=url, get_WebMessageAsJson=lambda: json.dumps(payload))
                receive(self.control, message)
                if approved:
                    self.browser.on_script_notify.assert_called_once_with(self.control, message)
                else:
                    self.browser.on_script_notify.assert_not_called()
