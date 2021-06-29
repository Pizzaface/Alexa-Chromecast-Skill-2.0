import unittest
import time
from local.controllers.chromecast_controller import APP_PLEX_ID, APP_YOUTUBE_ID
from tests import utils

# Test values, change to match your Plex library
TST_CHROMECAST_NAME = 'Living Room TV'
TST_MOVIE_NAME = 'guardians of the galaxy'  # Needs to have subtitles and at least 2 audio streams
TST_ARTIST_NAME = 'pink'
TST_SHOW_NAME = 'mythic quest'
TST_EPISODE_TITLE = 'breaking brad'  # Needs to be the name or part of a name of one episode

TST_EPISODE_SEASON = 2  # Provide a season number and episode number for a particular episode
TST_EPISODE_NUMBER = 4


def wait_till_playing(pc):
    max_time = 30
    while not pc.status.player_is_playing:
        max_time -= 1
        time.sleep(1)
        if max_time == 0:
            raise TimeoutError()


class TestPlexCommands(unittest.TestCase):

    def setUp(self):
        utils.load_test_env()
        from local.main import ChromecastController
        self.chromecast_controller = ChromecastController()
        self.cc_name = TST_CHROMECAST_NAME

    def tearDown(self):
        self.chromecast_controller.chromecast_collector.stop()

    def test_open(self):
        self.chromecast_controller.handle_command(self.cc_name, 'open', {'app': 'plex'})
        time.sleep(20)
        cast = self.chromecast_controller.get_chromecast(self.cc_name).cast
        self.assertEqual(APP_PLEX_ID, cast.app_id)

        self.chromecast_controller.handle_command(self.cc_name, 'open', {'app': 'youtube'})
        time.sleep(20)
        self.assertEqual(APP_YOUTUBE_ID, cast.app_id)

    def test_play_movie(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self.chromecast_controller.handle_command(self.cc_name, 'play_media',
                                                      {'play': 'find', 'title': TST_MOVIE_NAME, 'app': 'plex'})
            item = pc.get_current_item()
            self.assertEqual('movie', item.TYPE)
            self.assertTrue(TST_MOVIE_NAME.lower() in item.title.lower())
            time.sleep(5)
            self.chromecast_controller.handle_command(self.cc_name, 'play')
            wait_till_playing(pc)

            self.chromecast_controller.handle_command(self.cc_name, 'restart')
            time.sleep(5)

            # Test Pause
            self.assertFalse(pc.status.player_is_paused)
            self.chromecast_controller.handle_command(self.cc_name, 'pause')
            time.sleep(5)
            self.assertTrue(pc.status.player_is_paused)

            self.chromecast_controller.handle_command(self.cc_name, 'play')
            time.sleep(10)
            self.assertFalse(pc.status.player_is_paused)

            # Test Fast Forward worked
            current_time = pc.status.current_time
            self.chromecast_controller.handle_command(self.cc_name, 'seek', {'direction': 'forward', 'duration': 'PT2M'})
            time.sleep(10)
            self.assertGreater(pc.status.current_time, current_time + 30)

            # Test Rewind worked
            current_time = pc.status.current_time
            self.chromecast_controller.handle_command(self.cc_name, 'seek', {'direction': 'back', 'duration': 'PT1M'})
            time.sleep(10)
            self.assertLess(pc.status.current_time, current_time - 30)

            # Turn on subtitles
            self.assertFalse(next((sub for sub in pc.status.current_subtitle_tracks if sub.selected), False))
            self.chromecast_controller.handle_command(self.cc_name, 'subtitle_on')
            time.sleep(5)
            self.assertTrue(pc.status.media_custom_data['subtitleStreamID'] != '0')

            # Turn off subtitles
            self.chromecast_controller.handle_command(self.cc_name, 'subtitle_off')
            time.sleep(5)
            self.assertTrue(pc.status.media_custom_data['subtitleStreamID'] == '0')

            # Change audio stream
            current_audio = pc.status.media_custom_data['audioStreamID']
            self.chromecast_controller.handle_command(self.cc_name, 'change-audio')
            time.sleep(5)
            self.assertNotEqual(current_audio, pc.status.media_custom_data['audioStreamID'])
        finally:
            self.chromecast_controller.handle_command(self.cc_name, 'stop')
            time.sleep(5)
            self.assertFalse(pc.status.player_is_playing)

    def test_play_artist(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self.chromecast_controller.handle_command(self.cc_name, 'play_media',
                                                      {'play': 'find', 'type': 'artist', 'title': TST_ARTIST_NAME,
                                                       'app': 'plex'})
            item = pc.get_current_item()
            self.assertEqual('artist', item.TYPE)
            self.assertTrue(TST_ARTIST_NAME.lower() in item.title.lower())

            time.sleep(5)
            self.assertFalse(pc.status.player_is_playing)

            self.chromecast_controller.handle_command(self.cc_name, 'play')
            wait_till_playing(pc)
            self.assertTrue(pc.status.player_is_playing)

            self.chromecast_controller.handle_command(self.cc_name, 'set_volume', {'volume': 5})
            time.sleep(5)
            self.assertEqual(0.5, cc.cast.status.volume_level)

            self.chromecast_controller.handle_command(self.cc_name, 'set_volume', {'jump': 'up'})
            time.sleep(5)
            self.assertEqual(0.6, round(cc.cast.status.volume_level*10)/10)

            self.chromecast_controller.handle_command(self.cc_name, 'set_volume', {'jump': 'down'})
            time.sleep(5)
            self.assertEqual(0.5, round(cc.cast.status.volume_level*10)/10)

            self.assertFalse(cc.cast.status.volume_muted)
            self.chromecast_controller.handle_command(self.cc_name, 'mute')
            time.sleep(5)
            self.assertTrue(cc.cast.status.volume_muted)

            self.chromecast_controller.handle_command(self.cc_name, 'unmute')
            time.sleep(5)
            self.assertFalse(cc.cast.status.volume_muted)

            self.chromecast_controller.handle_command(self.cc_name, 'shuffle_off')
            time.sleep(5)

            current_content_id = pc.status.content_id
            self.chromecast_controller.handle_command(self.cc_name, 'shuffle_on')
            time.sleep(5)
            # There is a risk of collision on this test, it may randomly choose the first item...
            self.assertNotEqual(current_content_id, pc.status.content_id)

            self.chromecast_controller.handle_command(self.cc_name, 'shuffle_off')
            time.sleep(5)
            self.assertEqual(current_content_id, pc.status.content_id)

            self.chromecast_controller.handle_command(self.cc_name, 'play_next')
            time.sleep(5)
            self.assertNotEqual(current_content_id, pc.status.content_id)

            self.chromecast_controller.handle_command(self.cc_name, 'play_previous')
            time.sleep(5)
            self.assertEqual(current_content_id, pc.status.content_id)
        finally:
            self.chromecast_controller.handle_command(self.cc_name, 'stop')
            time.sleep(5)
            self.assertFalse(pc.status.player_is_playing)

    def test_play_show(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self.chromecast_controller.handle_command(self.cc_name, 'play_media',
                                                      {'play': 'find', 'type': 'show', 'title': TST_SHOW_NAME,
                                                       'app': 'plex'})
            item = pc.get_current_item()
            self.assertEqual('show', item.TYPE)
            self.assertTrue(TST_SHOW_NAME.lower() in item.title.lower())
            time.sleep(5)

            self.assertFalse(pc.status.player_is_playing)
            self.chromecast_controller.handle_command(self.cc_name, 'play')
            wait_till_playing(pc)
            self.assertTrue(pc.status.player_is_playing)

            # Test play previous episode
            self.chromecast_controller.handle_command(self.cc_name, 'restart')
            time.sleep(5)
            current_episode = pc.status.episode
            self.chromecast_controller.handle_command(self.cc_name, 'play_previous')
            time.sleep(10)
            self.assertEqual(current_episode - 1, pc.status.episode)

            # Test play next episode
            self.chromecast_controller.handle_command(self.cc_name, 'play_next')
            time.sleep(10)
            self.assertEqual(current_episode, pc.status.episode)
        finally:
            self.chromecast_controller.handle_command(self.cc_name, 'stop')
            time.sleep(5)
            self.assertFalse(pc.status.player_is_playing)

    def test_play_episode_by_title(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            # Retrieve by title
            self.chromecast_controller.handle_command(self.cc_name, 'play_media',
                                                      {'play': 'find', 'type': 'episode', 'tvshow': TST_SHOW_NAME,
                                                       'title': TST_EPISODE_TITLE, 'app': 'plex'})
            item = pc.get_current_item()
            self.assertEqual('episode', item.TYPE)
            self.assertTrue(TST_EPISODE_TITLE.lower() in item.title.lower())
            self.assertTrue(TST_SHOW_NAME.lower() in item.show().title.lower())
            time.sleep(5)

            self.assertFalse(pc.status.player_is_playing)
            self.chromecast_controller.handle_command(self.cc_name, 'play')
            wait_till_playing(pc)
            self.assertTrue(pc.status.player_is_playing)

            # Test play previous episode
            self.chromecast_controller.handle_command(self.cc_name, 'restart')
            time.sleep(5)
            current_episode = pc.status.episode
            self.chromecast_controller.handle_command(self.cc_name, 'play_previous')
            time.sleep(10)
            self.assertEqual(current_episode - 1, pc.status.episode)

            # Test play next episode
            self.chromecast_controller.handle_command(self.cc_name, 'play_next')
            time.sleep(10)
            self.assertEqual(current_episode, pc.status.episode)

        finally:
            self.chromecast_controller.handle_command(self.cc_name, 'stop')
            time.sleep(5)
            self.assertFalse(pc.status.player_is_playing)

    def test_play_episode_by_number(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            # Retrieve by season and episode
            self.chromecast_controller.handle_command(self.cc_name, 'play_media',
                                                      {'play': 'find', 'type': 'episode', 'seasnum': TST_EPISODE_SEASON,
                                                       'epnum': TST_EPISODE_NUMBER, 'tvshow': TST_SHOW_NAME,
                                                       'app': 'plex'})

            item = pc.get_current_item()
            self.assertEqual('episode', item.TYPE)
            self.assertEqual(TST_EPISODE_SEASON, item.seasonNumber)
            self.assertEqual(TST_EPISODE_NUMBER, item.episodeNumber)
            self.assertTrue(TST_SHOW_NAME.lower() in item.show().title.lower())
            time.sleep(5)

            self.assertFalse(pc.status.player_is_playing)
            self.chromecast_controller.handle_command(self.cc_name, 'play')
            wait_till_playing(pc)
            self.assertTrue(pc.status.player_is_playing)

            # Test play previous episode
            self.chromecast_controller.handle_command(self.cc_name, 'restart')
            time.sleep(5)
            current_episode = pc.status.episode
            self.chromecast_controller.handle_command(self.cc_name, 'play_previous')
            time.sleep(10)
            self.assertEqual(current_episode - 1, pc.status.episode)

            # Test play next episode
            self.chromecast_controller.handle_command(self.cc_name, 'play_next')
            time.sleep(10)
            self.assertEqual(current_episode, pc.status.episode)

        finally:
            self.chromecast_controller.handle_command(self.cc_name, 'stop')
            time.sleep(5)
            self.assertFalse(pc.status.player_is_playing)
