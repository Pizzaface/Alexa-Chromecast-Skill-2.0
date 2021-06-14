import logging
import unittest
from typing import List

import plexapi
import pychromecast
from dotenv import load_dotenv
from os.path import join, dirname
import sys
import os
import time

from pychromecast.controllers import plex

from local.controllers.chromecast_controller import ChromecastController
from local.controllers.plex_controller import MyPlexController

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../src")

class TestFind(unittest.TestCase):

    def setUp(self):
        dotenv_path = join(dirname(__file__), '.testenv')
        # Load file from the path.
        load_dotenv(dotenv_path)

    def test_audio(self):
        pc = MyPlexController()
        cc = ChromecastController().get_chromecast('Living Room TV')

        cc.change_audio()

        #items = pc.search('guardians of the galaxy', limit=5)
        #subs = pc.get_subtitle_streams(items[0])
        #auds = pc.get_audio_streams(items[0])
        #pc.set_audio_stream(part_id='33423', audio_stream_id='6016')
        #print(subs)


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
        self.chromecast_controller.handle_command(self.cc_name, 'play_video',
                                                  {'title': 'songs by Macklemore', 'app': 'youtube'})
        for _loops in range(5):
            time.sleep(60)

    def test_play_plex(self):
        cc = self.chromecast_controller.get_chromecast('Living Room TV')
        pc = cc.plex_controller
        #pc.mute(False)
        self.chromecast_controller.handle_command('Living Room TV', 'subtitle_off', {})
        #pc.mute(True)


        '''
        items = pc.search('guardians of the galaxy', limit=5)
        pc.resume_playing(items[0])
        self.chromecast_controller.handle_command('Living Room TV', 'seek',
                                                  {'direction': 'forward', 'duration': 'PT5M'})
        time.sleep(5)
        self.chromecast_controller.handle_command('Living Room TV', 'seek',
                                                  {'direction': 'back', 'duration': 'PT5M'})
        '''
    def test_find_plex(self):
        logger = logging.getLogger(pychromecast.__name__)
        logger.setLevel(logging.DEBUG)
        #self.chromecast_controller.handle_command(self.cc_name, 'open',
        #                                          {'app': 'plex'})
        # time.sleep(60)
        self.chromecast_controller.handle_command(self.cc_name, 'find_video',
                                                  {'title': 'guardians of the galaxy', 'app': 'plex'})

    def test_playlist(self):
        self.chromecast_controller.handle_command(self.cc_name, 'play_video',
                                                  {'title': 'macklemore playlist', 'app': 'youtube'})
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
