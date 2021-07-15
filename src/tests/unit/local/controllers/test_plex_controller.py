import unittest
from unittest.mock import Mock, patch

from local.controllers.plex_controller import MyPlexController, QUALITY_LIST
from tests.utils import patch_path


class TestPlexController(unittest.TestCase):

    def setUp(self) -> None:
        cc = Mock()
        cc.uuid = 'test_cc_id'
        self.pc = MyPlexController(cc)

    def test_transcode_level(self):
        pc = self.pc
        play_mock = Mock()

        with patch(patch_path(pc._start_playing), play_mock):
            with patch(patch_path(pc.build_play_list), Mock()):

                # Test high quality
                pc.transcode({'quality': 'high'})
                self.assertEqual(QUALITY_LIST['1080p'], pc.bitrate)
                play_mock.assert_called()

                # Test medium quality
                pc.transcode({'quality': 'medium'})
                self.assertEqual(QUALITY_LIST['720p'], pc.bitrate)

                # Test maximum quality
                pc.transcode({'quality': 'maximum'})
                self.assertEqual(0, pc.bitrate)

                # Test low quality
                pc.transcode({'quality': 'low'})
                self.assertEqual(QUALITY_LIST['480p'], pc.bitrate)

    def test_transcode_raise(self):
        pc = self.pc
        play_mock = Mock()

        with patch(patch_path(pc._start_playing), play_mock):
            with patch(patch_path(pc.build_play_list), Mock()):

                pc.transcode({'quality': 'medium'})
                self.assertEqual(QUALITY_LIST['720p'], pc.bitrate)

                # Test increase from medium
                pc.transcode({'raise_lower': 'up'})
                self.assertEqual(QUALITY_LIST['1080p'], pc.bitrate)

                # Test increase from high
                pc.transcode({'raise_lower': 'up'})
                self.assertEqual(0, pc.bitrate)

                play_mock.reset_mock()
                pc.transcode({'raise_lower': 'up'})
                self.assertEqual(0, pc.bitrate)
                play_mock.assert_not_called()

    def test_transcode_lower(self):
        pc = self.pc
        play_mock = Mock()

        with patch(patch_path(pc._start_playing), play_mock):
            with patch(patch_path(pc.build_play_list), Mock()):
                pc.transcode({'quality': 'high'})
                self.assertEqual(QUALITY_LIST['1080p'], pc.bitrate)
                play_mock.assert_called()

                # Test low quality
                pc.transcode({'quality': 'low'})
                self.assertEqual(QUALITY_LIST['480p'], pc.bitrate)

                # Test decrease
                pc.transcode({'raise_lower': 'down'})
                self.assertEqual(QUALITY_LIST['320p'], pc.bitrate)

                # Test decrease
                pc.transcode({'raise_lower': 'down'})
                self.assertEqual(QUALITY_LIST['240p'], pc.bitrate)

                # Test decrease
                play_mock.reset_mock()
                pc.transcode({'raise_lower': 'down'})
                self.assertEqual(QUALITY_LIST['240p'], pc.bitrate)
                play_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
