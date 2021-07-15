import os
import logging
from typing import Dict, List

import boto3
import json
from word2number import w2n
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_s3.adapter import S3Adapter
from ask_sdk_core.skill_builder import CustomSkillBuilder

from ask_sdk_model import Response
from ask_sdk_model import ui
import lambda_function.utils as utils
from lambda_function.lang.language import Language, Key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AWS_SNS_ARN = os.getenv('AWS_SNS_ARN')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')


def get_play_response(language, play_type):
    result = language.get(Key.Playing)
    if play_type == 'shuffle':
        result = language.get(Key.Shuffling)
    elif play_type == 'find':
        result = language.get(Key.Finding)
    return result


class SNSPublishError(Exception):
    """
    If something goes wrong with publishing to SNS
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input) or ask_utils.is_intent_name(
            'AMAZON.NavigateHomeIntent')(handler_input)

    def handle(self, handler_input):
        language = Language(handler_input.request_envelope.request.locale)
        card_title = language.get(Key.CardTitle)
        speak_output = language.get(Key.Help)
        return (
            handler_input
                .response_builder
                .speak(speak_output)
                .card(ui.SimpleCard(card_title, speak_output))
                .response
        )


class BaseIntentHandler(AbstractRequestHandler):
    """
    Base handler for all intents
    """
    def get_action(self):
        raise NotImplementedError

    @staticmethod
    def get_slot_values(params: List[str], handler_input: HandlerInput):
        results = {
            param: utils.get_slot_value(handler_input, param, '') for param in params
        }
        return {key: value for key, value in results.items() if value}

    def get_intent_name(self):
        return self.__class__.__name__.replace('Handler', '')

    def match_other_intent_names(self):
        return []

    def can_handle(self, handler_input: HandlerInput):
        intents = [self.get_intent_name()]
        other_intents = self.match_other_intent_names()
        if other_intents:
            intents.extend(other_intents)
        for intent in intents:
            if ask_utils.is_intent_name(intent)(handler_input):
                return True
        return False

    def get_data(self, handler_input: HandlerInput):
        return {}

    def get_response(self, language: Language, data: Dict):
        return language.get(Key.Ok)

    def get_card_response(self, language: Language, data: Dict):
        return self.get_response(language, data)

    def handle(self, handler_input: HandlerInput):
        language = Language(handler_input.request_envelope.request.locale)
        card_title = language.get(Key.CardTitle)
        room = utils.get_slot_value(handler_input, 'room', '')
        if room and room.lower().startswith('the '):
            room = room[4:]

        device_id = handler_input.request_envelope.context.system.device.device_id

        if not room:
            room = utils.get_persistent_session_attribute(handler_input, 'DEVICE_' + device_id, False)
            if not room:
                speak_output = language.get(Key.SetTheRoom)
                return (
                    handler_input
                        .response_builder
                        .speak(speak_output)
                        .ask(language.get(Key.ShortSetTheRoom))
                        .set_card(ui.SimpleCard(card_title, speak_output))
                        .response
                )

        try:
            data = self.get_data(handler_input)
            self.publish_command_to_sns(room, self.get_action(), data)
            speak_output = self.get_response(language, data)
            card_output = self.get_card_response(language, data)
            return (
                handler_input
                    .response_builder
                    .speak(speak_output)
                    .set_card(ui.SimpleCard(card_title, card_output))
                    .response
            )
        except SNSPublishError as error:
            logger.error(language.get(Key.LogErrorSnsPublish), exc_info=error)
            speak_output = language.get(Key.ErrorSnsPublish) + error.message
            return (
                handler_input
                    .response_builder
                    .speak(speak_output)
                    .set_card(ui.SimpleCard(card_title, speak_output))
                    .response
            )

    @staticmethod
    def publish_command_to_sns(room: str, command: str, data: Dict):
        message = {
            "handler_name": "chromecast",
            "room": room,
            "command": command,
            "data": data
        }
        sns_client = boto3.client("sns")
        response = sns_client.publish(
            TargetArn=AWS_SNS_ARN,
            Message=json.dumps({"default": json.dumps(message)}),
            MessageStructure="json"
        )

        print(response["ResponseMetadata"])

        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            message = "SNS Publish returned {} response instead of 200.".format(
                response["ResponseMetadata"]["HTTPStatusCode"])
            raise SNSPublishError(message)


class SetRoomIntentHandler(BaseIntentHandler):

    def get_action(self):
        # Nothing to do
        pass

    def handle(self, handler_input):
        device_id = handler_input.request_envelope.context.system.device.device_id
        room = utils.get_slot_value(handler_input, 'room')  # Must have a value enforced by Alexa dialog
        utils.set_persistent_session_attribute(handler_input, 'DEVICE_' + device_id, room)
        handler_input.attributes_manager.save_persistent_attributes()

        language = Language(handler_input.request_envelope.request.locale)
        speak_output = language.get(Key.ControlRoom, room=room)
        card_title = language.get(Key.CardTitle)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_card(ui.SimpleCard(card_title, speak_output))
                .response
        )


class OpenIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'open'

    def get_data(self, handler_input):
        return self.get_slot_values(['app'], handler_input)


class PlayIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.ResumeIntent']

    def get_action(self):
        return 'play'


class PauseIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.PauseIntent']

    def get_action(self):
        return 'pause'


class StopIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.StopIntent']

    def get_action(self):
        return 'stop'


class SetVolumeIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'set-volume'

    def get_data(self, handler_input):
        volume = int(utils.get_slot_value(handler_input, 'volume'))
        return {"volume": volume}

    def get_response(self, language: Language, data: Dict):
        volume = data['volume']
        if volume > 10 or volume < 0:
            return language.get(Key.ErrorSetVolumeRange)
        return super().get_response(language, data)


class VolumeChangeIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'set-volume'

    def get_data(self, handler_input):
        return self.get_slot_values(['raise_lower'], handler_input)


class PreviousIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.PreviousIntent']

    def get_action(self):
        return 'play-previous'

    def get_data(self, handler_input):
        return self.get_slot_values(['action'], handler_input)


class NextIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.NextIntent']

    def get_action(self):
        return 'play-next'

    def get_data(self, handler_input):
        return self.get_slot_values(['action'], handler_input)


class ShuffleOnIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.ShuffleOnIntent']

    def get_action(self):
        return 'shuffle-on'


class ShuffleOffIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.ShuffleOffIntent']

    def get_action(self):
        return 'shuffle-off'


class LoopOnIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.LoopOnIntent']

    def get_action(self):
        return 'loop-on'


class LoopOffIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.LoopOffIntent']

    def get_action(self):
        return 'loop-off'


class RewindIntentHandler(BaseIntentHandler):

    def get_action(self):
        return 'rewind'

    def get_data(self, handler_input):
        return {
            "duration": utils.get_slot_value(handler_input, 'duration', 'PT15S')
        }


class MuteIntentHandler(BaseIntentHandler):

    def get_action(self):
        return 'mute'


class UnMuteIntentHandler(BaseIntentHandler):

    def get_action(self):
        return 'unmute'


class RestartIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'rewind'

    def get_data(self, handler_input):
        return {
            "direction": utils.get_slot_value(handler_input, 'direction', '')
        }


class FastForwardIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'fast-forward'

    def get_data(self, handler_input):
        return {
            "duration": utils.get_slot_value(handler_input, 'duration', 'PT15S'),  # 15 seconds
        }


class PlayEpisodeIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-media'

    def get_data(self, handler_input):
        params = ['play', 'epnum', 'seasnum', 'tvshow', 'app', 'room']
        result = self.get_slot_values(params, handler_input)
        result['type'] = 'episode'
        return result

    def get_response(self, language, data):
        if 'epnum' not in data and 'seasnum' not in data:
            return language.get(Key.ErrorEpisodeParams)
        play = get_play_response(language, data['play'])
        epnum = data['epnum'] if 'epnum' in data else ''
        seasnum = data['seasnum'] if 'seasnum' in data else ''
        tvshow = data["tvshow"]
        if epnum and seasnum:
            msg = language.get(Key.PlayEpisodeNumber, play=play, episode=epnum, season=seasnum, show=tvshow)
        elif seasnum:
            msg = language.get(Key.PlaySeason, play=play, season=seasnum, show=tvshow)
        else:
            msg = language.get(Key.PlayShow, play=play, show=tvshow)
        if 'app' in data.keys() and data['app']:
            msg += language.get(Key.OnApp, app=data['app'])
        if 'room' in data.keys() and data['room']:
            msg += language.get(Key.InRoom, room=data['room'])
        return msg


class PlayPhotosIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-photos'

    def get_data(self, handler_input):
        language = Language(handler_input.request_envelope.request.locale)
        params = ['play', 'month', 'year', 'title']
        result = self.get_slot_values(params, handler_input)
        month = result['month'] if 'month' in result else ''
        title = result['title'] if 'title' in result else ''
        if month and month.lower() not in language.get(Key.ListMonths):
            title = month + (' ' + title if title else '')
            del result['month']
            result['title'] = title
        return result

    def get_response(self, language, data):
        play = get_play_response(language, data['play'])
        year = data['year'] if 'year' in data else ''
        title = data['title'] if 'title' in data else ''
        month = data['month'] if 'month' in data else ''
        if month and year:
            return language.get(Key.PlayPhotosByDate, play=play, month=month, year=year)
        elif title and year:
            return language.get(Key.PlayPhotosByEvent, play=play, title=title, year=year)
        elif title:
            return language.get(Key.PlayPhotosByTitle, play=play, title=title)


class PlayMediaIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-media'

    def get_data(self, handler_input):
        params = ['play', 'app', 'room', 'title', 'type', 'tvshow']
        result = {
            param:
                utils.get_slot_value(handler_input, param, '').lower()
            for param in params
        }

        if result['tvshow'] and 'season' in result['title'] and 'episode' in result['title']:
            self.set_episode_and_season(result)
        return {key: value for key, value in result.items() if value}

    def get_response(self, language, data):
        if 'epnum' in data or 'seasnum' in data:
            return PlayEpisodeIntentHandler().get_response(language, data)

        title = data['title'] if 'title' in data.keys() else ''
        media_type = data['type'] if 'type' in data.keys() else ''
        tv_show = data['tvshow'] if 'tvshow' in data.keys() else ''

        play = get_play_response(language, data['play'])
        if media_type == 'playlist':
            msg = language.get(Key.PlayPlaylist, play=play, title=title)
        elif media_type == 'movie':
            msg = language.get(Key.PlayMovie, play=play, title=title)
        elif media_type == 'show':
            msg = language.get(Key.PlayShow, play=play, show=title)
        elif media_type == 'episode':
            msg = language.get(Key.PlayEpisode, play=play, title=title, show=tv_show)
        else:
            msg = language.get(Key.PlayTitle, play=play, title=title)
        if 'app' in data.keys() and data['app']:
            msg += language.get(Key.OnApp, app=data['app'])
        if 'room' in data.keys() and data['room']:
            msg += language.get(Key.InRoom, room=data['room'])
        return msg

    @staticmethod
    def set_episode_and_season(result):
        title = result['title']
        del result['title']
        result['type'] = 'episode'
        if title.startswith('season'):
            title = title.replace('season', '')
            title = title.split('episode')
            result['seasnum'] = str(w2n.word_to_num(title[0]))
            result['epnum'] = str(w2n.word_to_num(title[1]))
        else:
            title = title.replace('episode', '')
            title = title.split('season')
            result['epnum'] = str(w2n.word_to_num(title[0]))
            result['seasnum'] = str(w2n.word_to_num(title[1]))


class PlayMusicIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-media'

    def get_data(self, handler_input):
        params = ['play', 'app', 'room', 'title', 'song', 'album', 'artist', 'type']
        result = {
            param:
                utils.get_slot_value(handler_input, param, '').lower()
            for param in params
        }
        transform = ['song', 'album', 'artist']
        for trans in transform:
            if result[trans]:
                result['title'] = result[trans]
                result['type'] = trans
        return {key: value for key, value in result.items() if value}

    def get_response(self, language, data):
        title = data['title'] if 'title' in data.keys() else ''
        media_type = data['type'] if 'type' in data.keys() else ''

        play = get_play_response(language, data['play'])
        if media_type == 'song':
            msg = language.get(Key.PlaySong, play=play, title=title)
        elif media_type == 'album':
            msg = language.get(Key.PlaySongsByAlbum, play=play, album=title)
        elif media_type == 'artist':
            msg = language.get(Key.PlaySongsByArtist, play=play, artist=title)
        else:
            msg = language.get(Key.PlayTitle, play=play, title=title)
        if 'app' in data.keys() and data['app']:
            msg += language.get(Key.OnApp, app=data['app'])
        if 'room' in data.keys() and data['room']:
            msg += language.get(Key.InRoom, room=data['room'])
        return msg


class SubtitlesOnIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'subtitle-on'

    def get_response(self, language, data):
        return language.get(Key.SubtitlesOn)


class SubtitlesOffIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'subtitle-off'

    def get_response(self, language, data):
        return language.get(Key.SubtitlesOff)


class ChangeAudioIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'change-audio'

    def get_response(self, language, data):
        return language.get(Key.SwitchAudio)


class QualityIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'transcode'

    def get_data(self, handler_input):
        return self.get_slot_values(['raise_lower', 'quality'], handler_input)

    def get_card_response(self, language, data):
        if 'quality' in data:
            return language.get(Key.ChangeQuality, quality=data["quality"])
        return self.get_response(language, data)

    def get_response(self, language, data):
        if 'raise_lower' in data:
            if data['raise_lower'] == 'up':
                return language.get(Key.IncreaseQuality)
            else:
                return language.get(Key.DecreaseQuality)

        if 'quality' in data:
            quality = data['quality']
            if quality in ['1080p', '720p', '280p']:
                quality = language.get(Key['Speak' + quality])
            return language.get(Key.ChangeQuality, quality=quality)
        return language.get(Key.ErrorChangeQuality)


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        language = Language(handler_input.request_envelope.request.locale)
        speak_output = language.get(Key.Help)
        card_title = language.get(Key.CardTitle)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .card(ui.SimpleCard(card_title, speak_output))
                .response
        )


class CancelIntentHandler(AbstractRequestHandler):
    """
    Single handler for Cancel and Stop Intent.
    """

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        language = Language(handler_input.request_envelope.request.locale)
        speak_output = language.get(Key.Goodbye)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """
    Handler for Session End.
    """

    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """
    The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logger.error(exception, exc_info=True)
        language = Language(handler_input.request_envelope.request.locale)
        speak_output = language.get(Key.GeneralError)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.
try:
    s3_adapter = S3Adapter(bucket_name=AWS_S3_BUCKET)

    sb = CustomSkillBuilder(persistence_adapter=s3_adapter)

    sb.add_request_handler(LaunchRequestHandler())

    # Chromecast standard
    sb.add_request_handler(SetRoomIntentHandler())
    sb.add_request_handler(PauseIntentHandler())
    sb.add_request_handler(PlayIntentHandler())
    sb.add_request_handler(StopIntentHandler())
    sb.add_request_handler(SetVolumeIntentHandler())
    sb.add_request_handler(VolumeChangeIntentHandler())
    sb.add_request_handler(PreviousIntentHandler())
    sb.add_request_handler(NextIntentHandler())
    sb.add_request_handler(OpenIntentHandler())
    sb.add_request_handler(RewindIntentHandler())
    sb.add_request_handler(FastForwardIntentHandler())
    sb.add_request_handler(RestartIntentHandler())
    sb.add_request_handler(MuteIntentHandler())
    sb.add_request_handler(UnMuteIntentHandler())
    sb.add_request_handler(ShuffleOnIntentHandler())
    sb.add_request_handler(ShuffleOffIntentHandler())
    sb.add_request_handler(LoopOnIntentHandler())
    sb.add_request_handler(LoopOffIntentHandler())

    # Plex specific
    sb.add_request_handler(QualityIntentHandler())
    sb.add_request_handler(ChangeAudioIntentHandler())
    sb.add_request_handler(SubtitlesOnIntentHandler())
    sb.add_request_handler(SubtitlesOffIntentHandler())
    sb.add_request_handler(PlayMediaIntentHandler())
    sb.add_request_handler(PlayEpisodeIntentHandler())
    sb.add_request_handler(PlayMusicIntentHandler())
    sb.add_request_handler(PlayPhotosIntentHandler())

    sb.add_request_handler(HelpIntentHandler())
    sb.add_request_handler(CancelIntentHandler())
    sb.add_request_handler(SessionEndedRequestHandler())

    sb.add_request_handler(IntentReflectorHandler())
    sb.add_exception_handler(CatchAllExceptionHandler())

    lambda_handler = sb.lambda_handler()

except Exception as e:
    logger.exception('Unexpected error')
    raise e
