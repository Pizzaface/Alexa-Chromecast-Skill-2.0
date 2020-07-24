import os
import sys
import threading
import time
import logging
import logging.handlers
from datetime import datetime, timedelta
import pychromecast
from pychromecast import Chromecast
from pychromecast.controllers.youtube import YouTubeController
from pychromecast.controllers.plex import PlexController
import subprocess
import requests
from enum import Enum
import local.youtube as youtube_search
import local.moviedb_search as moviedb_search

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MyYouTubeController(YouTubeController):
    
    def __init__(self):
        self.play_list = {}
        super().__init__()

    def receive_message(self, msg, data):
        logger.debug('Received: %s %s' % (msg, data))
        return YouTubeController.receive_message(self, msg, data)

    def init_playlist(self):
        self.playlist = {}

    def play_previous(self, current_id):
        #This is not pretty.... it rebuilds the playlist on a previous command to make it work
        #There should be a way to play from a position in the queue, but I couldn't find it
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

    def new_media_status(self, status:pychromecast.controllers.media.MediaStatus):
        pass

    def new_cast_status(self, status):
        pass

class ChromecastState:

    @property
    def count(self):
        return len(self.__chromecasts)

    def stop(self):
        self.running = False
        self.thread.join(10)

    def __set_chromecasts(self):
        with self.lock:
            self.__chromecasts = {}
            for cc in pychromecast.get_chromecasts():
                logger.info("Found %s" % cc.device.friendly_name)
                cc.wait()
                self.__chromecasts[cc.device.friendly_name] = ChromecastWrapper(cc)
            self.expiry = datetime.now()

    def expire_chromecasts(self):
        while self.running:
            time.sleep(1)
            refresh_period = timedelta(minutes=120)
            if (self.expiry + refresh_period) < datetime.now():
                self.__set_chromecasts()

    def __init__(self):
        self.running = True
        self.expiry = datetime.now()
        self.lock = threading.Lock()
        self.__set_chromecasts()
        self.thread = threading.Thread(target=self.expire_chromecasts)
        self.thread.start()

    def match_chromecast(self, room) -> ChromecastWrapper:
        with self.lock:
            result = next((x for x in self.__chromecasts.values() if str.lower(room.strip()) in str.lower(x.name).replace(' the ', '')), False)
            if result:
                result.cast.wait()
            return result

    def get_chromecast(self, name):
        result = self.__chromecasts[name]
        result.cast.wait()
        return result

class Skill():

    def __init__(self):
        logger.info("Finding Chromecasts...")
        self.chromecast_controller = ChromecastState()
        if self.chromecast_controller.count == 0:
            logger.info("No Chromecasts found")
            exit(1)
        logger.info("%i Chromecasts found" % self.chromecast_controller.count)

    def get_chromecast(self, name) -> ChromecastWrapper:
        return self.chromecast_controller.get_chromecast(name)

    def handle_command(self, room, command, data):
        try:
            chromecast = self.chromecast_controller.match_chromecast(room)
            if not chromecast:
                logger.warn('No Chromecast found matching: %s' % room)
                return
            func = command.replace('-','_')
            logger.info('Sending %s command to Chromecast: %s' % (func, chromecast.name))

            getattr(self, func)(data, chromecast.name)
        except Exception:
            logger.exception('Unexpected error')

    def resume(self, data, name):
        self.play(data, name)

    def play(self, data, name):
        self.get_chromecast(name).media_controller.play()
    
    def pause(self, data, name):
        cc = self.get_chromecast(name)
        cc.media_controller.pause()

    def stop(self, data, name):
        self.get_chromecast(name).cast.quit_app()

    def set_volume(self, data, name):
        volume = data['volume'] # volume as 0-10
        volume_normalized = float(volume) / 10.0 # volume as 0-1
        self.get_chromecast(name).cast.set_volume(volume_normalized)

    def play_next(self, data, name):
        #mc.queue_next() didn't work
        self.get_chromecast(name).media_controller.skip()

    def play_previous(self, data, name):
        cc = self.get_chromecast(name)
        current_id = cc.media_controller.status.content_id
        cc.youtube_controller.play_previous(current_id)

    def play_video(self, data, name):
        cc = self.get_chromecast(name)
        yt = cc.youtube_controller
        video_title = data['title']
        streaming_app = data['app']
        if streaming_app == 'youtube':
            video_playlist = youtube_search.search(video_title)
            if len(video_playlist) == 0:
                logger.info('Unable to find youtube video for: %s' % video_title)
                return
            playing = False
            yt.init_playlist()
            for video in video_playlist:
                if not playing:
                    if not video['playlist_id']:
                        #Youtube controller will clear for a playlist
                        yt.clear_playlist()
                    yt.play_video(video['id'], video['playlist_id'])
                    logger.debug('Currently playing: %s' % video['id'])
                    playing = True
                else:
                    yt.add_to_queue(video['id'])
            logger.info('Asked chromecast to play %i titles matching: %s on YouTube' % (len(video_playlist), video_title))

        elif streaming_app == 'plex':
            #TODO: Future support other apps - Not Implemented
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

