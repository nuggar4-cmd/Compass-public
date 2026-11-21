"""Native startup and WebView2 policy for the portable Windows build."""

import json
import logging
import re

WEBVIEW2_CLIENT = r'Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
WEBVIEW2_HELP = (
    'Install or repair the Microsoft Edge WebView2 Evergreen Runtime, then open Compass again.\n\n'
    'https://developer.microsoft.com/microsoft-edge/webview2/'
)


def _registry_value(registry, hive, path, name):
    try:
        with registry.OpenKey(hive, path) as key:
            return registry.QueryValueEx(key, name)[0]
    except OSError:
        return None


def startup_issue(registry):
    framework = _registry_value(
        registry, registry.HKEY_LOCAL_MACHINE,
        r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full', 'Release',
    )
    if not isinstance(framework, int) or framework < 394802:
        return 'Install or repair Microsoft .NET Framework 4.6.2 or later, then open Compass again.'

    # Compass ships as Windows x64. Microsoft's machine-wide Evergreen key is in the 32-bit view.
    for hive, path in (
        (registry.HKEY_CURRENT_USER, rf'SOFTWARE\{WEBVIEW2_CLIENT}'),
        (registry.HKEY_LOCAL_MACHINE, rf'SOFTWARE\WOW6432Node\{WEBVIEW2_CLIENT}'),
    ):
        value = _registry_value(registry, hive, path, 'pv')
        if isinstance(value, str):
            parts = value.split('.')
            if len(parts) == 4 and all(part.isascii() and part.isdecimal() for part in parts):
                if any(part.strip('0') for part in parts):
                    return None
    return WEBVIEW2_HELP


def show_startup_error(message):
    from ctypes import windll

    windll.user32.MessageBoxW(None, message, 'Compass could not start', 0x10)


def confirm_windows_link(window, title, message):
    from System import Boolean, Func
    from System.Windows.Forms import (
        DialogResult, MessageBox, MessageBoxButtons, MessageBoxDefaultButton, MessageBoxIcon,
    )

    form = window.native
    if form.IsDisposed:
        return False

    def confirm():
        return MessageBox.Show(
            form, message, title, MessageBoxButtons.OKCancel,
            MessageBoxIcon.Question, MessageBoxDefaultButton.Button2,
        ) == DialogResult.OK

    if form.InvokeRequired:
        return bool(form.Invoke(Func[Boolean](confirm)))
    return confirm()


def launch_default_browser(url):
    """Hand an approved URL to the Windows Shell's configured handler."""
    from os import startfile

    try:
        startfile(url)
    except OSError:
        return False
    return True


def _allowed_bridge_message(message, methods):
    if not isinstance(message, str) or len(message) > 16_384:
        return False
    try:
        request = json.loads(message)
        if not isinstance(request, list) or len(request) != 3:
            return False
        method, arguments, request_id = request
        # The wheel derives IDs from the decimal string form of Math.random().
        return (
            isinstance(method, str) and method in methods
            and isinstance(request_id, str) and re.fullmatch(r'[0-9e-]{0,32}', request_id) is not None
            and isinstance(arguments, str) and isinstance(json.loads(arguments), list)
        )
    except (ValueError, RecursionError):
        return False


def install_windows_navigation_guard(window):
    """Restrict the pinned pywebview Edge backend to the bundled document."""
    methods = frozenset(window._functions)
    allowed_url = None
    failed = False

    def withhold_initial_page(renderer):
        nonlocal allowed_url, failed
        if renderer == 'edgechromium':
            allowed_url = window.real_url
            window.real_url = None
            if not allowed_url:
                failed = True
                return False

    def attach_policy():
        from System import Action

        form = window.native
        pending_navigation = None

        def close_protected_window():
            nonlocal failed
            failed = True
            window.real_url = None
            if not form.IsDisposed:
                form.BeginInvoke(Action(form.Close))

        def restrict_navigation(_, args):
            nonlocal pending_navigation
            if str(args.Uri).partition('#')[0] != allowed_url:
                args.Cancel = True
            else:
                pending_navigation = args.NavigationId

        def complete_navigation(sender, args):
            nonlocal pending_navigation
            if args.NavigationId != pending_navigation:
                return
            pending_navigation = None
            if args.IsSuccess and str(sender.Source).partition('#')[0] == allowed_url:
                browser.on_navigation_completed(sender, args)

        def restrict_browser_message(sender, args):
            if str(args.Source).partition('#')[0] == allowed_url and _allowed_bridge_message(
                args.get_WebMessageAsJson(), methods,
            ):
                browser.on_script_notify(sender, args)

        def cancel_request(_, args):
            args.Cancel = True

        def suppress_popup(_, args):
            args.Handled = True

        def configure_core(core):
            from Microsoft.Web.WebView2.Core import CoreWebView2PermissionState

            def deny_permission(_, args):
                args.State = CoreWebView2PermissionState.Deny

            # pywebview's default popup handler can open the system browser or navigate this view.
            core.NewWindowRequested -= browser.on_new_window_request
            core.NewWindowRequested += suppress_popup
            core.LaunchingExternalUriScheme += cancel_request
            core.FrameNavigationStarting += cancel_request
            core.PermissionRequested += deny_permission
            window.real_url = allowed_url
            browser.load_url(allowed_url)

        def on_initialized(sender, args):
            if not args.IsSuccess:
                close_protected_window()
                return
            try:
                configure_core(sender.CoreWebView2)
            except Exception:
                logging.exception('Could not configure Compass WebView2 navigation.')
                close_protected_window()

        try:
            browser = form.browser
            control = browser.webview
            control.NavigationStarting += restrict_navigation
            # The upstream callback re-injects the JS bridge even after a canceled navigation.
            control.NavigationCompleted -= browser.on_navigation_completed
            control.NavigationCompleted += complete_navigation
            # The upstream handler otherwise resolves arbitrary names against the bridge object.
            control.WebMessageReceived -= browser.on_script_notify
            control.WebMessageReceived += restrict_browser_message
            if control.CoreWebView2 is not None:
                configure_core(control.CoreWebView2)
            else:
                control.CoreWebView2InitializationCompleted += on_initialized
        except Exception:
            logging.exception('Could not attach Compass WebView2 navigation guards.')
            close_protected_window()

    window.events.initialized += withhold_initial_page
    window.events.before_show += attach_policy
    return lambda: failed
