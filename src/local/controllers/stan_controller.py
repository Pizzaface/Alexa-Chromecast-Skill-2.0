import logging

from pychromecast.controllers import BaseController
from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatusListener, CastStatus

from ..apis import stan

APP_NAMESPACE = "urn:x-cast:au.com.streamco.media.chromecast"
APP_STAN = '08CAA3D4'


class StanController(BaseController, CastStatusListener):
    """ Controller to interact with Supla namespace. """

    def new_cast_status(self, status: CastStatus):
        self.logger.debug('****')
        self.logger.debug(status)
        self.logger.debug('****')

    def new_media_status(self, status: MediaStatus):
        self.logger.debug('****')
        self.logger.debug(f'New Media Status Event: {status}')
        self.logger.debug('****')

    def __init__(self):
        super().__init__(APP_NAMESPACE, APP_STAN)
        self.logger = logging.getLogger(__name__)
        self.api = stan.API()
        self.api.login('julie.mcneish@gmail.com', 'xxxxxxxx')

    def receive_message(self, message, data: dict):
        self.logger.debug(message)
        self.logger.debug(data)

    def play_media(self):
        jw_token = self.api.userdata.get('token')
        msg = {
            'type': 'LOAD',
            'requestId': 1,
            'media': {
                'contentId': 'https://api.stan.com.au/concurrency/v1/media/3019990/hd/dash/high/3538995',
                'streamType': 'BUFFERED',
                'contentType': 'application/dash+xml',
                "autoplay": True,
                "currentTime": 0,
                "activeTrackIds": None,
                'customData': {
                    'guid': '3019990',
                    'jwToken': jw_token,
                    'programId': '3019990',
                    'programType': 'movie',
                    'mainURL': 'https://api.stan.com.au/cat/v12/programs/3019990.json',
                    'userId': 'd33a09cfb69947fbb6a9b33eebe72807',
                    'profileId': 'd33a09cfb69947fbb6a9b33eebe72807',
                    'time': 0,
                    'preloadTime': 0,
                    'totalDuration': 9137,
                    'quality': 'auto',
                    'audioLanguage': 'en',
                    'audioType': 'main',
                    'audioLayout': '',
                    'autoCueEnabled': True,
                    'userInactivityEnabled': True,
                    'closedCaptionsEnabled': False,
                    'chaptersEnabled': True,
                    'textTracks': [],
                    'activeTextTrack': None
                }
            }
        }
        self.namespace = 'urn:x-cast:com.google.cast.media'
        try:
            self.send_message(msg, inc_session_id=True)
        finally:
            self.namespace = APP_NAMESPACE

