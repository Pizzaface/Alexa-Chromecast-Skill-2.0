import logging
import time
from typing import Callable
from pychromecast.controllers.media import MEDIA_PLAYER_STATE_PLAYING
from tests import utils
import unittest

# Test values
# TST_CHROMECAST_NAME = 'Media Room TV'
TST_CHROMECAST_NAME = 'Living Room TV'
TST_COMMAND_TIMEOUT = 60

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TestChromecast(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        utils.load_test_env()
        from local.main import ChromecastController
        cls.chromecast_controller = ChromecastController()
        cls.cc_name = TST_CHROMECAST_NAME
        cls.mc = cls.chromecast_controller.get_chromecast(cls.cc_name).media_controller

    @classmethod
    def tearDownClass(cls) -> None:
        cls.chromecast_controller.chromecast_collector.stop()

    def _wait_till_event(self, check: Callable):
        logger.info(f'Waiting for event {check}...')
        for _ in range(TST_COMMAND_TIMEOUT):
            if check():
                logger.info('Event occurred.')
                return
            time.sleep(1)
        logger.error('Timed out waiting for event.')

    def _wait_till_playing(self):
        self._wait_till_event(lambda: self.mc.status.player_state == MEDIA_PLAYER_STATE_PLAYING)
        self.assertTrue(self.mc.status.player_state == MEDIA_PLAYER_STATE_PLAYING)

    def _wait_till_paused(self):
        self._wait_till_event(lambda: self.mc.is_paused)
        self.assertTrue(self.mc.is_paused)

    def _wait_till_stopped(self):
        self._wait_till_event(lambda: not self.mc.is_playing and not self.mc.is_paused)
        self.assertTrue(not self.mc.is_playing and not self.mc.is_paused)

    def _command(self, command, params=None):
        if not params:
            params = {}
        self.chromecast_controller.handle_command(self.cc_name, command, params)
        time.sleep(5)

    def _stop(self):
        self._command('stop')
        self._wait_till_stopped()
