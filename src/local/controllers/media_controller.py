from abc import ABC, abstractmethod


class MediaExtensions(ABC):

    @abstractmethod
    def launch(self):
        raise NotImplementedError()

    @abstractmethod
    def previous(self):
        raise NotImplementedError()

    @abstractmethod
    def next(self):
        raise NotImplementedError()

    @abstractmethod
    def play_item(self, options):
        raise NotImplementedError()

    @abstractmethod
    def shuffle_on(self):
        raise NotImplementedError()

    @abstractmethod
    def shuffle_off(self):
        raise NotImplementedError()

    @abstractmethod
    def loop_on(self):
        raise NotImplementedError()

    @abstractmethod
    def loop_off(self):
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        raise NotImplementedError()

    @abstractmethod
    def transcode(self, data):
        raise NotImplementedError()

    @abstractmethod
    def play(self):
        raise NotImplementedError()

    @abstractmethod
    def pause(self):
        raise NotImplementedError()
