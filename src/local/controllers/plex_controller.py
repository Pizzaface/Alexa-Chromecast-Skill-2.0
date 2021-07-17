from datetime import datetime
import json
import logging
import os
import socket
import ssl
import time
from typing import Optional, List

import requests
from dateutil.relativedelta import relativedelta
from plexapi.exceptions import Unauthorized, NotFound
from plexapi.media import Media
from plexapi.playqueue import PlayQueue
from plexapi.server import PlexServer
from plexapi.video import Show, Episode
from pychromecast import Chromecast
from pychromecast.controllers.plex import PlexController, media_to_chromecast_command

from local import utils, constants
from local.controllers.media_controller import MediaExtensions

logger = logging.getLogger(__name__)

# Transcode qualities
QUALITY_LIST = {
    '240p': 320,
    '320p': 720,
    '480p': 1500,
    '720p_low': 2000,
    '720p_med': 3000,
    '720p': 4000,
    '1080p': 8000
}


class PlexControllerError(Exception):
    # Nothing more to do
    pass


class MyPlexController(PlexController, MediaExtensions):

    @property
    def plex_server(self) -> PlexServer:
        if self.__plex_server:
            return self.__plex_server
        else:
            self.__plex_server = self.__get_plex_server()
            return self.__plex_server

    @property
    def bitrate(self):
        return self.__bitrate

    def __init__(self, cc: Chromecast):
        self.__current_item = None
        self.__playlist: Optional[PlayQueue] = None
        self.__plex_server = None
        self._subtitle_code = os.environ.get(constants.ENV_PLEX_SUBTITLE_LANG, 'eng')
        self.__bitrate = 0
        self.cast_id = cc.uuid
        self._load_settings()
        super().__init__()

    def _get_content_id(self):
        # On occasion content_id is not found
        content_id = None
        for _ in range(3):
            content_id = self.status.content_id
            if content_id:
                break
            time.sleep(1)
        return content_id

    def get_playing_item(self):
        content_id = self._get_content_id()
        if content_id:
            return self.plex_server.fetchItem(content_id)
        return None

    def transcode(self, data):
        raise_lower = utils.get_dict_val(data, 'raise_lower', '')
        bitrate = 0
        max_bitrate = 20000 if self.__bitrate == 0 else self.__bitrate
        if raise_lower == 'up':
            bitrate = next((value for key, value in QUALITY_LIST.items() if value > max_bitrate), 0)
        elif raise_lower == 'down':
            keys = list(QUALITY_LIST.keys())
            keys.reverse()
            bitrate = next((QUALITY_LIST[key] for key in keys if QUALITY_LIST[key] < max_bitrate), QUALITY_LIST['240p'])

        else:
            quality = utils.get_dict_val(data, 'quality', '')
            if quality == 'maximum':
                bitrate = 0
            elif quality.lower() in ['high', '1080p']:
                bitrate = QUALITY_LIST['1080p']
            elif quality.lower() in ['medium', '720p']:
                bitrate = QUALITY_LIST['720p']
            elif quality.lower() in ['low', '480p']:
                bitrate = QUALITY_LIST['480p']

        if bitrate != self.__bitrate:
            self.__bitrate = bitrate
            self._save_settings()
            self._resume_playing()

    def __shuffle(self, turn_on: bool):
        self._start_playing(shuffle=turn_on)

    def shuffle_on(self):
        self.__shuffle(True)

    def shuffle_off(self):
        self.__shuffle(False)

    def is_shuffle_on(self):
        return self.__playlist.playQueueShuffled if self.__playlist else False

    def __loop(self, turn_on: bool):
        playlist = self.__playlist
        if playlist:
            self._start_playing(shuffle=playlist.playQueueShuffled, repeat=turn_on)
        else:
            logger.warning('No current item to repeat.')

    def loop_on(self):
        self.__loop(True)

    def loop_off(self):
        self.__loop(False)

    def previous(self):
        # Previous doesn't go to the previous episode when it's part way through
        self.rewind()
        for _i in range(10):
            if self.status.current_time < 10:
                break
            time.sleep(1)
        super().previous()

    def play_photos(self, data):
        title = utils.get_dict_val(data, 'title')
        month: str = utils.get_dict_val(data, 'month')
        year = utils.get_dict_val(data, 'year')

        photos = []
        if title:
            photos = self.__get_photos_by_title(title, year)
        elif year:
            photos = self.__get_photos_by_date(month, year)
        if not photos:
            logger.info(f'Unable to find photos matching: {data}')
            return

        self.__current_item = photos
        play_type = utils.get_dict_val(data, 'play')
        if play_type == 'find':
            self.show_media()
        else:
            self._start_playing(shuffle=(play_type == 'shuffle'))

    def get_media_index(self):
        return self.status.media_custom_data.get("mediaIndex", 0)

    def get_part_index(self):
        return self.status.media_custom_data.get("partIndex", 0)

    def play(self):
        if self.__current_item and not self.status.player_is_paused:
            self._resume_playing()
        else:
            super().play()

    def stop(self):
        super().stop()
        # Reload to get update of played position
        self.current_item.reload()
        self.show_media()

    @property
    def current_item(self) -> Media:
        return self.__current_item

    def _set_current_item(self, item):
        self.__current_item = item
        self.__playlist = None

    def search(self, title, media_type='', limit=10):
        items = self.plex_server.search(title, mediatype=media_type, limit=limit)
        return items

    def block_until_playing(self, media=None, timeout=None, **kwargs):
        return super().block_until_playing(media=media, timeout=timeout, **kwargs)

    def _save_settings(self):
        file_name = f'.plex_config_{self.cast_id}'
        with open(file_name, "w") as write_file:
            write_file.write(json.dumps({
                'bitrate': self.__bitrate
            }))

    def _load_settings(self):
        file_name = f'.plex_config_{self.cast_id}'
        if not os.path.exists(file_name):
            return
        with open(file_name, "r") as read_file:
            content = json.loads(read_file.read())
        logger.info('Loaded settings:')
        logger.info(json.dumps(content, indent=4, sort_keys=True))
        self.__bitrate = content['bitrate']

    def get_audio_streams(self):
        item = self.get_playing_item().reload()
        if not item:
            return []
        part_index = self.get_part_index()
        media_index = self.get_media_index()
        part = item.media[media_index].parts[part_index]
        return part.audioStreams()

    def get_subtitle_streams(self):
        item = self.get_playing_item().reload()
        part_index = self.get_part_index()
        media_index = self.get_media_index()
        part = item.media[media_index].parts[part_index]
        return [subtitle for subtitle in part.subtitleStreams() if subtitle.languageCode == self._subtitle_code]

    def set_audio_stream(self, audio_stream_id):
        item = self.get_playing_item()
        part_index = self.get_part_index()
        media_index = self.get_media_index()
        part = item.media[media_index].parts[part_index]
        self.plex_server.query(f'/library/parts/{part.id}?audioStreamID={audio_stream_id}', requests.put)

    def set_subtitle_stream(self, subtitle_stream_id):
        if str(subtitle_stream_id) == '1':
            subtitle_stream_id = ''
        item = self.get_playing_item()
        part_index = self.get_part_index()
        media_index = self.get_media_index()
        part = item.media[media_index].parts[part_index]
        self.plex_server.query(f'/library/parts/{part.id}?subtitleStreamID={subtitle_stream_id}', requests.put)

    def turn_off_subtitles(self):
        item = self.get_playing_item()
        part_index = self.get_part_index()
        media_index = self.get_media_index()
        part = item.media[media_index].parts[part_index]
        self.plex_server.query(f'/library/parts/{part.id}?subtitleStreamID=0&allParts=1', requests.put)
        self._resume_playing()

    def receive_message(self, message, data: dict):
        self.logger.debug(data)

    def _send_start_play(self, media=None, bitrate=None, **kwargs):
        """
        Override to allow more
        """
        msg = media_to_chromecast_command(
            media, requestiId=self._inc_request(), **kwargs
        )
        if bitrate:
            data = msg["media"]["customData"]
            data['directStream'] = False
            data['directPlay'] = False
            data['bitrate'] = bitrate
            quality = next((key for key, item in QUALITY_LIST.items() if item == bitrate), 'UNKNOWN')
            logger.info(f'Transcoding media to {quality}, bitrate: {bitrate}')

        self.logger.debug("Create command: \n%r\n", json.dumps(msg, indent=4))
        self._last_play_msg = msg
        self._send_cmd(
            msg,
            namespace="urn:x-cast:com.google.cast.media",
            inc_session_id=True,
            inc=False,
        )

    @classmethod
    def __get_ssl_cert_name(cls, hostname, port):
        context = ssl.create_default_context()
        context.check_hostname = False
        with context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=hostname,
        ) as conn:
            # 5 second timeout
            conn.settimeout(5.0)
            try:
                conn.connect((hostname, port))
                domain = conn.getpeercert()['subject'][0][0][1]
                domain = domain.replace('*', '')
                return domain
            except Exception as err:
                msg = f'Unable to retrieve Plex certificate from {hostname}:{port}'
                logger.error(msg)
                logger.error(err)
                raise PlexControllerError(msg)

    @classmethod
    def __get_plex_server(cls) -> Optional[PlexServer]:
        ip_address = os.environ.get(constants.ENV_PLEX_IP_ADDRESS)
        port = os.environ.get(constants.ENV_PLEX_PORT)
        port = int(port) if port else False
        token = os.environ.get(constants.ENV_PLEX_TOKEN)
        if not ip_address or not port or not token:
            msg = 'Plex config is not set, set these in .custom_env'
            logger.warning(msg)
            raise PlexControllerError(msg)

        logger.info(f'Plex IP: {ip_address}, Port: {port}')
        logger.info('Looking up Plex server certificate...')
        cert_common_name = cls.__get_ssl_cert_name(ip_address, port)
        plex_address = f'https://{ip_address.replace(".", "-")}{cert_common_name}:{port}'
        try:
            return PlexServer(plex_address, token)
        except Unauthorized:
            msg = 'Authentication failed to Plex, check your token is correct in .custom_env'
            logger.error(msg)
            raise PlexControllerError(msg)
        except requests.exceptions.ConnectionError:
            msg = f'Failed to connect to Plex using determined address [{plex_address}]'
            logger.error(msg)
            raise PlexControllerError(msg)

    @staticmethod
    def get_next_episode_to_watch(show):
        """
        Get the last episode that was being watched, or the next unwatched one
        Otherwise just return the last one
        """
        episodes: List = show.episodes()
        episodes.reverse()
        pos = next((i for i, episode in enumerate(episodes) if episode.isWatched), 0)
        if pos == 0:
            # Return the last episode
            return episodes[pos]
        # Return the next episode, if there is one
        pos = pos - 1 if pos > 0 else 0
        return episodes[pos]

    def play_item(self, options):
        title = utils.get_dict_val(options, 'title', '')
        tv_show = utils.get_dict_val(options, 'tv_show', '')
        media_type = utils.get_dict_val(options, 'type')

        media_type = self._map_plex_type(media_type)

        if media_type == 'show':
            show = self.__get_show_by_title(tv_show if tv_show else title)
            if not show:
                logger.warning(f'Unable to find a matching show for: {tv_show if tv_show else title}')
                return
            play_media = show
            logger.info(f'Selected show: {show}')

        elif media_type == 'episode':
            ep_season = self.__get_episode_or_season(options)
            if not ep_season:
                logger.warning(f'Unable to find a matching episode/season for: {options}')
                return
            play_media = ep_season
            logger.info(f'Selected episode/season: {ep_season} for show: {ep_season.show()}')

        else:
            items = self.search(title, media_type=media_type, limit=10)
            if len(items) == 0:
                logger.info(f'Unable to find any item in Plex matching title: {title}')
                return
            play_media = items[0]

        self._set_current_item(play_media)
        play_command = utils.get_dict_val(options, 'play')
        if play_command == 'find':
            super().stop()
            self.show_media()
        else:
            self._start_playing(shuffle=(play_command == 'shuffle'))

    def show_media(self, **kwargs):
        # Tracks don't display in show details, fudge this by playing the track, then pausing it
        item = self.__current_item
        if type(item) == list:
            item = item[0]
        if item.TYPE in ['track']:
            self._start_playing()
            for _ in range(10):
                self.pause()
                if self.status.player_is_paused:
                    break
                time.sleep(1)
            return

        msg = media_to_chromecast_command(
            item, type='SHOWDETAILS', requestId=self._inc_request(), **kwargs
        )
        msg['media']['contentId'] = item.key

        def callback():  # pylint: disable=missing-docstring
            self._send_cmd(msg, inc_session_id=True, inc=False)

        self.launch(callback)

    def _resume_playing(self):
        if self.current_item:
            self.current_item.reload()
        self._start_playing(resume=True)

    def _start_playing(self, shuffle=False, repeat=False, resume=False):
        if not self.current_item:
            # Nothing to play
            return

        if not resume or not self.__playlist:
            self.__playlist = self.build_play_list(shuffle, repeat)

        media = self.__playlist
        if type(media) == PlayQueue:
            play_item = media.selectedItem
        else:
            play_item = media
        if 'viewOffset' in vars(play_item):
            offset = play_item.viewOffset / 1000
            self.block_until_playing(media, offset=offset, bitrate=self.__bitrate)
        else:
            self.block_until_playing(media, bitrate=self.__bitrate)

    def change_audio_track(self):
        audio_streams = self.get_audio_streams()
        if len(audio_streams) == 1:
            # Nothing to do only 1 audio stream
            return

        # Switch to next stream after the current selected
        pos = next((i for i, x in enumerate(audio_streams) if x.selected), -1) + 1
        if pos >= len(audio_streams):
            pos = 0
        self.set_audio_stream(audio_streams[pos].id)
        self._resume_playing()

    def change_subtitle_track(self):
        subtitle_streams = self.get_subtitle_streams()
        pos = next((i for i, x in enumerate(subtitle_streams) if x.selected), -1) + 1
        if pos >= len(subtitle_streams):
            pos = 0
        self.set_subtitle_stream(subtitle_streams[pos].id)
        self._resume_playing()

    def __get_episode_or_season(self, options) -> Episode:
        ep_num = utils.get_dict_val(options, 'epnum', '')
        seas_num = utils.get_dict_val(options, 'seasnum', '')
        tv_show = utils.get_dict_val(options, 'tvshow', '')
        title = utils.get_dict_val(options, 'title', '')
        result = None
        if ep_num:
            result = self.__get_episode_by_number(tv_show, ep_num, seas_num)
        elif seas_num:
            result = self.__get_season(tv_show, seas_num)
        elif title:
            result = self.__get_episode_by_title(tv_show, title)
        return result

    def __get_show_by_title(self, title) -> Optional[Show]:
        found_shows = self.search(title, media_type='show', limit=10)
        if not found_shows:
            # Try a broader search
            items = self.search(title, limit=10)
            for item in items:
                if item.TYPE == 'episode':
                    found_shows = [item.show()]
                    break
        return found_shows[0] if found_shows else None

    def __get_episode_by_number(self, tv_show, ep_num, seas_num) -> Optional[Episode]:
        show = self.__get_show_by_title(tv_show)
        try:
            if show:
                return show.get(season=seas_num, episode=ep_num)
        except NotFound:
            logger.warning(f'Unable to find Season {seas_num}, Episode {ep_num} for show: {show}')
        return None

    def __get_season(self, tv_show, seas_num) -> Optional[Episode]:
        show = self.__get_show_by_title(tv_show)
        try:
            if show:
                return show.season(season=seas_num)
        except NotFound:
            logger.warning(f'Unable to find Season {seas_num} for show: {show}')
        return None

    def __get_episode_by_title(self, tv_show, title) -> Optional[Episode]:
        episode = None
        found_episodes = self.search(title, media_type='episode', limit=10)
        show = self.__get_show_by_title(tv_show)
        for ep in found_episodes:
            if ep.grandparentKey == show.key:
                episode = ep
                break
        if not episode and found_episodes:
            return found_episodes[0]
        return episode

    def build_play_list(self, shuffle=False, repeat=False) -> PlayQueue:
        item = self.__current_item
        if type(item) == list or item.TYPE in ['artist', 'album', 'photo']:
            # noinspection PyTypeChecker
            play_list = self.plex_server.createPlayQueue(item,
                                                         shuffle=1 if shuffle else 0,
                                                         repeat=1 if repeat else 0)
            play_list.playQueueShuffled = shuffle
        elif item.TYPE == 'episode':
            episodes = self.__get_episodes(item.show(), item, count=20)
            play_list = self.plex_server.createPlayQueue(episodes, startItem=item)
        elif item.TYPE == 'show':
            episode = self.get_next_episode_to_watch(item)
            episodes = self.__get_episodes(item, episode, count=20)
            play_list = self.plex_server.createPlayQueue(episodes, startItem=episode)
        else:
            play_list = self.plex_server.createPlayQueue(item)
        return play_list

    @staticmethod
    def __get_episodes(show: Show, episode: Episode, count) -> List:
        eps = show.episodes()
        if len(eps) <= count:
            return eps
        pos = eps.index(episode)
        length = len(eps)
        end_pos = min(max(pos + count // 2 + 1, count + 1), length)
        start_pos = max(pos - count // 2 - (count // 2 - min(length - end_pos, 0)), 0)
        return eps[start_pos:end_pos]

    def __get_photos_by_title(self, title, year):
        photos = []
        photo_library = self.plex_server.library.section('Photos')
        title = f'{title} {year}' if year else title
        albums = photo_library.searchAlbums(title=title)
        if len(albums) == 0:
            albums = photo_library.searchAlbums(title=title)
        for album in albums:
            photos.extend(album.photos())
        return photos

    def __get_photos_by_date(self, month, year):
        # Default to entire year
        day_from = '01'
        month_from = '01'
        day_to = '31'
        month_to = '12'

        if month:
            dte = datetime.strptime(f'1 {month} {year}', '%d %B %Y')
            month_to = dte.month
            month_from = dte.month
            dte = dte + relativedelta(months=1) - relativedelta(days=1)
            day_to = dte.day

        photo_library = self.plex_server.library.section('Photos')
        return photo_library.search(filters={'originallyAvailableAt>>=': f'{year}-{month_from}-{day_from}',
                                             'originallyAvailableAt<<=': f'{year}-{month_to}-{day_to}'})

    @staticmethod
    def _map_plex_type(media_type):
        if media_type == 'song':
            return 'track'
        if media_type == 'video':
            return 'movie'
        return media_type
