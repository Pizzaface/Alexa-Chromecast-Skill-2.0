import logging
import threading
import time
from datetime import datetime, timedelta

import pychromecast

from local import utils
from local.controllers.plex_controller import MyPlexController
from local.controllers.youtube_controller import MyYouTubeController
from local.helpers import moviedb_search

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChromecastWrapper:
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

    def __init__(self, cc):
        self.__cc = cc
        cc.media_controller.register_status_listener(self)
        cc.register_status_listener(self)

        self._youtube_controller = MyYouTubeController()
        cc.register_handler(self._youtube_controller)

        self._plex_controller = MyPlexController()
        cc.register_handler(self._plex_controller)

    def new_media_status(self, status):
        pass

    def new_cast_status(self, status):
        pass


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
                if not cc.device.friendly_name in self.__chromecasts.keys():
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

    def handle_command(self, room, command, data):
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
        self.get_chromecast(name).media_controller.play()

    def pause(self, data, name):
        cc = self.get_chromecast(name)
        cc.media_controller.pause()

    def shutdown(self, signum, frame):
        logger.info('Shutting down periodic Chromecast scanning')
        self.chromecast_collector.stop()

    def stop(self, data, name):
        self.get_chromecast(name).media_controller.stop()

    def open(self, data, name):
        app = data['app']
        if app == 'youtube':
            self.get_chromecast(name).youtube_controller.launch()
        elif app == 'plex':
            self.get_chromecast(name).plex_controller.launch()
        else:
            pass

    def set_volume(self, data, name):
        volume = data['volume']  # volume as 0-10
        volume_normalized = float(volume) / 10.0  # volume as 0-1
        self.get_chromecast(name).cast.set_volume(volume_normalized)

    def mute(self, data, name):
        self.get_chromecast(name).cast.set_volume_muted(True)

    def unmute(self, data, name):
        self.get_chromecast(name).cast.set_volume_muted(False)

    def play_next(self, data, name):
        # mc.queue_next() didn't work
        self.get_chromecast(name).media_controller.skip()

    def rewind(self, data, name):
        mc = self.get_chromecast(name).media_controller
        duration = data['duration']
        position = 0
        if duration:
            seconds = utils.parse_iso_duration(duration)
            position = mc.status.current_time - seconds
        mc.seek(position)

    def seek(self, data, name):
        mc = self.get_chromecast(name).media_controller
        duration = data['duration']
        direction = data['direction']
        seconds = utils.parse_iso_duration(duration)
        if direction == 'back':
            seconds = -seconds
        mc.seek(mc.status.current_time + seconds)

    def play_previous(self, data, name):
        cc = self.get_chromecast(name)
        current_id = cc.media_controller.status.content_id
        cc.youtube_controller.play_previous(current_id)

    def play_video(self, data, name):
        cc = self.get_chromecast(name)
        video_title = data['title']
        streaming_app = data['app'] if 'app' in data.keys() else ''

        if not streaming_app:
            if cc.cast.app_id == pychromecast.APP_YOUTUBE:
                streaming_app = 'youtube'
            elif cc.cast.app_id == cc.plex_controller.app_id:
                streaming_app = 'plex'

        if streaming_app == 'youtube':
            cc.youtube_controller.play_youtube(video_title)
        elif streaming_app == 'plex':
            cc.plex_controller.play_plex(video_title)
            # TODO: Future support other apps - Not Implemented
            logger.info('Asked chromecast to play title: %s on Plex' % video_title)
        else:
            logger.info('The streaming application %s is not supported' % streaming_app)

    def find(self, data, name):
        cc = self.get_chromecast(name)
        video_title = data['title']
        streaming_app = data['app'] if 'app' in data.keys() else ''

        if not streaming_app:
            if cc.cast.app_id == pychromecast.APP_YOUTUBE:
                streaming_app = 'youtube'
            elif cc.cast.app_id == cc.plex_controller.app_id:
                streaming_app = 'plex'

        #if streaming_app == 'youtube':
        #    cc.youtube_controller.find_youtube(video_title)
        if streaming_app == 'plex':
            cc.plex_controller.find_plex(video_title)
            # TODO: Future support other apps - Not Implemented
            logger.info('Asked chromecast to play title: %s on Plex' % video_title)
        else:
            logger.info('The streaming application %s is not supported' % streaming_app)

    def play_trailer(self, data, name):
        cc = self.get_chromecast(name)
        yt = cc.youtube_controller
        moviedb_result = moviedb_search.get_movie_trailer_youtube_id(data['title'])
        video_id = moviedb_result["youtube_id"]
        yt.play_video(video_id)
        logger.info('video sent to chromecast, id: %s' % video_id)

    def restart(self, data, name):
        self.get_chromecast(name).cast.reboot()

    def change_audio(self, data, name):
        plex_c = self.get_chromecast(name).plex_controller
        plex_c.change_audio_track()

    def subtitle_on(self, data, name):
        plex_c = self.get_chromecast(name).plex_controller
        plex_c.change_subtitle_track()

    def subtitle_off(self, data, name):
        plex_c = self.get_chromecast(name).plex_controller
        plex_c.turn_off_subtitles()

