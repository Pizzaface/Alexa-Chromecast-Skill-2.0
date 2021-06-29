import logging

from pychromecast.controllers.youtube import YouTubeController
import local.helpers.youtube as youtube_search
from local.controllers.media_controller import MediaExtensions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MyYouTubeController(YouTubeController, MediaExtensions):
    """
    Youtube Controller extension
    """

    def __init__(self):
        self._play_list = {}
        super().__init__()

    def receive_message(self, msg, data):
        logger.debug('Received: %s %s' % (msg, data))
        return YouTubeController.receive_message(self, msg, data)

    def init_playlist(self):
        self._play_list = {}

    def shuffle_on(self):
        # TODO: Implement
        pass

    def shuffle_off(self):
        # TODO: Implement
        pass

    def play_next(self, chromecast, action=''):
        chromecast.media_controller.skip()

    def play_previous(self, chromecast, action=''):
        # This is not pretty.... it rebuilds the playlist on a previous command to make it work
        # There should be a way to play from a position in the queue, but I couldn't find it
        current_id = self._get_content_id()
        select_from_here = False
        if len(self._play_list) == 0:
            self._play_list = self._session.get_queue_videos()

        previous_id = False
        self.clear_playlist()
        for video in self._play_list:

            if video['data-video-id'] == current_id:
                if previous_id:
                    self.play_video(previous_id)
                    select_from_here = True
                else:
                    return

            if select_from_here:
                self.add_to_queue(video['data-video-id'])

            previous_id = video['data-video-id']

    def find_item(self, options):
        pass

    def play_item(self, options):
        self.launch()
        # ['app', 'room', 'title', 'song', 'album', 'artist', 'playlist', 'tvshow', 'movie']
        title = next(value for key, value in options.keys() if value and key not in ['app', 'room'])
        video_playlist = youtube_search.search(title)
        if len(video_playlist) == 0:
            logger.info('Unable to find youtube media for: %s' % title)
            return
        playing = False
        self.init_playlist()
        for video in video_playlist:
            if not playing:
                if not video['playlist_id']:
                    # Youtube controller will clear for a playlist
                    self.clear_playlist()
                self.play_video(video['id'], video['playlist_id'])
                logger.debug('Currently playing: %s' % video['id'])
                playing = True
            else:
                self.add_to_queue(video['id'])
        logger.info(
            'Asked chromecast to play %i titles matching: %s on YouTube' % (len(video_playlist), title))
