"""GTK and WebKitGTK desktop renderer for the Debian package."""

import json
from urllib.parse import urlsplit

from .bridge import Bridge

UI_ORIGIN = 'compass://ui'
START_URI = f'{UI_ORIGIN}/index.html?desktop=1'
MEDIA_TYPES = {
    '/index.html': 'text/html; charset=utf-8',
    '/styles.css': 'text/css; charset=utf-8',
    '/catalog.js': 'text/javascript; charset=utf-8',
    '/app.js': 'text/javascript; charset=utf-8',
}
BRIDGE_SCRIPT = """
(() => {
  if (location.href.split('#', 1)[0] !== 'compass://ui/index.html?desktop=1') return;
  const call = message => window.webkit.messageHandlers.compass.postMessage(message);
  window.pywebview = {api: {
    catalog: () => call(['catalog']),
    app_info: () => call(['app_info']),
    open_official: id => call(['open_official', id]),
  }};
})();
"""


def run(ui_directory, version):
    try:
        import gi

        gi.require_version('Gtk', '3.0')
        gi.require_version('WebKit2', '4.1')
        from gi.repository import Gio, GLib, Gtk, WebKit2
    except (ImportError, ValueError) as error:
        raise SystemExit('Install the GTK and WebKitGTK dependencies listed in the Compass README.') from error

    if not Gtk.init_check()[0]:
        raise SystemExit('Compass needs a graphical desktop session.')

    window = Gtk.Window(title='Compass')
    window.set_default_size(1100, 740)
    window.set_size_request(600, 480)
    window.set_icon_name('io.github.nuggar4_cmd.Compass')
    window.connect('destroy', Gtk.main_quit)

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
        uri = urlsplit(request.get_uri())
        content_type = MEDIA_TYPES.get(uri.path)
        if uri.netloc == 'ui' and content_type:
            try:
                data = (ui_directory / uri.path[1:]).read_bytes()
                request.finish(Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data)), len(data), content_type)
                return
            except OSError:
                pass
        request.finish_error(GLib.Error.new_literal(Gio.io_error_quark(), 'Compass asset unavailable',
                                                   Gio.IOErrorEnum.NOT_FOUND))

    context.register_uri_scheme('compass', serve_asset, None)
    context.connect('download-started', lambda _context, download: download.cancel())
    view = WebKit2.WebView.new_with_context(context)
    view.get_settings().set_property('enable-html5-local-storage', False)
    view.get_settings().set_property('javascript-can-open-windows-automatically', False)

    def navigation_policy(_view, decision, kind):
        if kind == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            if uri.split('#', 1)[0] == START_URI:
                return False
        elif kind != WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
            return False
        decision.ignore()
        return True

    def deny_permission(_view, request):
        request.deny()
        return True

    def handle_message(_manager, value, reply):
        try:
            data = value.to_json(0)
            origin = (view.get_uri() or '').split('#', 1)[0]
            if not data or len(data) > 256 or origin != START_URI:
                raise ValueError('Invalid Compass request')
            request = json.loads(data)
            if request == ['catalog']:
                result = bridge.catalog()
            elif request == ['app_info']:
                result = bridge.app_info()
            elif isinstance(request, list) and len(request) == 2 and request[0] == 'open_official':
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
        raise SystemExit('Could not start the Compass desktop connection.')
    manager.add_script(WebKit2.UserScript.new(
        BRIDGE_SCRIPT, WebKit2.UserContentInjectedFrames.TOP_FRAME,
        WebKit2.UserScriptInjectionTime.START, [f'{UI_ORIGIN}/*'], None,
    ))

    window.add(view)
    view.load_uri(START_URI)
    window.show_all()
    Gtk.main()
