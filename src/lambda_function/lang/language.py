import os
from enum import unique, Enum

file_path = os.path.dirname(__file__)

@unique
class Key(Enum):
    CardTitle = 1
    Help = 2
    Ok = 3
    Goodbye = 4
    GeneralError = 5
    SetTheRoom = 6
    ShortSetTheRoom = 7
    ControlRoom = 8
    SubtitlesOff = 9
    SubtitlesOn = 10
    LogErrorSnsPublish = 11
    ErrorSnsPublish = 12
    SwitchAudio = 13
    ChangeQuality = 14
    IncreaseQuality = 15
    DecreaseQuality = 16
    ErrorChangeQuality = 17
    ErrorEpisodeParams = 18
    ErrorSetVolumeRange = 19
    Playing = 20
    Finding = 21
    Shuffling = 22
    InRoom = 23
    OnApp = 24
    PlayTitle = 25
    PlaySongsByArtist = 26
    PlaySong = 27
    PlaySongsByAlbum = 28
    PlayPhotosByDate = 29
    PlayPhotosByEvent = 30
    PlayPhotosByTitle = 31
    PlayPlaylist = 32
    PlayMovie = 33
    PlayShow = 34
    PlayEpisode = 35
    PlayEpisodeNumber = 36
    PlaySeason = 37
    Speak1080p = 38
    Speak720p = 39
    Speak480p = 40
    ListMonths = 41


class Language:
    __LANGUAGES = {}

    @property
    def locale(self):
        return self.__locale

    def __init__(self, locale):
        # If already loaded just return that
        self.__locale = locale
        if locale in self.__LANGUAGES.keys():
            return

        # Dynamically load language
        filename = locale.replace('-', '')
        if os.path.exists(file_path + os.path.sep + filename + '.py'):
            lang = __import__('lambda_function.lang.' + filename, fromlist=['LANGUAGE'])
        else:
            from lambda_function.lang import enAU as lang
        self.__LANGUAGES[locale] = lang.LANGUAGE

    def get(self, key: Key, **kwargs):
        lang = self.__LANGUAGES[self.__locale]
        result = lang[key]
        if type(result) == str:
            return result.format(**kwargs)
        return result

