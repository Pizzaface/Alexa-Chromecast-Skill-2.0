import time

from tests import utils

# Test values, change to match your Plex library
TST_CHROMECAST_NAME = 'Living Room TV'


class TestYouTube:

    def setUp(self):
        utils.load_test_env()
        from local.main import ChromecastController
        self.chromecast_controller = ChromecastController()
        self.cc_name = TST_CHROMECAST_NAME

    def test_playlist(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_video',
                                                  {'title': 'macklemore playlist', 'app': 'youtube'})
        time.sleep(20)
        self.chromecast_controller.handle_command(self.cc_name, 'play_next', {})
        time.sleep(20)
        self.chromecast_controller.handle_command(self.cc_name, 'play_previous', {})
        time.sleep(60)

    def test_play_trailer(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_trailer', {'title': 'The Matrix'})

    def test_play_on_app(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_video',
                                                  {'title': 'songs by Macklemore', 'app': 'youtube'})
        for _loops in range(5):
            time.sleep(60)
