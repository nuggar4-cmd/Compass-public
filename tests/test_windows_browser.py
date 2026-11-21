import os
import unittest
from unittest.mock import Mock, call, patch

from compass.bridge import Bridge
from compass.catalog import destination
from compass.windows import launch_default_browser


class WindowsBrowserTests(unittest.TestCase):
    def test_default_https_handler_receives_the_approved_url(self):
        with patch.dict(os.environ, {'BROWSER': 'other-browser'}), patch.object(
            os, 'startfile', create=True,
        ) as startfile, patch('webbrowser.open') as browser_override:
            url = destination('7zip')
            self.assertTrue(launch_default_browser(url))
            startfile.assert_called_once_with(url)
            browser_override.assert_not_called()

    def test_cancellation_and_shell_failure_allow_a_fresh_attempt(self):
        confirm = Mock(side_effect=[False, True, True])
        bridge = Bridge(confirm, launch_default_browser)
        with patch.object(os, 'startfile', side_effect=[OSError('Shell failure'), None], create=True) as startfile:
            self.assertFalse(bridge.open_official('7zip')['ok'])
            startfile.assert_not_called()

            result = bridge.open_official('7zip')
            self.assertEqual(result, {'ok': False, 'message': 'Could not open your browser. Please try again.'})
            self.assertTrue(bridge.open_official('7zip')['ok'])

        self.assertEqual(confirm.call_count, 3)
        self.assertEqual(startfile.call_args_list, [call(destination('7zip'))] * 2)
