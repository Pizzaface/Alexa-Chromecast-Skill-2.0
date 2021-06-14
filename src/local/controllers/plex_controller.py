import logging
import os
import socket
import ssl
import time
from typing import Optional

import requests
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from pychromecast.controllers.plex import PlexController

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PlexControllerError(Exception):
    pass


class MyPlexController(PlexController):

    @property
    def play_list(self):
        return self._play_list

    @property
    def plex_server(self):
        if self.__plex_server:
            return self.__plex_server
        else:
            self.__plex_server = self.__get_plex_server()
            return self.__plex_server

    def get_playing_item(self):
        if self.status.player_is_idle:
            return None
        # On occasion content_id is not found
        content_id = None
        for i in range(3):
            content_id = self.status.content_id
            if content_id:
                break
            time.sleep(1)
        return self.plex_server.fetchItem(content_id)

    def __init__(self):
        self._play_list = []
        self.__plex_server = None
        self._subtitle_code = os.environ.get('PLEX_SUBTITLE_LANG', 'eng')
        super().__init__()

    def get_media_index(self):
        return self.status.media_custom_data.get("mediaIndex", 0)

    def get_part_index(self):
        return self.status.media_custom_data.get("partIndex", 0)

    def play(self):
        if self.status.player_is_idle and self.status.content_id:
            # Displaying item - so play it
            item = self.plex_server.fetchItem(self.status.content_id)
            self.resume_playing(item)
        else:
            super().play()

    def stop(self):
        if not self.status.player_is_idle and self.status.content_id:
            item = self.plex_server.fetchItem(self.status.content_id)
            self.show_media(item)
        else:
            super().stop()

    def add_playlist_items(self, items):
        self._play_list = items

    def clear_playlist(self):
        self._play_list = []

    def search(self, title, limit=None):
        return self.plex_server.search(title, limit=limit)

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
        hostname = os.environ.get('PLEX_HOST')
        port = os.environ.get('PLEX_PORT')
        port = int(port) if port else False
        token = os.environ.get('PLEX_TOKEN')
        if not hostname or not port or not token:
            msg = 'Plex config is not set, set these in .custom_env'
            logger.warning(msg)
            raise PlexControllerError(msg)

        logger.info(f'Plex Host: {hostname}, Port: {port}')
        logger.info('Looking up Plex server certificate...')
        cert_common_name = cls.__get_ssl_cert_name(hostname, port)
        plex_address = f'https://{hostname.replace(".", "-")}{cert_common_name}:{port}'
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

    def play_plex(self, video_title):
        # Find best match
        items = self.search(video_title)
        media = False
        for item in items:
            if item.TYPE == 'show':
                # Get last unwatched one
                media = next((episode for episode in item.episodes() if not episode.isWatched), False)
            if not media and item.TYPE == 'movie':
                media = item
            if not media and item.TYPE == 'episode':
                media = item
            if media:
                break
        self.resume_playing(media)

    def find_plex(self, video_title):
        # Find best match
        items = self.search(video_title)
        self.add_playlist_items(items)
        media = False
        for item in items:
            if item.TYPE == 'show':
                # Get last unwatched one
                media = next((episode for episode in item.episodes() if not episode.isWatched), False)
            if not media and item.TYPE == 'movie':
                media = item
            if not media and item.TYPE == 'episode':
                media = item
            if media:
                break
        self.show_media(media)

    def resume_playing(self, media):
        offset = media.viewOffset / 1000
        self.block_until_playing(media, offset=offset)

    def change_audio_track(self):
        audio_streams = self.get_audio_streams()
        if len(audio_streams) == 1:
            # Nothing to do only 1 audio stream
            return

        # Switch to next stream after the current selected
        pos = next((i for i, x in enumerate(audio_streams) if x.selected), -1) + 1
        if pos > len(audio_streams):
            pos = 0
        self.set_audio_stream(audio_streams[pos].id)
        self.resume_playing(self.get_playing_item())

    def change_subtitle_track(self):
        subtitle_streams = self.get_subtitle_streams()
        pos = next((i for i, x in enumerate(subtitle_streams) if x.selected), -1) + 1
        if pos > len(subtitle_streams):
            pos = 0
        self.set_subtitle_stream(subtitle_streams[pos].id)
        self.resume_playing(self.get_playing_item())
