import unittest
from unittest.mock import patch, Mock
from pychromecast.controllers.plex import PlexController

from local.controllers.plex_controller import MyPlexController
from tests import utils
from tests.utils import patch_path

# Test values, change to match your Plex library
TST_SONG_NAME = 'the truth about love'
TST_ARTIST_NAME = 'pink'
TST_ALBUM_NAME = 'bliss'

TST_TV_SHOW_LARGE = 'doctor who'  # Needs over 20 episodes, to test playlist creation
TST_TV_SHOW_LARGE_TITLE = 'the next doctor'

TST_TV_SHOW_SMALL = 'firefly'  # Needs less than 20 episodes, to test playlist creation
TST_TV_SHOW_SMALL_TITLE = 'heart of gold'
TST_TV_SHOW_SMALL_EPISODES = 14


class TestPlexFind(unittest.TestCase):

    def setUp(self):
        utils.load_test_env()

    def test_find_song(self):
        pc = MyPlexController()
        with patch(patch_path(PlexController.stop), Mock()):
            with patch(patch_path(pc.show_media), Mock()):
                pc.find_item({'type': 'song', 'title': TST_SONG_NAME})
                self.assertIsNotNone(pc.get_current_item())
                self.assertEqual('track', pc.get_current_item().TYPE)
                self.assertTrue(TST_SONG_NAME.lower() in pc.get_current_item().title.lower())

    def test_find_artist(self):
        pc = MyPlexController()
        with patch(patch_path(PlexController.stop), Mock()):
            with patch(patch_path(pc.show_media), Mock()):
                pc.find_item({'type': 'artist', 'title': TST_ARTIST_NAME})
                self.assertIsNotNone(pc.get_current_item())
                self.assertEqual('artist', pc.get_current_item().TYPE)
                self.assertTrue(TST_ARTIST_NAME.lower() in pc.get_current_item().title.lower())

    def test_find_album(self):
        pc = MyPlexController()
        with patch(patch_path(PlexController.stop), Mock()):
            with patch(patch_path(pc.show_media), Mock()):
                pc.find_item({'type': 'album', 'title': TST_ALBUM_NAME})
                self.assertIsNotNone(pc.get_current_item())
                self.assertEqual('album', pc.get_current_item().TYPE)
                self.assertTrue(TST_ALBUM_NAME.lower() in pc.get_current_item().title.lower())

    def test_find_show(self):
        pc = MyPlexController()
        with patch(patch_path(PlexController.stop), Mock()):
            with patch(patch_path(pc.show_media), Mock()):
                pc.find_item({'type': 'show', 'title': TST_TV_SHOW_LARGE})
                self.assertIsNotNone(pc.get_current_item())
                self.assertEqual('show', pc.get_current_item().TYPE)
                self.assertTrue(TST_TV_SHOW_LARGE.lower() in pc.get_current_item().title.lower())
                playlist = pc.build_play_list()
                self.assertEqual(21, playlist.playQueueTotalCount)

    def test_find_show2(self):
        pc = MyPlexController()
        with patch(patch_path(PlexController.stop), Mock()):
            with patch(patch_path(pc.show_media), Mock()):
                pc.find_item({'type': 'show', 'title': TST_TV_SHOW_SMALL})
                self.assertIsNotNone(pc.get_current_item())
                self.assertEqual('show', pc.get_current_item().TYPE)
                self.assertTrue(TST_TV_SHOW_SMALL.lower() in pc.get_current_item().title.lower())
                playlist = pc.build_play_list()
                self.assertEqual(TST_TV_SHOW_SMALL_EPISODES, playlist.playQueueTotalCount)

    def test_find_episode(self):
        pc = MyPlexController()
        with patch(patch_path(PlexController.stop), Mock()):
            with patch(patch_path(pc.show_media), Mock()):
                pc.find_item({'type': 'episode', 'title': TST_TV_SHOW_LARGE_TITLE, 'tvshow': TST_TV_SHOW_LARGE})
                self.assertIsNotNone(pc.get_current_item())
                self.assertEqual('episode', pc.get_current_item().TYPE)
                self.assertTrue(TST_TV_SHOW_LARGE_TITLE.lower() in pc.get_current_item().title.lower())
                playlist = pc.build_play_list()
                self.assertEqual(21, playlist.playQueueTotalCount)

    def test_find_episode2(self):
        pc = MyPlexController()
        with patch(patch_path(PlexController.stop), Mock()):
            with patch(patch_path(pc.show_media), Mock()):
                pc.find_item({'type': 'episode', 'title': TST_TV_SHOW_SMALL_TITLE, 'tvshow': TST_TV_SHOW_SMALL})
                self.assertIsNotNone(pc.get_current_item())
                self.assertEqual('episode', pc.get_current_item().TYPE)
                self.assertTrue(TST_TV_SHOW_SMALL_TITLE.lower() in pc.get_current_item().title.lower())
                playlist = pc.build_play_list()
                self.assertEqual(TST_TV_SHOW_SMALL_EPISODES, playlist.playQueueTotalCount)
