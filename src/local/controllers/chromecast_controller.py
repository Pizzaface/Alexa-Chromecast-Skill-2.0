import logging
import os
import threading
import time
from datetime import datetime, timedelta
import pychromecast
from pychromecast.controllers.media import MediaStatusListener, MediaStatus
from pychromecast.controllers.receiver import CastStatusListener

from local import utils, constants
from local.controllers.media_controller import MediaExtensions
from local.controllers.plex_controller import MyPlexController
from local.controllers.youtube_controller import MyYouTubeController

logger = logging.getLogger(__name__)

APP_YOUTUBE = 'youtube'
APP_PLEX = 'plex'

APP_PLEX_ID = '9AC194DC'  # Plex App Id in pychromecast seems to be wrong...
APP_YOUTUBE_ID = pychromecast.APP_YOUTUBE
APP_NETFLIX_ID = 'CA5E8412'


class ChromecastWrapper(MediaStatusListener, CastStatusListener):
    """
    Thin wrapper to register controllers and listeners
    """

    @property
    def cast(self) -> pychromecast.Chromecast:
        return self.__cc

    @property
    def media_controller(self):
        return self.cast.media_controller

    @property
    def name(self):
        return self.__cc.device.friendly_name

    @property
    def plex_controller(self) -> MyPlexController:
        return self._plex_controller

    @property
    def youtube_controller(self) -> MyYouTubeController:
        return self._youtube_controller

    def __init__(self, cc: pychromecast.Chromecast):
        self.__cc = cc
        cc.media_controller.register_status_listener(self)
        cc.register_status_listener(self)

        self._plex_controller = None
        self._youtube_controller = None

        if os.environ.get(constants.ENV_YOUTUBE_API_KEY):
            self._youtube_controller = MyYouTubeController(cc)
            cc.register_handler(self._youtube_controller)
        else:
            logger.warning('Youtube controller not loaded. Please set your Youtube API Key.')

        if os.environ.get(constants.ENV_PLEX_IP_ADDRESS):
            self._plex_controller = MyPlexController(cc)
            cc.register_handler(self._plex_controller)
        else:
            logger.warning('Plex controller not loaded. Please set your Plex configuration.')

    def new_media_status(self, status: MediaStatus):
        logger.debug('----')
        logger.debug(f'New Media Status Event: {status}')
        logger.debug('----')

    def new_cast_status(self, status: MediaStatus):
        logger.debug('----')
        logger.debug(f'New Cast Status Event: {status}')
        logger.debug('----')

    def __get_controller(self, app=''):
        if app == APP_YOUTUBE and self.youtube_controller:
            return self.youtube_controller
        if app == APP_PLEX and self.plex_controller:
            return self.plex_controller
        if app:
            logger.error(f'Unable to process command, the streaming application {app} is not supported')
            return None
        return self.media_controller

    def get_controller(self, app='') -> MediaExtensions:
        if not app:
            # If no app is specified assume it's the active one
            current_app_id = self.cast.app_id
            if current_app_id == APP_YOUTUBE_ID:
                app = APP_YOUTUBE
            elif current_app_id == APP_PLEX_ID:
                app = APP_PLEX
        return self.__get_controller(app)


class ChromecastCollector:
    """
    Stores available Chromecasts.
    Every 2 hours it will check, and add any new Chromecasts
    """

    @property
    def count(self):
        return len(self.__chromecasts)

    def stop(self):
        self.running = False
        self.thread.join(10)

    def __set_chromecasts(self):
        with self.lock:
            for cc in pychromecast.get_chromecasts()[0]:
                cc.wait()
                if cc.device.friendly_name not in self.__chromecasts.keys():
                    logger.info("Adding %s" % cc.device.friendly_name)
                    self.__chromecasts[cc.device.friendly_name] = ChromecastWrapper(cc)
            self.expiry = datetime.now()

    def expire_chromecasts(self):
        while self.running:
            time.sleep(1)
            refresh_period = timedelta(minutes=120)
            if (self.expiry + refresh_period) < datetime.now():
                logger.info("Searching for new Chromecasts...")
                self.__set_chromecasts()
                logger.info("Search completed.")

    def __init__(self):
        self.running = True
        self.expiry = datetime.now()
        self.lock = threading.Lock()
        self.__chromecasts = {}
        self.__set_chromecasts()
        self.thread = threading.Thread(target=self.expire_chromecasts)
        self.thread.start()

    def match_chromecast(self, room) -> ChromecastWrapper:
        with self.lock:
            result = next((x for x in self.__chromecasts.values() if
                           str.lower(room.strip()) in str.lower(x.name).replace(' the ', '')), None)
            if result:
                result.cast.wait()
            return result

    def get_chromecast(self, name) -> ChromecastWrapper:
        result = self.__chromecasts[name]
        result.cast.wait()
        return result


class ChromecastController:
    """
    Wrapper to send commands to different named Chromecasts
    """

    def __init__(self):

        logger.info("Finding Chromecasts...")
        self.chromecast_collector = ChromecastCollector()
        if self.chromecast_collector.count == 0:
            logger.info("No Chromecasts found")
            exit(1)
        logger.info("%i Chromecasts found" % self.chromecast_collector.count)

    def get_chromecast(self, name) -> ChromecastWrapper:
        return self.chromecast_collector.get_chromecast(name)

    def handle_command(self, room, command, data=None):
        if data is None:
            data = {}
        try:
            chromecast = self.chromecast_collector.match_chromecast(room)
            if not chromecast:
                logger.warning('No Chromecast found matching: %s' % room)
                return
            func = command.replace('-', '_')
            logger.info('Sending %s command to Chromecast: %s' % (func, chromecast.name))

            getattr(self, func)(data, chromecast.name)
        except Exception as err:
            logger.exception(f'Unexpected error: {err}')

    def resume(self, data, name):
        self.play(data, name)

    def play(self, data, name):
        self.get_chromecast(name).get_controller().play()

    def pause(self, data, name):
        self.get_chromecast(name).get_controller().pause()

    def shutdown(self, signum, frame):
        logger.info('Shutting down periodic Chromecast scanning')
        self.chromecast_collector.stop()

    def stop(self, data, name):
        cc = self.get_chromecast(name)
        if cc.cast.app_id == APP_NETFLIX_ID:
            logger.warning("Stop doesn't work on Netflix. Stopping Netflix app.")
            cc.cast.quit_app()
        else:
            self.get_chromecast(name).get_controller().stop()

    def open(self, data, name):
        app = data['app']
        controller = self.get_chromecast(name).get_controller(app)
        if controller:
            controller.launch()

    def set_volume(self, data, name):
        if 'volume' in data:
            volume = data['volume']  # volume as 0-10
            volume_normalized = float(volume) / 10.0  # volume as 0-1
        else:
            raise_lower = data['raise_lower']
            cast = self.get_chromecast(name).cast
            vol = cast.status.volume_level
            volume_normalized = vol + 0.1 if 'up' in raise_lower else vol - 0.1
        self.get_chromecast(name).cast.set_volume(volume_normalized)

    def mute(self, data, name):
        self.get_chromecast(name).cast.set_volume_muted(True)

    def unmute(self, data, name):
        self.get_chromecast(name).cast.set_volume_muted(False)

    def shuffle_on(self, data, name):
        cc = self.get_chromecast(name)
        cc.get_controller().shuffle_on()

    def shuffle_off(self, data, name):
        cc = self.get_chromecast(name)
        cc.get_controller().shuffle_off()

    def play_next(self, data, name):
        # mc.queue_next() didn't work
        cc = self.get_chromecast(name)
        cc.get_controller().next()

    def play_previous(self, data, name):
        cc = self.get_chromecast(name)
        cc.get_controller().previous()

    def transcode(self, data, name):
        cc = self.get_chromecast(name)
        cc.get_controller().transcode(data)

    def rewind(self, data, name):
        mc = self.get_chromecast(name).media_controller
        duration = utils.get_dict_val(data, 'duration')
        seconds = utils.parse_iso_duration(duration)
        position = mc.status.current_time - seconds
        mc.seek(position)

    def fast_forward(self, data, name):
        mc = self.get_chromecast(name).media_controller
        duration = utils.get_dict_val(data, 'duration')
        seconds = utils.parse_iso_duration(duration)
        position = mc.status.current_time + seconds
        mc.seek(position)

    def play_media(self, data, name):
        cc = self.get_chromecast(name)
        streaming_app = data['app'] if 'app' in data.keys() else ''
        cc.get_controller(streaming_app).play_item(data)

    def play_photos(self, data, name):
        cc = self.get_chromecast(name)
        cc.plex_controller.play_photos(data)

    def restart(self, data, name):
        # Reboot is no longer supported
        mc = self.get_chromecast(name).media_controller
        mc.seek(0)

    def change_audio(self, data, name):
        plex_c = self.get_chromecast(name).plex_controller
        plex_c.change_audio_track()

    def subtitle_on(self, data, name):
        plex_c = self.get_chromecast(name).plex_controller
        plex_c.change_subtitle_track()

    def subtitle_off(self, data, name):
        plex_c = self.get_chromecast(name).plex_controller
        plex_c.turn_off_subtitles()
