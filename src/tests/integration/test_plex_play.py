import time

from local.controllers.chromecast_controller import APP_PLEX_ID, APP_YOUTUBE_ID
from local.controllers.plex_controller import MyPlexController
from tests.integration.helpers import TestChromecast

# Test values, change to match your Plex library
TST_MOVIE_NAME = 'guardians of the galaxy'  # Needs to have subtitles and at least 2 audio streams
TST_ARTIST_NAME = 'pink'
TST_SHOW_NAME = 'mythic quest'
TST_EPISODE_TITLE = 'breaking brad'  # Needs to be the name or part of a name of one episode

TST_EPISODE_SEASON = 2  # Provide a season number and episode number for a particular episode
TST_EPISODE_NUMBER = 4


class TestPlexCommands(TestChromecast):

    def get_playing_bitrate(self, pc: MyPlexController):
        # On occasion bitrate is not found
        bitrate = None
        for _ in range(10):
            bitrate = pc.status.media_custom_data['bitrate'] if 'bitrate' in pc.status.media_custom_data else None
            if bitrate:
                break
            time.sleep(1)
        return bitrate

    def test_open(self):
        cast = self.chromecast_controller.get_chromecast(self.cc_name).cast

        self._command('open', {'app': 'plex'})
        self._wait_till_event(lambda: cast.app_id == APP_PLEX_ID)
        self.assertEqual(APP_PLEX_ID, cast.app_id)

        self._command('open', {'app': 'youtube'})
        self._wait_till_event(lambda: cast.app_id == APP_YOUTUBE_ID)
        self.assertEqual(APP_YOUTUBE_ID, cast.app_id)

    def test_play_movie(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self._command('play_media',
                          {'play': 'find', 'title': TST_MOVIE_NAME, 'app': 'plex'})

            item = pc.current_item
            self.assertEqual('movie', item.TYPE)
            self.assertTrue(TST_MOVIE_NAME.lower() in item.title.lower())
            self._command('play')
            self._wait_till_playing()

            current_time = pc.status.current_time
            self._command('restart')
            self._wait_till_playing()
            self._wait_till_event(lambda: pc.status.current_time < 10)

            # Test Pause
            self.assertFalse(pc.status.player_is_paused)
            current_time = pc.status.current_time
            self._command('pause')
            self._wait_till_paused()

            self._command('play')
            self._wait_till_playing()
            self.assertLessEqual(current_time, pc.status.current_time)

            # Test Fast Forward worked
            current_time = pc.status.current_time
            self._command('fast_forward', {'duration': 'PT2M'})
            self._wait_till_event(lambda: pc.status.current_time > current_time + 30)
            self.assertGreater(pc.status.current_time, current_time + 30)

            # Test Rewind worked
            current_time = pc.status.current_time
            self._command('rewind', {'duration': 'PT1M'})
            self._wait_till_event(lambda: pc.status.current_time < current_time - 30)
            self.assertLess(pc.status.current_time, current_time - 30)

            # Turn on subtitles
            self.assertFalse(next((sub for sub in pc.status.current_subtitle_tracks if sub.selected), False))
            self._command('subtitle_on')
            self.assertTrue(pc.status.media_custom_data['subtitleStreamID'] != '0')

            # Turn off subtitles
            self._command('subtitle_off')
            self.assertTrue(pc.status.media_custom_data['subtitleStreamID'] == '0')

            # Change audio stream
            current_audio = pc.status.media_custom_data['audioStreamID']
            self._command('change-audio')
            self._wait_till_event(lambda: current_audio != pc.status.media_custom_data['audioStreamID'])
            self.assertNotEqual(current_audio, pc.status.media_custom_data['audioStreamID'])

            # Play for 20 seconds
            time.sleep(20)

            # Test resume
            self._stop()
            self._command('play')
            self._wait_till_playing()
            self.assertLess(20, pc.status.current_time)
            time.sleep(10)

        finally:
            self._stop()

    def test_play_artist(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self._command('play_media',
                          {'play': 'find', 'type': 'artist', 'title': TST_ARTIST_NAME,
                           'app': 'plex'})
            item = pc.current_item
            self.assertEqual('artist', item.TYPE)
            self.assertTrue(TST_ARTIST_NAME.lower() in item.title.lower())
            self.assertFalse(pc.status.player_is_playing)

            self._command('play')
            self._wait_till_playing()
            self.assertTrue(pc.status.player_is_playing)

            self._command('set_volume', {'volume': 5})
            self.assertEqual(0.5, cc.cast.status.volume_level)

            self._command('set_volume', {'raise_lower': 'up'})
            self.assertEqual(0.6, round(cc.cast.status.volume_level * 10) / 10)

            self._command('set_volume', {'raise_lower': 'down'})
            self.assertEqual(0.5, round(cc.cast.status.volume_level * 10) / 10)

            self.assertFalse(cc.cast.status.volume_muted)
            self._command('mute')
            self.assertTrue(cc.cast.status.volume_muted)

            self._command('unmute')
            self.assertFalse(cc.cast.status.volume_muted)

            current_content_id = pc.status.content_id

            self._command('shuffle_on')
            # There is a risk of collision on this test, it may randomly choose the first item...
            self._wait_till_playing()
            self.assertNotEqual(current_content_id, pc.status.content_id)

            self._command('shuffle_off')
            self._wait_till_playing()
            self.assertEqual(current_content_id, pc.status.content_id)

            current_content_id = self.mc.status.content_id
            self._command('play_next')
            self._wait_till_event(lambda: current_content_id != self.mc.status.content_id)
            self.assertNotEqual(current_content_id, self.mc.status.content_id)

            current_content_id = self.mc.status.content_id
            self._command('play_previous')
            self._wait_till_event(lambda: current_content_id != self.mc.status.content_id)
            self.assertNotEqual(current_content_id, self.mc.status.content_id)
        finally:
            self._stop()

    def _wait_till_episode(self, episode):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        self._wait_till_event(lambda: pc.status.episode != episode)
        self.assertNotEqual(episode, pc.status.episode)

    def _wait_till_bitrate(self, bitrate):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        self._wait_till_event(lambda: bitrate != self.get_playing_bitrate(pc))
        self.assertNotEqual(bitrate, self.get_playing_bitrate(pc))

    def test_play_show(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self._command('play_media',
                          {'play': 'find', 'type': 'show', 'title': TST_SHOW_NAME,
                           'app': 'plex'})
            item = pc.current_item
            self.assertEqual('show', item.TYPE)
            self.assertTrue(TST_SHOW_NAME.lower() in item.title.lower())

            self.assertFalse(pc.status.player_is_playing)
            self._command('play')
            self._wait_till_playing()
            self.assertTrue(pc.status.player_is_playing)
            time.sleep(10)

            # Test play previous episode
            current_episode = pc.status.episode
            self._command('play_previous')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode - 1, pc.status.episode)

            # Test play next episode
            self._wait_till_playing()
            current_episode = pc.status.episode
            self._command('play_next')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode + 1, pc.status.episode)
        finally:
            self._stop()

    def test_play_episode_by_title(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            # Retrieve by title
            self._command('play_media',
                          {'play': 'find', 'type': 'episode', 'tvshow': TST_SHOW_NAME,
                           'title': TST_EPISODE_TITLE, 'app': 'plex'})
            item = pc.current_item
            self.assertEqual('episode', item.TYPE)
            self.assertTrue(TST_EPISODE_TITLE.lower() in item.title.lower())
            self.assertTrue(TST_SHOW_NAME.lower() in item.show().title.lower())

            self.assertFalse(pc.status.player_is_playing)
            self._command('play')
            self._wait_till_playing()
            self.assertTrue(pc.status.player_is_playing)

            # Test play previous episode
            current_episode = pc.status.episode
            self._command('play_previous')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode - 1, pc.status.episode)

            # Test play next episode
            current_episode = pc.status.episode
            self._command('play_next')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode + 1, pc.status.episode)

        finally:
            self._stop()

    def test_play_episode_by_number(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            # Retrieve by season and episode
            self._command('play_media',
                          {'play': 'find', 'type': 'episode', 'seasnum': TST_EPISODE_SEASON,
                           'epnum': TST_EPISODE_NUMBER, 'tvshow': TST_SHOW_NAME,
                           'app': 'plex'})

            item = pc.current_item
            self.assertEqual('episode', item.TYPE)
            self.assertEqual(TST_EPISODE_SEASON, item.seasonNumber)
            self.assertEqual(TST_EPISODE_NUMBER, item.episodeNumber)
            self.assertTrue(TST_SHOW_NAME.lower() in item.show().title.lower())

            self.assertFalse(pc.status.player_is_playing)
            self._command('play')
            self._wait_till_playing()
            self.assertTrue(pc.status.player_is_playing)

            # Test play previous episode
            current_episode = pc.status.episode
            self._command('play_previous')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode - 1, pc.status.episode)

            # Test play next episode
            current_episode = pc.status.episode
            self._command('play_next')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode + 1, pc.status.episode)

        finally:
            self._stop()

    def test_play_first_episode(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            # Retrieve by season and episode
            self._command('play_media',
                          {'play': 'find', 'type': 'episode', 'seasnum': 1,
                           'epnum': 1, 'tvshow': TST_SHOW_NAME,
                           'app': 'plex'})

            item = pc.current_item
            self.assertEqual('episode', item.TYPE)
            self.assertEqual(1, item.seasonNumber)
            self.assertEqual(1, item.episodeNumber)
            self.assertTrue(TST_SHOW_NAME.lower() in item.show().title.lower())

            self.assertFalse(pc.status.player_is_playing)
            self._command('play')
            self._wait_till_playing()
            self.assertTrue(pc.status.player_is_playing)

            # Test play previous episode
            self._command('play_previous')
            time.sleep(20)
            self.assertEqual(1, pc.status.episode)

            # Test play next episode
            current_episode = pc.status.episode
            self._command('play_next')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode + 1, pc.status.episode)

        finally:
            self._stop()

    def test_play_season(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            # Retrieve by season and episode
            self._command('play_media',
                          {'play': 'find', 'type': 'episode', 'seasnum': 1,
                           'tvshow': TST_SHOW_NAME,
                           'app': 'plex'})

            item = pc.current_item
            self.assertEqual('season', item.TYPE)
            self.assertEqual(1, item.seasonNumber)
            self.assertTrue(TST_SHOW_NAME.lower() in item.show().title.lower())

            self.assertFalse(pc.status.player_is_playing)
            self._command('play')
            self._wait_till_playing()
            self.assertTrue(pc.status.player_is_playing)
            self.assertEqual(1, pc.status.episode)

            # Test play previous episode
            self._command('play_previous')
            time.sleep(20)
            self.assertEqual(1, pc.status.episode)

            # Test play next episode
            current_episode = pc.status.episode
            self._command('play_next')
            self._wait_till_episode(current_episode)
            self.assertEqual(current_episode + 1, pc.status.episode)

        finally:
            self._stop()

    def test_transcode(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self._command('play_media',
                          {'play': 'play', 'title': 'mythic quest', 'app': 'plex'})
            self._wait_till_playing()

            # Maximum quality
            self._command('transcode',
                          {'quality': 'maximum'})
            self.assertEqual(0, self.get_playing_bitrate(pc))

            # Medium quality
            current_bitrate = self.get_playing_bitrate(pc)
            self._command('transcode',
                          {'quality': 'medium'})
            self._wait_till_bitrate(current_bitrate)
            self.assertEqual(4000, self.get_playing_bitrate(pc))

            # Reduce quality
            current_bitrate = self.get_playing_bitrate(pc)
            self._command('transcode',
                          {'raise_lower': 'down'})
            self._wait_till_bitrate(current_bitrate)
            self.assertEqual(3000, self.get_playing_bitrate(pc))

            # Increase quality
            current_bitrate = self.get_playing_bitrate(pc)
            self._command('transcode',
                          {'raise_lower': 'up'})
            self._wait_till_bitrate(current_bitrate)
            self.assertEqual(4000, self.get_playing_bitrate(pc))

            # Maximum quality
            current_bitrate = self.get_playing_bitrate(pc)
            self._command('transcode',
                          {'quality': 'maximum'})
            self._wait_till_bitrate(current_bitrate)
            self.assertEqual(0, self.get_playing_bitrate(pc))

            # Increase quality from maximum
            self._command('transcode',
                          {'raise_lower': 'up'})
            time.sleep(20)
            self.assertEqual(0, self.get_playing_bitrate(pc))

            # Reduce quality from maximum
            current_bitrate = self.get_playing_bitrate(pc)
            self._command('transcode',
                          {'raise_lower': 'down'})
            self._wait_till_bitrate(current_bitrate)
            self.assertEqual(8000, self.get_playing_bitrate(pc))

        finally:
            self._stop()

    def test_play_photos(self):
        cc = self.chromecast_controller.get_chromecast(self.cc_name)
        pc = cc.plex_controller
        try:
            self._command('open', {'app': 'plex'})

            self._command('play_photos',
                          {'play': 'play', 'year': 2012})
            self.assertIsNotNone(pc.current_item)
            self.assertFalse(pc.is_shuffle_on())

            # Shuffle play queue
            self._command('shuffle-on')
            self._wait_till_playing()
            self.assertTrue(pc.is_shuffle_on())

            # Unshuffle play queue
            self._command('shuffle-off')
            self._wait_till_playing()
            self.assertFalse(pc.is_shuffle_on())

            # Play shuffled
            self._command('play_photos',
                          {'play': 'shuffle', 'year': 2012})
            self._wait_till_playing()
            self.assertIsNotNone(pc.current_item)
            self.assertTrue(pc.is_shuffle_on())

        finally:
            self._stop()

