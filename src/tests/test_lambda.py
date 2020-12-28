import unittest
import pychromecast
from mock import Mock
from dotenv import load_dotenv
from os.path import join, dirname
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../src")

class SlotValue:
    def __init__(self, value, resolutions=False):
        self.value = value
        self.resolutions = resolutions

class MockResponseBuilder:

    def __init__(self):
        self.ask_text = ''
        self.speak_text = ''
        self.card = None

    def speak(self, text):
        self.speak_text = text
        return self

    def ask(self, text):
        self.speak_text = text
        return self

    def set_card(self, card):
        self.card = card
        return self

    @property
    def response(self):
        return self

class TestChromecast(unittest.TestCase):
    
    def setUp(self):
        dotenv_path = join(dirname(__file__), '.testenv')
        # Load file from the path.
        load_dotenv(dotenv_path)

    def test_play_trailer(self):
        from lambda_function.main import PlayTrailerIntentHandler
        req = PlayTrailerIntentHandler()
        req.publish_command_to_sns = Mock()

        #Mock handler inputs
        handler_input = Mock()
        handler_input.response_builder = MockResponseBuilder()
        handler_input.request_envelope.request.intent.slots = {
            'movie': SlotValue('Matrix'),
            'room': SlotValue('Sala de Estar')
            }
        response = req.handle(handler_input)
        self.assertTrue('reproduciendo' in response.speak_text.lower())
