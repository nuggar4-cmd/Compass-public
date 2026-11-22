"""GTK and WebKitGTK desktop renderer for the Debian package."""

import json
from threading import Thread

from .bridge import Bridge
from .link_check import MAX_LINK_LENGTH

UI_ORIGIN = 'compass://ui'
START_URI = f'{UI_ORIGIN}/index.html?desktop=1'
ASSETS = {
    START_URI: ('index.html', 'text/html; charset=utf-8'),
    f'{UI_ORIGIN}/styles.css': ('styles.css', 'text/css; charset=utf-8'),
    f'{UI_ORIGIN}/catalog.js': ('catalog.js', 'text/javascript; charset=utf-8'),
    f'{UI_ORIGIN}/app.js': ('app.js', 'text/javascript; charset=utf-8'),
    f'{UI_ORIGIN}/compass-mark.png': ('compass-mark.png', 'image/png'),
}
BRIDGE_SCRIPT = """
(() => {
  if (location.href.split('#', 1)[0] !== 'compass://ui/index.html?desktop=1') return;
  const call = message => window.webkit.messageHandlers.compass.postMessage(message);
  window.pywebview = {api: {
    catalog: () => call(['catalog']),
    app_info: () => call(['app_info']),
    open_official: id => call(['open_official', id]),
    suggest_link: () => call(['suggest_link']),
    inspect_link: value => call(['inspect_link', value]),
    explain_link: (reason, language) => call(['explain_link', reason, language]),
  }};
})();
"""


def show_startup_error(message):
    try:
        import gi

        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
    except (ImportError, ValueError):
        return

    if not Gtk.init_check()[0]:
        return

    dialog = Gtk.MessageDialog(
        modal=True, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE,
        text='Compass could not start', secondary_text=message,
    )
    try:
        dialog.run()
    finally:
        dialog.destroy()


def _startup_failed(message):
    show_startup_error(message)
    raise SystemExit(message)


def _load_assets(ui_directory):
    assets = {}
    for uri, (name, media_type) in ASSETS.items():
        asset = ui_directory / name
        if asset.is_symlink() or not asset.is_file():
            raise OSError(f'Unavailable bundled Compass asset: {name}')
        data = asset.read_bytes()
        if not data:
            raise OSError(f'Empty bundled Compass asset: {name}')
        assets[uri] = (media_type, data)
    return assets


def run(ui_directory, version):
    try:
        import gi

        gi.require_version('Gtk', '3.0')
        gi.require_version('WebKit2', '4.1')
        from gi.repository import Gio, GLib, Gtk, WebKit2
    except (ImportError, ValueError):
        _startup_failed('Install the GTK and WebKitGTK dependencies listed in the Compass README.')

    if not Gtk.init_check()[0]:
        raise SystemExit('Compass needs a graphical desktop session.')

    if (WebKit2.get_major_version(), WebKit2.get_minor_version()) < (2, 40):
        _startup_failed('Compass needs WebKitGTK 2.40 or later. Update WebKitGTK and try again.')

    try:
        assets = _load_assets(ui_directory)
    except OSError:
        _startup_failed('Compass could not load its bundled interface. Reinstall the package or restore the source checkout.')

    def confirm(title, message):
        dialog = Gtk.MessageDialog(
            transient_for=window, modal=True, destroy_with_parent=True,
            message_type=Gtk.MessageType.QUESTION, buttons=Gtk.ButtonsType.OK_CANCEL,
            text=title, secondary_text=message,
        )
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        try:
            return dialog.run() == Gtk.ResponseType.OK
        finally:
            dialog.destroy()

    bridge = Bridge(confirm, lambda url: Gio.AppInfo.launch_default_for_uri(url, None), version=version)
    context = WebKit2.WebContext.new_ephemeral()
    context.get_security_manager().register_uri_scheme_as_secure('compass')

    def serve_asset(request, _data):
        asset = assets.get(request.get_uri())
        if asset is None:
            request.finish_error(GLib.Error.new_literal(Gio.io_error_quark(), 'Compass asset unavailable',
                                                       Gio.IOErrorEnum.NOT_FOUND))
            return
        media_type, data = asset
        stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
        request.finish(stream, len(data), media_type)

    context.register_uri_scheme('compass', serve_asset, None)
    context.connect('download-started', lambda _context, download: download.cancel())
    view = WebKit2.WebView.new_with_context(context)
    view.get_settings().set_property('enable-html5-local-storage', False)
    view.get_settings().set_property('javascript-can-open-windows-automatically', False)

    def navigation_policy(_view, decision, kind):
        if kind == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri() or ''
            if uri.split('#', 1)[0] == START_URI:
                return False
        elif kind != WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
            return False
        decision.ignore()
        return True

    def deny_permission(_view, request):
        request.deny()
        return True

    explanation_pending = False

    def start_explanation(request, value, reply):
        nonlocal explanation_pending
        if explanation_pending:
            reply.return_value(value.new_from_json(value.get_context(), '{"status":"unavailable"}'))
            return

        # WebKit's boxed copy retains the pending reply beyond the signal handler.
        held_reply = reply.copy()
        value_type = type(value)
        reply_context = value.get_context()

        def finish(result):
            nonlocal explanation_pending
            explanation_pending = False
            held_reply.return_value(value_type.new_from_json(reply_context, json.dumps(result)))
            return GLib.SOURCE_REMOVE

        def explain():
            GLib.idle_add(finish, bridge.explain_link(request[1], request[2]))

        explanation_pending = True
        try:
            Thread(target=explain, daemon=True).start()
        except RuntimeError:
            finish({'status': 'unavailable'})

    def handle_message(_manager, value, reply):
        try:
            data = value.to_json(0)
            origin = (view.get_uri() or '').split('#', 1)[0]
            if not data or len(data) > MAX_LINK_LENGTH * 12 + 64 or origin != START_URI:
                raise ValueError('Invalid Compass request')
            request = json.loads(data)
            if not isinstance(request, list):
                raise ValueError('Invalid Compass request')
            if len(request) == 2 and request[0] == 'inspect_link':
                result = bridge.inspect_link(request[1])
            elif len(data) > 256:
                raise ValueError('Invalid Compass request')
            elif len(request) == 3 and request[0] == 'explain_link':
                start_explanation(request, value, reply)
                return True
            elif request == ['catalog']:
                result = bridge.catalog()
            elif request == ['app_info']:
                result = bridge.app_info()
            elif request == ['suggest_link']:
                result = bridge.suggest_link()
            elif len(request) == 2 and request[0] == 'open_official':
                result = bridge.open_official(request[1])
            else:
                raise ValueError('Unknown Compass request')
            reply.return_value(value.new_from_json(value.get_context(), json.dumps(result)))
        except (TypeError, ValueError):
            reply.return_error_message('Invalid Compass request')
        return True

    view.connect('decide-policy', navigation_policy)
    view.connect('permission-request', deny_permission)
    manager = view.get_user_content_manager()
    manager.connect('script-message-with-reply-received::compass', handle_message)
    if not manager.register_script_message_handler_with_reply('compass', None):
        _startup_failed('Could not start the Compass desktop connection.')
    manager.add_script(WebKit2.UserScript.new(
        BRIDGE_SCRIPT, WebKit2.UserContentInjectedFrames.TOP_FRAME,
        WebKit2.UserScriptInjectionTime.START, [f'{UI_ORIGIN}/*'], None,
    ))

    window = Gtk.Window(title='Compass')
    window.set_default_size(1100, 740)
    window.set_size_request(600, 480)
    window.set_icon_name('io.github.nuggar4_cmd.Compass')
    window.connect('destroy', Gtk.main_quit)
    window.add(view)
    view.load_uri(START_URI)
    window.show_all()
    Gtk.main()
