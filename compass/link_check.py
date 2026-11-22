"""Check an address against the reviewed catalog without visiting it."""

from http.client import HTTPConnection, HTTPException
from ipaddress import ip_address
import json
import re
from socket import AF_INET, SHUT_RDWR, SOCK_STREAM, socket
from sys import audit
from threading import Timer
from time import monotonic
from unicodedata import category
from urllib.parse import urlsplit

from . import catalog


MAX_LINK_LENGTH = 2048
LOCAL_MODEL = 'qwen2.5:0.5b'
_MAX_AI_RESPONSE = 8192
_AI_DEADLINE = 10
_LOCAL_SUFFIXES = frozenset({
    'arpa', 'example', 'home', 'internal', 'invalid', 'lan', 'local', 'localdomain', 'localhost', 'onion', 'test',
})
_DNS_LABEL = re.compile(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?')
_DNS_SUFFIX = re.compile(r'(?:[a-z]{2,63}|xn--[a-z0-9-]+)')
_BAD_URL_CHARACTER = re.compile(r'[\\<>"`]|%(?![0-9a-f]{2})', re.IGNORECASE)


def _blocked(reason):
    return {'status': 'blocked', 'reason': reason}


def inspect_link(value):
    if not isinstance(value, str) or len(value) > MAX_LINK_LENGTH:
        return _blocked('malformed')
    url = value.strip(' ')
    if not url:
        return _blocked('empty')
    if any(char.isspace() or category(char).startswith('C') for char in url) or _BAD_URL_CHARACTER.search(url):
        return _blocked('malformed')

    try:
        parsed = urlsplit(url)
    except ValueError:
        return _blocked('malformed')
    if parsed.scheme != 'https':
        return _blocked('scheme' if parsed.scheme else 'malformed')
    if not parsed.netloc:
        return _blocked('malformed')

    authority = parsed.netloc.lower()
    if '@' in authority:
        return _blocked('credentials')
    if not authority.isascii() or '%' in authority:
        return _blocked('encoded-authority')
    host = parsed.hostname
    if not host:
        return _blocked('malformed')
    display_host = f'[{host}]' if ':' in host else host
    if authority not in (display_host, f'{display_host}:443'):
        return _blocked('port' if authority.startswith(f'{display_host}:') else 'malformed')

    try:
        address = ip_address(host.removesuffix('.'))
    except ValueError:
        labels = host.removesuffix('.').split('.')
        if len(host) > 253 or not all(_DNS_LABEL.fullmatch(label) for label in labels):
            return _blocked('malformed')
        suffix = labels[-1]
        if len(labels) < 2 or suffix in _LOCAL_SUFFIXES or not _DNS_SUFFIX.fullmatch(suffix):
            return _blocked('nonpublic')
    else:
        if not address.is_global or address.is_multicast or address.is_reserved or getattr(address, 'is_site_local', False):
            return _blocked('local-address')

    tail = url.split('://', 1)[1][len(parsed.netloc):]
    if not tail.startswith('/'):
        tail = '/' + tail
    reviewed_url = f'https://{display_host}{tail}'
    for app in catalog.CATALOG:
        if app.url == reviewed_url:
            try:
                destination = catalog.destination(app.id)
            except ValueError:
                return _blocked('malformed')
            if destination != reviewed_url:
                return _blocked('malformed')
            return {'status': 'verified', 'reason': 'publisher-listed', 'publisher': app.name}
    return {'status': 'unverified', 'reason': 'unlisted'}


# The model selects a wording and never receives a pasted address or changes the verdict.
_EXPLANATIONS = {
    'publisher-listed': {
        'en': ('The complete address matches a reviewed publisher page. This check only covers that starting address.',
               'Compare the address in your browser after any redirect and check the file before opening it.'),
        'tr': ('Adresin tamamı incelenmiş yayıncı sayfasıyla eşleşiyor. Denetim bu başlangıç adresini kapsıyor.',
               'Yönlendirmeden sonra tarayıcıdaki adresi karşılaştır ve açmadan önce indirilen dosyayı kontrol et.'),
    },
    'unlisted': {
        'en': ('This exact address has no reviewed catalog entry. HTTPS alone cannot tell you who publishes the page.',
               'Look for the app by name in Compass, or reach the publisher from an address you already trust.'),
        'tr': ('Bu adresin tamamı için katalogda incelenmiş kayıt yok. HTTPS tek başına sayfanın yayıncısını göstermez.',
               'Uygulamayı Compass’ta adıyla ara veya yayıncıya daha önceden güvendiğin bir adresten ulaş.'),
    },
    'empty': {
        'en': ('There is no address to compare with the catalog.',
               'Paste the full HTTPS link you want to check.'),
        'tr': ('Katalogla karşılaştırılacak bir adres girilmedi.',
               'Denetlemek istediğin HTTPS bağlantısını tam olarak yapıştır.'),
    },
    'malformed': {
        'en': ('Compass could not read the address as a complete URL.',
               'Check for missing parts or extra characters and copy the whole address again.'),
        'tr': ('Compass girilen adresi tam bir bağlantı olarak okuyamadı.',
               'Eksik bölüm veya fazladan karakter olup olmadığına bakıp adresi yeniden kopyala.'),
    },
    'scheme': {
        'en': ('The catalog reviews web addresses that start with https://.',
               'Get the full HTTPS address directly from the publisher.'),
        'tr': ('Katalog, https:// ile başlayan web adreslerini inceliyor.',
               'Tam HTTPS adresini doğrudan yayıncı sayfasından al.'),
    },
    'credentials': {
        'en': ('The address can include login data before the @ sign. The site is the part that follows it.',
               'Use the official publisher address without login information embedded in the link.'),
        'tr': ('@ işaretinden önce giriş bilgileri bulunabilir. Gerçek site adı bu işaretten sonra gelir.',
               'Bağlantının içinde giriş bilgisi bulunmayan resmî yayıncı adresini kullan.'),
    },
    'nonpublic': {
        'en': ('The address has no supported public domain name for this check.',
               'Use an HTTPS link with the full domain from the publisher’s public website.'),
        'tr': ('Adreste bu denetime uygun genel bir alan adı bulunamadı.',
               'Yayıncının herkese açık sitesindeki tam alan adını içeren HTTPS adresini kullan.'),
    },
    'port': {
        'en': ('The address includes an unsupported HTTPS port.',
               'Get the exact link from the publisher instead of editing the visible port yourself.'),
        'tr': ('Adres, desteklenmeyen bir HTTPS bağlantı noktası içeriyor.',
               'Bağlantı noktasını kendin değiştirmek yerine bağlantıyı doğrudan yayıncıdan al.'),
    },
    'encoded-authority': {
        'en': ('The address uses an unsupported way of writing its server name.',
               'Look up the publisher by name and copy the official public address from a trusted source.'),
        'tr': ('Adresin sunucu adı bu denetimin desteklemediği bir biçimde yazılmış.',
               'Yayıncıyı adıyla arayıp resmî adresi güvendiğin bir kaynaktan kopyala.'),
    },
    'local-address': {
        'en': ('This IP address is reserved or intended for a local or private network.',
               'For a public publisher page, look for its official HTTPS domain name.'),
        'tr': ('Bu IP adresi ayrılmış ya da yerel veya özel bir ağ için kullanılıyor.',
               'Herkese açık yayıncı sayfasının resmî HTTPS alan adını bul.'),
    },
}

_CHOICES = {'reason': 0, 'next_step': 1}
_CHOICE_SCHEMA = {
    'type': 'object',
    'properties': {'choice': {'type': 'string', 'enum': list(_CHOICES)}},
    'required': ['choice'],
    'additionalProperties': False,
}


def _interrupt_transport(transport):
    try:
        transport.shutdown(SHUT_RDWR)
    except OSError:
        # A response that completed at the deadline may have closed it already.
        pass


class _LocalModelConnection(HTTPConnection):
    def __init__(self):
        super().__init__('127.0.0.1', 11434, timeout=_AI_DEADLINE)

    def connect(self):
        audit('http.client.connect', self, self.host, self.port)
        # The fixed IPv4 address can connect directly without a hostname resolver.
        transport = socket(AF_INET, SOCK_STREAM)
        try:
            transport.settimeout(self.timeout)
            transport.connect((self.host, self.port))
        except OSError:
            transport.close()
            raise
        self.sock = transport


def explain_link(reason, language):
    unavailable = {'status': 'unavailable'}
    if not isinstance(reason, str) or reason not in _EXPLANATIONS or language not in ('en', 'tr'):
        return unavailable
    request = json.dumps({
        'model': LOCAL_MODEL,
        'stream': False,
        'format': _CHOICE_SCHEMA,
        'messages': [
            {'role': 'system', 'content': 'Choose which guidance to display for a fixed link inspection result. '
             'Prefer reason for a concrete URL issue and next_step if more evidence is needed. '
             'Return only JSON with choice reason or next_step.'},
            {'role': 'user', 'content': f'Result reason: {reason}. Language: {language}.'},
        ],
        'options': {'temperature': 0, 'num_predict': 32},
        'keep_alive': '1m',
    }).encode('utf-8')
    deadline = monotonic() + _AI_DEADLINE
    connection = _LocalModelConnection()
    watchdog = None
    try:
        connection.connect()
        remaining = deadline - monotonic()
        if remaining <= 0:
            return unavailable
        # Keep the transport when HTTPConnection transfers it to a closing response.
        watchdog = Timer(remaining, _interrupt_transport, args=(connection.sock,))
        watchdog.daemon = True
        watchdog.start()
        connection.request('POST', '/api/chat', request, {'Content-Type': 'application/json', 'Connection': 'close'})
        with connection.getresponse() as response:
            content_type = response.getheader('Content-Type', '').split(';', 1)[0].strip().lower()
            if response.status != 200 or content_type != 'application/json':
                return unavailable
            data = response.read(_MAX_AI_RESPONSE + 1)
        if monotonic() >= deadline or len(data) > _MAX_AI_RESPONSE:
            return unavailable
        reply = json.loads(data)
        if (not isinstance(reply, dict) or reply.get('done') is not True
                or not isinstance(reply.get('message'), dict) or reply['message'].get('role') != 'assistant'
                or not isinstance(reply['message'].get('content'), str)):
            return unavailable
        choice = json.loads(reply['message']['content'])
        if not isinstance(choice, dict) or set(choice) != {'choice'}:
            return unavailable
        index = _CHOICES.get(choice['choice'])
        if index is None:
            return unavailable
        return {'status': 'ready', 'explanation': _EXPLANATIONS[reason][language][index]}
    except (OSError, HTTPException, TypeError, ValueError, RuntimeError):
        return unavailable
    finally:
        if watchdog is not None:
            watchdog.cancel()
        connection.close()
