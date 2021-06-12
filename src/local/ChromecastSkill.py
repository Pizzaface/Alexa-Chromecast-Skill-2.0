import os
import socket
import ssl
import threading
import time
import logging.handlers
from datetime import datetime, timedelta
import pychromecast
from plexapi.server import PlexServer
from pychromecast import Chromecast
from pychromecast.controllers.plex import PlexController
from pychromecast.controllers.youtube import YouTubeController
import local.youtube as youtube_search
import local.moviedb_search as moviedb_search

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MyYouTubeController(YouTubeController):
    """
    Youtube Controller extension
    """

    def __init__(self):
        self.play_list = {}
        super().__init__()

    def receive_message(self, msg, data):
        logger.debug('Received: %s %s' % (msg, data))
        return YouTubeController.receive_message(self, msg, data)

    def init_playlist(self):
        self.playlist = {}

    def play_previous(self, current_id):
        # This is not pretty.... it rebuilds the playlist on a previous command to make it work
        # There should be a way to play from a position in the queue, but I couldn't find it
        select_from_here = False
        if len(self.playlist) == 0:
            self.playlist = self._session.get_queue_videos()

        previous_id = False
        self.clear_playlist()
        for video in self.playlist:

            if video['data-video-id'] == current_id:
                if previous_id:
                    self.play_video(previous_id)
                    select_from_here = True
                else:
                    return

            if select_from_here:
                self.add_to_queue(video['data-video-id'])

            previous_id = video['data-video-id']


class ChromecastWrapper:
    """
    Thin wrapper to register controllers and listeners
    """
    @property
    def cast(self) -> Chromecast:
        return self.__cc

    @property
    def media_controller(self):
        return self.cast.media_controller

    @property
    def name(self):
        return self.__cc.device.friendly_name

    def __init__(self, cc):
        self.__cc = cc
        cc.media_controller.register_status_listener(self)
        cc.register_status_listener(self)

        self.youtube_controller = MyYouTubeController()
        cc.register_handler(self.youtube_controller)

        self.plex_controller = PlexController()
        cc.register_handler(self.plex_controller)

    def new_media_status(self, status: pychromecast.controllers.media.MediaStatus):
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

    def get_chromecast(self, name):
        result = self.__chromecasts[name]
        result.cast.wait()
        return result


def play_youtube(cc, video_title):
    yt = cc.youtube_controller
    video_playlist = youtube_search.search(video_title)
    if len(video_playlist) == 0:
        logger.info('Unable to find youtube video for: %s' % video_title)
        return
    playing = False
    yt.init_playlist()
    for video in video_playlist:
        if not playing:
            if not video['playlist_id']:
                # Youtube controller will clear for a playlist
                yt.clear_playlist()
            yt.play_video(video['id'], video['playlist_id'])
            logger.debug('Currently playing: %s' % video['id'])
            playing = True
        else:
            yt.add_to_queue(video['id'])
    logger.info(
        'Asked chromecast to play %i titles matching: %s on YouTube' % (len(video_playlist), video_title))

def get_ssl_cert_name(hostname, port):
    context = ssl.create_default_context()
    context.check_hostname = False
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 5 second timeout
    conn.settimeout(5.0)
    conn.connect((hostname, port))
    domain = conn.getpeercert()['subject'][0][0][1]
    domain = domain.replace('*', '')
    return domain


def play_plex(cc, video_title):
    plex = cc.plex_controller
    hostname = os.environ.get('PLEX_HOST')
    port = int(os.environ.get('PLEX_PORT'))
    token = os.environ.get('PLEX_TOKEN')
    logger.info(f'Plex Host: {hostname}, Port: {port}')

    cert_common_name = get_ssl_cert_name(hostname, port)
    plex_server = PlexServer(f'https://{hostname.replace(".", "-")}{cert_common_name}:{port}', token)

    # Find best match
    items = plex_server.search(video_title)
    media = False
    for item in items:
        if item.TYPE == 'show':
            # Play most recent episode
            episodes = item.episodes()
            # Get last unwatched one
            media = next((episode for episode in item.episodes() if not episode.isWatched), False)
        if not media and item.TYPE == 'movie':
            media = item
        if not media and item.TYPE == 'episode':
            media = item
        if media:
            break
    plex.block_until_playing(media)


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
        except:
            logger.exception('Unexpected error')

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
        self.get_chromecast(name).cast.quit_app()

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

    def play_next(self, data, name):
        # mc.queue_next() didn't work
        self.get_chromecast(name).media_controller.skip()

    def rewind(self, data, name):
        self.get_chromecast(name).media_controller.seek(0)

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
            elif cc.cast.app_id == '9AC194DC':
                streaming_app = 'plex'

        if streaming_app == 'youtube':
            play_youtube(cc, video_title)
        elif streaming_app == 'plex':
            play_plex(cc, video_title)
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

