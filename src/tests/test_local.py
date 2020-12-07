import unittest
import pychromecast
from mock import Mock
from dotenv import load_dotenv
from os.path import join, dirname
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../src")

class TestLocal(unittest.TestCase):
    
    def setUp(self):
        dotenv_path = join(dirname(__file__), '.testenv')
        # Load file from the path.
        load_dotenv(dotenv_path)
        from local.main import ChromecastController
        self.chromecast_controller = ChromecastController()
        self.cc_name = 'Media Room'

    def tearDown(self):
        self.chromecast_controller.chromecast_collector.stop()

    def test_play_trailer(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_trailer', {'title': 'The Matrix'})

    def test_play_on_app(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_video', {'title': 'songs by Macklemore', 'app': 'youtube'})
        for _loops in range(5):
            time.sleep(60)

    def test_playlist(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_video', {'title': 'macklemore playlist', 'app': 'youtube'})
        time.sleep(20)
        self.chromecast_controller.handle_command(self.cc_name, 'play_next', {})
        time.sleep(20)
        self.chromecast_controller.handle_command(self.cc_name, 'play_previous', {})
        time.sleep(60)

    def test_play_next(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_next', {})

    def test_pause(self):
        self.chromecast_controller.handle_command(self.cc_name, 'pause', {})

    def test_play_previous(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_previous', {})
