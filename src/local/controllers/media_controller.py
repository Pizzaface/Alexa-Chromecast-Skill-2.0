import time
from abc import ABC, abstractmethod


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
    def shuffle_on(self):
        raise NotImplementedError()

    @abstractmethod
    def shuffle_off(self):
        raise NotImplementedError()

    def _get_content_id(self):
        # On occasion content_id is not found
        content_id = None
        for _ in range(3):
            content_id = self.status.content_id
            if content_id:
                break
            time.sleep(1)
        return content_id
