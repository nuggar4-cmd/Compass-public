from dataclasses import replace
from http.client import HTTPException
import json
from socket import SHUT_RDWR
import unittest
from unittest.mock import patch

from compass import catalog, link_check
from compass.bridge import Bridge


class LinkInspectionTests(unittest.TestCase):
    def test_verified_exact_address_with_normalized_host_and_default_port(self):
        result = link_check.inspect_link('  HTTPS://WWW.7-ZIP.ORG:443  ')
        self.assertEqual(result, {
            'status': 'verified', 'reason': 'publisher-listed', 'publisher': '7-Zip',
        })

    def test_every_reviewed_catalog_address_is_verified(self):
        for app in catalog.CATALOG:
            with self.subTest(app=app.id):
                self.assertEqual(link_check.inspect_link(catalog.destination(app.id))['status'], 'verified')

    def test_catalog_match_must_agree_with_the_native_destination(self):
        publisher = catalog.BY_ID['7zip']
        replacement = replace(publisher, url='https://www.7-zip.org/other.html')
        with patch.dict(catalog.BY_ID, {'7zip': replacement}):
            self.assertEqual(link_check.inspect_link(publisher.url), {'status': 'blocked', 'reason': 'malformed'})

    def test_same_publisher_domain_with_different_suffix_stays_unverified(self):
        addresses = (
            'https://www.7-zip.org/other', 'https://www.7-zip.org/?',
            'https://www.7-zip.org/?a=b', 'https://www.7-zip.org/#',
            'https://www.7-zip.org/#other', 'https://www.7-zip.org./',
            'https://www.7-zip.org.example.com/', 'https://example.com/',
        )
        for address in addresses:
            with self.subTest(address=address):
                self.assertEqual(link_check.inspect_link(address), {'status': 'unverified', 'reason': 'unlisted'})

    def test_blocks_unsupported_or_private_addresses(self):
        examples = (
            (None, 'malformed'), ('   ', 'empty'), ('www.7-zip.org/', 'malformed'),
            ('https:///www.7-zip.org', 'malformed'), ('https://example.com/white space', 'malformed'),
            ('https://example.com/\u202e', 'malformed'), ('https://example.com/\n', 'malformed'),
            ('https://example.com/path%ff%', 'malformed'), ('https://example.com/' + 'a' * 2048, 'malformed'),
            ('http://www.7-zip.org/', 'scheme'), ('file:///home/test/sample.txt', 'scheme'),
            ('https://sample@www.7-zip.org/', 'credentials'), ('https://www.7-zip.org:80/', 'port'),
            ('https://www.7-zip.org:/', 'port'), ('https://example%2ecom/', 'encoded-authority'),
            ('https://örnek.com/', 'encoded-authority'), ('https://localhost/', 'nonpublic'),
            ('https://example.local/', 'nonpublic'), ('https://127.0.0.1/', 'local-address'),
            ('https://192.168.0.2/', 'local-address'), ('https://[::1]/', 'local-address'),
            ('https://[fe80::3]/', 'local-address'), ('https://[::1]invalid/', 'malformed'),
        )
        for address, reason in examples:
            with self.subTest(address=address):
                self.assertEqual(link_check.inspect_link(address), {'status': 'blocked', 'reason': reason})

    def test_inspection_cannot_request_network_or_open_a_site(self):
        with patch.object(link_check, 'HTTPConnection') as connection:
            bridge = Bridge(lambda *_: self.fail('Confirmation was opened'),
                            lambda *_: self.fail('Address was opened'))
            self.assertEqual(bridge.inspect_link('https://example.com/')['status'], 'unverified')
            connection.assert_not_called()


class LocalExplanationTests(unittest.TestCase):
    def setUp(self):
        self.connection_class = self.enterContext(patch.object(link_check, 'HTTPConnection'))
        self.watchdog_class = self.enterContext(patch.object(link_check, 'Timer'))
        self.connection = self.connection_class.return_value
        self.reply = self.connection.getresponse.return_value.__enter__.return_value
        self.reply.status = 200
        self.reply.getheader.return_value = 'application/json; charset=utf-8'

    def set_message(self, content):
        self.reply.read.return_value = json.dumps({
            'done': True, 'message': {'role': 'assistant', 'content': content},
        }).encode('utf-8')

    def test_explanation_has_fixed_loopback_request_and_only_vetted_wording(self):
        self.set_message('{"choice":"next_step"}')
        bridge = Bridge(lambda *_: self.fail('Confirmation was opened'))
        result = bridge.explain_link('unlisted', 'tr')
        self.assertEqual(result, {
            'status': 'ready',
            'explanation': 'Uygulamayı Compass’ta adıyla ara veya yayıncıya daha önceden güvendiğin bir adresten ulaş.',
        })
        self.connection_class.assert_called_once_with('127.0.0.1', 11434, timeout=10)
        self.connection.connect.assert_called_once_with()
        method, route, raw, headers = self.connection.request.call_args.args
        self.assertEqual((method, route), ('POST', '/api/chat'))
        self.assertEqual(headers['Content-Type'], 'application/json')
        request = json.loads(raw)
        self.assertEqual(request['model'], 'qwen2.5:0.5b')
        self.assertFalse(request['stream'])
        self.assertNotIn('tools', request)
        self.assertEqual(request['messages'][1]['content'], 'Result reason: unlisted. Language: tr.')
        self.reply.read.assert_called_once_with(link_check._MAX_AI_RESPONSE + 1)
        self.watchdog_class.return_value.cancel.assert_called_once_with()
        self.connection.close.assert_called_once()

    def test_arbitrary_reason_and_language_cannot_reach_the_model(self):
        for reason, language in (
            ('https://example.com/path?private=value', 'tr'), ('unlisted', 'other'),
            (None, 'en'), ([], 'tr'), ('unlisted', ['en']),
        ):
            with self.subTest(reason=reason, language=language):
                self.assertEqual(link_check.explain_link(reason, language), {'status': 'unavailable'})
        self.connection_class.assert_not_called()

    def test_model_output_cannot_replace_the_explanation_or_verdict(self):
        for content in (
            'plain text', '{"choice":"Go to another address"}', '{"choice":"reason","verdict":"verified"}',
            '{"choice":[]}', '[]',
        ):
            with self.subTest(content=content):
                self.set_message(content)
                self.assertEqual(link_check.explain_link('unlisted', 'en'), {'status': 'unavailable'})

    def test_unavailable_or_oversized_local_response_falls_back(self):
        self.set_message('{"choice":"reason"}')
        for status in (302, 404, 500):
            with self.subTest(status=status):
                self.reply.status = status
                self.assertEqual(link_check.explain_link('unlisted', 'en'), {'status': 'unavailable'})
        self.reply.read.assert_not_called()
        self.reply.status = 200
        self.reply.read.return_value = b' ' * (link_check._MAX_AI_RESPONSE + 1)
        self.assertEqual(link_check.explain_link('unlisted', 'en'), {'status': 'unavailable'})
        for error in (ConnectionRefusedError, TimeoutError, HTTPException):
            with self.subTest(error=error):
                self.connection.request.side_effect = error
                self.assertEqual(link_check.explain_link('unlisted', 'en'), {'status': 'unavailable'})

    def test_deadline_interrupts_the_transport_even_after_response_detaches_it(self):
        transport = self.connection.sock
        response_context = self.connection.getresponse.return_value

        def detach_response():
            self.connection.sock = None
            return response_context

        def interrupt_read(_size):
            _, interrupt = self.watchdog_class.call_args.args
            interrupt(*self.watchdog_class.call_args.kwargs['args'])
            raise TimeoutError

        self.connection.getresponse.side_effect = detach_response
        self.reply.read.side_effect = interrupt_read
        self.assertEqual(link_check.explain_link('unlisted', 'en'), {'status': 'unavailable'})
        transport.shutdown.assert_called_once_with(SHUT_RDWR)
        self.watchdog_class.return_value.start.assert_called_once_with()
        self.watchdog_class.return_value.cancel.assert_called_once_with()
        self.connection.close.assert_called_once_with()

    def test_successful_response_at_total_deadline_falls_back(self):
        self.set_message('{"choice":"reason"}')
        with patch.object(link_check, 'monotonic', side_effect=(100, 102, 110)):
            self.assertEqual(link_check.explain_link('unlisted', 'en'), {'status': 'unavailable'})
        self.assertEqual(self.watchdog_class.call_args.args[0], 8)

    def test_only_one_explanation_can_use_the_provider(self):
        self.set_message('{"choice":"reason"}')
        bridge = Bridge(lambda *_: self.fail('Confirmation was opened'))
        with bridge._explaining:
            self.assertEqual(bridge.explain_link('unlisted', 'en'), {'status': 'unavailable'})
        self.connection_class.assert_not_called()
        self.assertEqual(bridge.explain_link('unlisted', 'en')['status'], 'ready')
