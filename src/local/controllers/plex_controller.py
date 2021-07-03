import logging
import os
import socket
import ssl
import time
from typing import Optional, List

import requests
from plexapi.exceptions import Unauthorized, NotFound
from plexapi.server import PlexServer
from pychromecast.controllers.plex import PlexController, media_to_chromecast_command

from local import utils, constants
from local.controllers.media_controller import MediaExtensions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PlexControllerError(Exception):
    pass


class MyPlexController(PlexController, MediaExtensions):

    @property
    def plex_server(self):
        if self.__plex_server:
            return self.__plex_server
        else:
            self.__plex_server = self.__get_plex_server()
            return self.__plex_server

    def __init__(self):
        self.__current_item = None
        self.__plex_server = None
        self._subtitle_code = os.environ.get(constants.ENV_PLEX_SUBTITLE_LANG, 'eng')
        self.__shuffle = 0
        self.__loop = 0
        super().__init__()

    def get_playing_item(self):
        content_id = self._get_content_id()
        if content_id:
            return self.plex_server.fetchItem(content_id)
        return None

    def get_current_item(self):
        return self.__current_item

    def __shuffle_it(self):
        item = self.get_current_item()
        if item:
            play_queue = self.plex_server.createPlayQueue(item, shuffle=self.__shuffle, repeat=self.__loop)
            self.resume_playing(play_queue)
        else:
            logger.warning('No current item to shuffle.')

    def shuffle_on(self):
        self.__shuffle = 1
        self.__shuffle_it()

    def shuffle_off(self):
        self.__shuffle = 0
        self.__shuffle_it()

    def loop(self, on=True):
        self.__loop = 1 if on else 0
        item = self.get_current_item()
        if item:
            play_queue = self.plex_server.createPlayQueue(item, shuffle=self.__shuffle, repeat=self.__loop)
            self.resume_playing(play_queue)
        else:
            logger.warning('No current item to shuffle.')

    def play_previous(self, action=''):
        if self.status.current_time >= 10:
            self.rewind()
        self.previous()

    def play_next(self, action=''):
        self.next()

    def get_media_index(self):
        return self.status.media_custom_data.get("mediaIndex", 0)

    def get_part_index(self):
        return self.status.media_custom_data.get("partIndex", 0)

    def play(self):
        if not self.status.player_is_playing or not self.status.player_is_paused:
            self.resume_playing(self.build_play_list())
            return
        super().play()

    def stop(self):
        super().stop()
        self.show_media(self.get_current_item())

    def _set_current_item(self, item):
        self.__current_item = item
        self.__shuffle = 0
        self.__loop = 0

    def search(self, title, media_type='', limit=10):
        items = self.plex_server.search(title, mediatype=media_type, limit=limit)
        return items

    def block_until_playing(self, media=None, timeout=None, **kwargs):
        return super().block_until_playing(media=media, timeout=timeout, **kwargs)

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
        self.resume_playing(self.get_playing_item())

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

    def play_item(self, options):
        self._play_item(options, find=False)

    @staticmethod
    def get_next_episode_to_watch(show):
        # Get the last episode that was being watched, or the next unwatched one
        # Otherwise just return the last one
        episodes: List = show.episodes()
        episodes.reverse()
        pos = next((i for i, episode in enumerate(episodes) if episode.isWatched), 0)
        if pos == 0 or episodes[pos].viewOffset != 0:
            # Return currently watching episode, or the last episode
            return episodes[pos]
        # Return the next episode, if there is one
        pos = pos - 1 if pos > 0 else 0
        return episodes[pos]

    def _play_item(self, options, find=False):
        title = utils.get_dict_val(options, 'title', '')
        tv_show = utils.get_dict_val(options, 'tv_show', '')
        media_type = utils.get_dict_val(options, 'type', '')

        if media_type == 'song':
            media_type = 'track'
        if media_type in ['show', 'episode']:
            show, episode = self.__get_show_episode(media_type, options)
            if not show:
                logger.info(f'Unable to find a matching show for: {tv_show if tv_show else title}')
                return
            play_media = episode if episode else show
        else:
            items = self.search(title, media_type=media_type, limit=10)
            if len(items) == 0:
                logger.info(f'Unable to find any item in Plex matching title: {title}')
                return
            play_media = items[0]
        self._set_current_item(play_media)
        if find:
            super().stop()
            self.show_media(play_media)
        else:
            self.resume_playing(self.build_play_list())

    def show_media(self, item=None, **kwargs):
        # Tracks don't display in show details, fudge this by playing the track, then pausing it
        if item.TYPE == 'track':
            self.resume_playing(item)
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

    def find_item(self, options):
        self._play_item(options, True)

    def resume_playing(self, media, **kwargs):
        if 'viewOffset' in vars(media):
            offset = media.viewOffset / 1000
            self.block_until_playing(media, offset=offset, **kwargs)
        else:
            self.block_until_playing(media, **kwargs)

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
        self.resume_playing(self.get_playing_item())

    def change_subtitle_track(self):
        subtitle_streams = self.get_subtitle_streams()
        pos = next((i for i, x in enumerate(subtitle_streams) if x.selected), -1) + 1
        if pos >= len(subtitle_streams):
            pos = 0
        self.set_subtitle_stream(subtitle_streams[pos].id)
        self.resume_playing(self.get_playing_item())

    def __get_show_episode(self, media_type, options):

        ep_num = utils.get_dict_val(options, 'epnum', '')
        seas_num = utils.get_dict_val(options, 'seasnum', '')
        tv_show = utils.get_dict_val(options, 'tvshow', '')
        title = utils.get_dict_val(options, 'title', '')

        show = None
        episode = None
        found_episodes = []
        if media_type == 'episode' and not (ep_num and seas_num):
            found_episodes = self.search(title, media_type='episode', limit=10)
        show_title = title if media_type == 'show' else tv_show
        found_shows = self.search(show_title, media_type='show', limit=10)
        if len(found_shows) == 0:
            # Try a broader search
            items = self.search(show_title, limit=10)
            for item in items:
                if item.TYPE == 'episode':
                    found_shows = [item.show()]
                    break
        if found_shows:
            show = found_shows[0]
            if ep_num and seas_num:
                try:
                    episode = show.get(season=seas_num, episode=ep_num)
                except NotFound:
                    logger.warning(f'Unable to find Season {seas_num}, Episode {ep_num} for show: {show}')
            elif found_episodes:
                for ep in found_episodes:
                    if ep.grandparentKey == show.key:
                        episode = ep
                        break
            else:
                episode = None
        elif found_episodes:
            episode = found_episodes[0]
            show = episode.show()

        logger.info(f"Selected show: {show}, episode: {episode}")
        return show, episode

    def build_play_list(self):
        item = self.__current_item
        if item.TYPE == 'episode':
            episodes = self.__get_episodes(item.show(), item, count=20)
            play_list = self.plex_server.createPlayQueue(episodes, startItem=item)
        elif item.TYPE == 'show':
            episode = self.get_next_episode_to_watch(item)
            episodes = self.__get_episodes(item, episode, count=20)
            play_list = self.plex_server.createPlayQueue(episodes, startItem=episode)
        elif item.TYPE in ['artist', 'album']:
            play_list = self.plex_server.createPlayQueue(item, shuffle=1)
        else:
            play_list = self.plex_server.createPlayQueue(item)
        return play_list

    def __get_episodes(self, show, episode, count):
        eps = show.episodes()
        if len(eps) <= count:
            return eps
        pos = eps.index(episode)
        length = len(eps)
        end_pos = min(max(pos + count//2 + 1, count + 1), length)
        start_pos = max(pos - count//2 - (count//2 - min(length - end_pos, 0)), 0)
        return eps[start_pos:end_pos]
