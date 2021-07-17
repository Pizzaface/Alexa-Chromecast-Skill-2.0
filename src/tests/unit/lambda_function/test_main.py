import unittest
from typing import Optional, Dict
from unittest.mock import Mock, patch

from ask_sdk_model import Response

from lambda_function import utils
from lambda_function.lang.language import Language, Key
from tests.utils import patch_path


class SlotValue:
    def __init__(self, value, resolutions=False):
        self.value = value
        self.resolutions = resolutions


class MockResponseBuilder(Response):

    def __init__(self):
        self.ask_text = ''
        self.speak_text = ''
        self.card = None

    def speak(self, text):
        self.speak_text = text
        return self

    def ask(self, text):
        self.ask_text = text
        return self

    def set_card(self, card):
        self.card = card
        return self

    @property
    def response(self):
        return self


class TestMain(unittest.TestCase):

    @staticmethod
    def get_persistent_session_attribute(handler_input, name, default):
        return 'test room'

    @staticmethod
    def set_persistent_session_attribute(handler_input, name, value):
        pass

    def setUp(self):
        self.handler_input = Mock()
        self.handler_input.response_builder = MockResponseBuilder()
        self.handler_input.request_envelope.context.system.device.device_id = 'test_device_id'
        self.handler_input.request_envelope.request.locale = 'en-AU'
        self.language = Language('en-AU')

    @staticmethod
    def __slot_to_dict(slot_values: Dict[str, SlotValue]):
        return {key: slot.value for key, slot in slot_values.items()}

    def __test_dict_values(self, data, values):
        self.assertEqual(len(values), len(data))
        for key, value in values.items():
            self.assertEqual(value, data[key])

    def __test_speech_values(self, output, strings):
        for a_string in strings:
            self.assertTrue(a_string in output)

    def test_no_room(self):
        from lambda_function.main import PlayPhotosIntentHandler
        req = PlayPhotosIntentHandler()
        req.publish_command_to_sns = Mock()

        # Mock handler inputs
        self.handler_input.request_envelope.request.intent.slots = {
            'play': SlotValue('play'),
            'year': SlotValue('2012')
        }
        with patch(patch_path(utils.get_persistent_session_attribute), Mock(return_value=False)):
            resp: Optional[MockResponseBuilder] = req.handle(self.handler_input)
            self.assertTrue(self.language.get(Key.SetTheRoom) in resp.speak_text)

    def test_set_room(self):
        from lambda_function.main import SetRoomIntentHandler
        req = SetRoomIntentHandler()
        req.publish_command_to_sns = Mock()

        # Mock handler inputs
        self.handler_input.request_envelope.request.intent.slots = {
            'room': SlotValue('media room')
        }
        with patch(patch_path(utils.get_persistent_session_attribute), Mock(return_value='media room')):
            with patch(patch_path(utils.set_persistent_session_attribute), Mock()):
                resp: Optional[MockResponseBuilder] = req.handle(self.handler_input)
                self.assertTrue(self.language.get(Key.ControlRoom, room='media room') in resp.speak_text)

    def test_photos_play_year(self):
        from lambda_function.main import PlayPhotosIntentHandler
        req = PlayPhotosIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'year': SlotValue('2012')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlayPhotosByYear, play='Playing', year='2012'), resp.speak_text)

    def test_photos_play_month_year(self):
        from lambda_function.main import PlayPhotosIntentHandler
        req = PlayPhotosIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'month': SlotValue('august'),
            'year': SlotValue('2012')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlayPhotosByDate, play='Playing', year='2012', month='august'),
                         resp.speak_text)

    def test_photos_play_bad_month_year(self):
        from lambda_function.main import PlayPhotosIntentHandler
        req = PlayPhotosIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'month': SlotValue('christmas'),
            'year': SlotValue('2012')
        }
        passed_values = self.__slot_to_dict(slot_values)
        del passed_values['month']
        passed_values['title'] = 'christmas'
        resp = self.__test_values_passed(req, slot_values, passed_values)
        self.assertEqual(self.language.get(Key.PlayPhotosByEvent, play='Playing', year='2012', title='christmas'),
                         resp.speak_text)

    def test_photos_play_title(self):
        from lambda_function.main import PlayPhotosIntentHandler
        req = PlayPhotosIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'title': SlotValue('christmas')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlayPhotosByTitle, play='Playing', title='christmas'), resp.speak_text)

    def test_media_play_movie(self):
        from lambda_function.main import PlayMediaIntentHandler
        req = PlayMediaIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'type': SlotValue('movie'),
            'title': SlotValue('the matrix')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlayMovie, play='Playing', title='the matrix'), resp.speak_text)

    def test_media_play_show(self):
        from lambda_function.main import PlayMediaIntentHandler
        req = PlayMediaIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'type': SlotValue('show'),
            'title': SlotValue('mythic quest')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlayShow, play='Playing', show='mythic quest'), resp.speak_text)

    def test_media_play_episode(self):
        from lambda_function.main import PlayMediaIntentHandler
        req = PlayMediaIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'type': SlotValue('episode'),
            'title': SlotValue('breaking brad'),
            'tvshow': SlotValue('mythic quest')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlayEpisode, play='Playing', title='breaking brad', show='mythic quest'),
                         resp.speak_text)

    def test_media_play_episode_mix(self):
        from lambda_function.main import PlayMediaIntentHandler
        req = PlayMediaIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'type': SlotValue('episode'),
            'title': SlotValue('season one episode twenty three'),
            'tvshow': SlotValue('mythic quest')
        }
        passed_values = self.__slot_to_dict(slot_values)
        del passed_values['title']
        passed_values['epnum'] = '23'
        passed_values['seasnum'] = '1'
        resp = self.__test_values_passed(req, slot_values, passed_values)
        self.assertEqual(self.language.get(Key.PlayEpisodeNumber, play='Playing', episode='23', season='1',
                                           show='mythic quest'), resp.speak_text)

    def test_media_play_season(self):
        from lambda_function.main import PlayEpisodeIntentHandler
        req = PlayEpisodeIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'type': SlotValue('episode'),
            'seasnum': SlotValue('1'),
            'tvshow': SlotValue('mythic quest')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlaySeason, play='Playing', season='1',
                                           show='mythic quest'), resp.speak_text)

    def test_media_play_episode_number(self):
        from lambda_function.main import PlayEpisodeIntentHandler
        req = PlayEpisodeIntentHandler()
        slot_values = {
            'play': SlotValue('play'),
            'type': SlotValue('episode'),
            'epnum': SlotValue('7'),
            'seasnum': SlotValue('3'),
            'tvshow': SlotValue('mythic quest')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.PlayEpisodeNumber, play='Playing', episode='7', season='3',
                                           show='mythic quest'), resp.speak_text)

    def __test_values_passed(self, request, slot_values, passed_values):
        request.publish_command_to_sns = Mock()
        with patch(patch_path(utils.get_persistent_session_attribute), self.get_persistent_session_attribute):
            self.handler_input.request_envelope.request.intent.slots = slot_values
            response: Optional[MockResponseBuilder] = request.handle(self.handler_input)
        data = request.get_data(self.handler_input)
        self.__test_dict_values(data, passed_values)
        return response

    def test_quality_low(self):
        from lambda_function.main import QualityIntentHandler
        req = QualityIntentHandler()
        slot_values = {
            'quality': SlotValue('low')
        }
        self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))

    def test_quality_720p(self):
        from lambda_function.main import QualityIntentHandler
        req = QualityIntentHandler()
        slot_values = {
            'quality': SlotValue('720p')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.__test_speech_values(resp.speak_text, [
            'seven twenty pea'
        ])
        self.assertTrue('720p' in resp.card.content)

    def test_quality_increase(self):
        from lambda_function.main import QualityIntentHandler
        req = QualityIntentHandler()
        slot_values = {
            'raise_lower': SlotValue('up')
        }
        self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))

    def test_quality_decrease(self):
        from lambda_function.main import QualityIntentHandler
        req = QualityIntentHandler()
        slot_values = {
            'raise_lower': SlotValue('down')
        }
        self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))

    def test_volume_set(self):
        from lambda_function.main import VolumeChangeIntentHandler
        req = VolumeChangeIntentHandler()
        slot_values = {
            'volume': SlotValue('5')
        }
        resp = self.__test_values_passed(req, slot_values, {'volume': 5})
        self.assertEqual(self.language.get(Key.SetVolume, volume=5), resp.speak_text)

    def test_volume_too_high(self):
        from lambda_function.main import VolumeChangeIntentHandler
        req = VolumeChangeIntentHandler()
        slot_values = {
            'volume': SlotValue('11')
        }
        resp = self.__test_values_passed(req, slot_values, {'volume': 11})
        self.assertEqual(self.language.get(Key.ErrorSetVolumeRange), resp.speak_text)

    def test_volume_too_low(self):
        from lambda_function.main import VolumeChangeIntentHandler
        req = VolumeChangeIntentHandler()
        slot_values = {
            'volume': SlotValue('-1')
        }
        resp = self.__test_values_passed(req, slot_values, {'volume': -1})
        self.assertEqual(self.language.get(Key.ErrorSetVolumeRange), resp.speak_text)

    def test_volume_increase(self):
        from lambda_function.main import VolumeChangeIntentHandler
        req = VolumeChangeIntentHandler()
        slot_values = {
            'raise_lower': SlotValue('up')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.IncreaseVolume), resp.speak_text)

    def test_volume_decrease(self):
        from lambda_function.main import VolumeChangeIntentHandler
        req = VolumeChangeIntentHandler()
        slot_values = {
            'raise_lower': SlotValue('down')
        }
        resp = self.__test_values_passed(req, slot_values, self.__slot_to_dict(slot_values))
        self.assertEqual(self.language.get(Key.DecreaseVolume), resp.speak_text)

    def test_volume_none(self):
        from lambda_function.main import VolumeChangeIntentHandler
        req = VolumeChangeIntentHandler()
        slot_values = {}
        resp = self.__test_values_passed(req, slot_values, {'raise_lower': 'up'})
        self.assertEqual(self.language.get(Key.IncreaseVolume), resp.speak_text)


if __name__ == '__main__':
    unittest.main()
