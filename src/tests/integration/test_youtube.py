import time
import unittest

from tests.integration.helpers import TestChromecast


class TestYoutube(TestChromecast):

    def test_playlist(self):
        try:
            self.assertFalse(self.mc.is_playing)
            self._command('play_media',
                           {'play': 'find',
                            'title': '90s hits',
                            'type': 'playlist',
                            'app': 'youtube'})
            self._wait_till_playing()

            # Test next
            current_content_id = self.mc.status.content_id
            self._command('play_next', {})
            self._wait_till_event(lambda: current_content_id != self.mc.status.content_id)
            self.assertNotEqual(current_content_id, self.mc.status.content_id)

            # Test previous
            self._wait_till_playing()
            new_content_id = self.mc.status.content_id
            self._command('play_previous', {})
            self._wait_till_event(lambda: new_content_id != self.mc.status.content_id)
            self.assertEqual(current_content_id, self.mc.status.content_id)

            # Test pause
            self._wait_till_playing()
            self.assertFalse(self.mc.is_paused)
            self._command('pause', {})
            self._wait_till_paused()

            # Test play
            self._command('play', {})
            self._wait_till_playing()

            # Test Fast Forward
            current_time = self.mc.status.current_time
            self._command('fast_forward', {'duration': 'PT1M'})
            self._wait_till_event(lambda: self.mc.status.current_time > current_time + 30)
            self.assertGreater(self.mc.status.current_time, current_time + 30)

            # Test Rewind
            current_time = self.mc.status.current_time
            self._command('rewind', {'duration': 'PT1M'})
            self._wait_till_event(lambda: self.mc.status.current_time < current_time - 30)
            self.assertLess(self.mc.status.current_time, current_time - 30)

        finally:
            self._stop()

    def test_play_trailer(self):
        try:
            self.assertFalse(self.mc.is_playing)
            self._command('play_media', {
                'title': 'The Matrix',
                'type': 'trailer',
                'app': 'youtube'})
            self._wait_till_playing()

        finally:
            self._stop()

    def test_search(self):
        try:
            self.assertFalse(self.mc.is_playing)
            self._command('play_media', {'play': 'find',
                                          'title': 'macklemore',
                                          'app': 'youtube'})
            self._wait_till_playing()

            # Test next
            current_content_id = self.mc.status.content_id
            self._command('play_next')
            self._wait_till_event(lambda: current_content_id != self.mc.status.content_id)
            self.assertNotEqual(current_content_id, self.mc.status.content_id)

            # Test previous
            self._wait_till_playing()
            new_content_id = self.mc.status.content_id
            self._command('play_previous')
            self._wait_till_event(lambda: new_content_id != self.mc.status.content_id)
            self.assertEqual(current_content_id, self.mc.status.content_id)

            # Test pause
            self._wait_till_playing()
            self.assertFalse(self.mc.is_paused)
            self._command('pause')
            self._wait_till_paused()

        finally:
            self._stop()

    def test_shuffle(self):
        try:
            self.assertFalse(self.mc.is_playing)
            self._command('play_media', {'play': 'find',
                                          'title': 'macklemore',
                                          'app': 'youtube'})
            self._wait_till_playing()
            current_content_id = self.mc.status.content_id

            self._command('shuffle_on')
            self._wait_till_event(lambda: current_content_id != self.mc.status.content_id)
            self.assertNotEqual(current_content_id, self.mc.status.content_id)

            self._command('shuffle_off')
            self._wait_till_event(lambda: current_content_id == self.mc.status.content_id)
            self.assertEqual(current_content_id, self.mc.status.content_id)
        finally:
            self._stop()


if __name__ == '__main__':
    unittest.main()
