import logging
import os

from pychromecast import Chromecast
from pychromecast.controllers.youtube import YouTubeController
from pyyoutube import api as youtube_api

from local import utils, constants
from local.controllers.media_controller import MediaExtensions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Categories for searching
CATEGORY_MUSIC = '10'
CATEGORY_SHOWS = '43'
CATEGORY_TRAILERS = '44'

# How many Youtube results to return
SEARCH_LIMIT = 10


class MyYouTubeController(YouTubeController, MediaExtensions):
    """
    Youtube Controller extension
    """

    def pause(self):
        self.chromecast.media_controller.pause()

    def __init__(self, chromecast: Chromecast):
        self.chromecast = chromecast
        self.__api = youtube_api.Api(api_key=os.environ.get(constants.ENV_YOUTUBE_API_KEY))
        super().__init__()

    def receive_message(self, msg, data):
        logger.debug('Received: %s %s' % (msg, data))
        return YouTubeController.receive_message(self, msg, data)

    def shuffle_on(self):
        # TODO: Implement
        pass

    def shuffle_off(self):
        # TODO: Implement
        pass

    def play_next(self, action=''):
        self.chromecast.media_controller.queue_next()

    def play_previous(self, action=''):
        self.chromecast.media_controller.queue_prev()

    def find_item(self, options):
        self.play_item(options)

    def stop(self):
        self.chromecast.media_controller.stop()

    def play(self):
        self.chromecast.media_controller.play()

    def play_item(self, options):
        self.launch()
        title = utils.get_dict_val(options, 'title', '')
        opt_type = utils.get_dict_val(options, 'type', '')

        # Set search params
        yt_type = opt_type if opt_type == 'playlist' else None
        yt_video_type = opt_type if opt_type in ['movie', 'episode'] else None
        yt_category_id = None
        if opt_type == 'show':
            yt_category_id = CATEGORY_SHOWS
        elif opt_type in ['song', 'album', 'artist']:
            yt_category_id = CATEGORY_MUSIC
        elif opt_type == 'trailer':
            yt_category_id = CATEGORY_TRAILERS
        elif opt_type == 'channel':
            yt_type = opt_type

        yt_type = 'video' if yt_category_id or yt_video_type else yt_type
        video_playlist = self.__api.search(q=title,
                                           search_type=yt_type,
                                           video_type=yt_video_type,
                                           video_category_id=yt_category_id,
                                           limit=SEARCH_LIMIT)

        if len(video_playlist.items) == 0:
            logger.info('Unable to find youtube media for: %s' % title)
            return
        playing = False
        for video in video_playlist.items:
            video_id = video.id.videoId
            video_playlist_id = video.id.playlistId
            if not playing:
                self.clear_playlist()
                self.play_video(video_id, video_playlist_id)
                logger.debug('Currently playing: %s' % video_id)
                playing = True
            else:
                self.add_to_queue(video_id)
        logger.info(
            'Asked chromecast to play %i titles matching: %s on YouTube' % (len(video_playlist.items), title))
