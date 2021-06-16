import time
from abc import ABC, abstractmethod

from pychromecast.controllers.media import MediaController


class MediaExtensions(ABC):

    @abstractmethod
    def play_previous(self, chromecast, action):
        raise NotImplementedError()

    @abstractmethod
    def play_next(self, chromecast, action):
        raise NotImplementedError()

    @abstractmethod
    def play_item(self, options):
        raise NotImplementedError()

    @abstractmethod
    def find_item(self, options):
        raise NotImplementedError()

    @abstractmethod
    def shuffle(self, on):
        raise NotImplementedError()

    def _get_content_id(self):
        # On occasion content_id is not found
        content_id = None
        for i in range(3):
            content_id = self.status.content_id
            if content_id:
                break
            time.sleep(1)
        return content_id


class MyMediaController(MediaExtensions, MediaController):

    def shuffle(self, on):
        pass

    def play_item(self, options):
        pass

    def find_item(self, options):
        pass

    def play_previous(self, chromecast, action=''):
        super().queue_next()

    def play_next(self, chromecast, action=''):
        super().queue_prev()
