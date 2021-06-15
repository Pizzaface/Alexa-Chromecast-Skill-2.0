import os
import logging
import boto3
import json
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_s3.adapter import S3Adapter
from ask_sdk_core.skill_builder import CustomSkillBuilder

from ask_sdk_model import Response
from ask_sdk_model import ui
import lambda_function.utils as utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AWS_SNS_ARN = os.getenv('AWS_SNS_ARN')
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
CARD_TITLE = 'Alexa Chromecast Controller'

HELP_TEXT = '''
    Welcome to the Alexa Chromecast controller. This skill allows you to control your Chromecasts in different rooms.
    An Alexa Device can be configured to control a Chromecast in a particular room.
    Then you can say something like: Alexa, ask Chromecast to play, or: Alexa, ask Chromecast to pause.
    Or you can control a specific room, by saying something like: Alexa, ask Chromecast to play in the media room.
    '''


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
        speak_output = HELP_TEXT
        return (
            handler_input.response_builder
                .speak(speak_output)
                .card(ui.SimpleCard(CARD_TITLE, speak_output))
                .response
        )


class BaseIntentHandler(AbstractRequestHandler):
    """
    Base handler for all intents
    """

    def get_action(self):
        raise NotImplementedError

    def get_intent_name(self):
        return self.__class__.__name__.replace('Handler', '')

    def match_other_intent_names(self):
        return []

    def can_handle(self, handler_input):
        intents = [self.get_intent_name()]
        other_intents = self.match_other_intent_names()
        if other_intents:
            intents.extend(other_intents)
        for intent in intents:
            if ask_utils.is_intent_name(intent)(handler_input):
                return True
        return False

    def get_data(self, handler_input):
        return {}

    def get_response(self, data):
        return 'Ok'

    def handle(self, handler_input):
        room = utils.get_slot_value(handler_input, 'room', False)
        device_id = handler_input.request_envelope.context.system.device.device_id

        if not room:
            room = utils.get_persistent_session_attribute(handler_input, 'DEVICE_' + device_id, False)
            if not room:
                speak_output = 'I need to set the room of the Chromecast that this Alexa device will control. Please say something like: set room to media room.'
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask('Please set the Chromecasts room, by saying something like: set room to media room.')
                        .set_card(ui.SimpleCard(CARD_TITLE, speak_output))
                        .response
                )

        try:
            data = self.get_data(handler_input)
            self.publish_command_to_sns(room, self.get_action(), data)
            speak_output = self.get_response(data)
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .set_card(ui.SimpleCard(CARD_TITLE, speak_output))
                    .response
            )
        except SNSPublishError as error:
            logger.error('Sending command to the Chromecast failed', exc_info=error)
            speak_output = 'There was an error sending the command to the Chromecast. ' + error.message
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .set_card(ui.SimpleCard(CARD_TITLE, speak_output))
                    .response
            )

    def publish_command_to_sns(self, room, command, data):
        message = {
            "handler_name": "chromecast",
            "room": room,
            "command": command,
            "data": data
        }
        sns_client = boto3.client("sns")
        # Disable check subscriptions - failed with a valid subscription
        # response = sns_client.list_subscriptions()
        # subscriptions = response['Subscriptions']
        # if len(subscriptions) == 0:
        #     raise SNSPublishError('No clients are subscribed.')
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
        pass

    def handle(self, handler_input):
        device_id = handler_input.request_envelope.context.system.device.device_id
        room = utils.get_slot_value(handler_input, 'room')  # Must have a value enforced by Alexa dialog
        utils.set_persistent_session_attribute(handler_input, 'DEVICE_' + device_id, room)
        handler_input.attributes_manager.save_persistent_attributes()
        speak_output = 'Ok, this Alexa device will control the Chromecast in the %s. To control another room you can say something like: Alexa, play in the media room.' % room
        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_card(ui.SimpleCard(CARD_TITLE, speak_output))
                .response
        )


class OpenIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'open'

    def get_data(self, handler_input):
        return {"app": utils.get_slot_value(handler_input, 'app')}


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
        if volume > 10 or volume < 0:
            return "Sorry, you can only set the volume between 0 and 10."
        return {"volume": volume}


class PreviousIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.PreviousIntent']

    def get_action(self):
        return 'play-previous'

    def get_data(self, handler_input):
        return {
            "action": utils.get_slot_value(handler_input, 'action', '')
        }


class NextIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.NextIntent']

    def get_action(self):
        return 'play-next'

    def get_data(self, handler_input):
        return {
            "action": utils.get_slot_value(handler_input, 'action', '')
        }


class RewindIntentHandler(BaseIntentHandler):

    def get_action(self):
        return 'rewind'

    def get_data(self, handler_input):
        return {
            "duration": utils.get_slot_value(handler_input, 'duration', '')
        }


class MuteIntentHandler(BaseIntentHandler):

    def get_action(self):
        return 'mute'


class UnMuteIntentHandler(BaseIntentHandler):

    def get_action(self):
        return 'unmute'


class RestartIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'restart'


class PlayTrailerIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-trailer'

    def get_data(self, handler_input):
        return {"title": utils.get_slot_value(handler_input, 'movie')}

    def get_response(self, data):
        return 'Playing trailer for %s' % data['title']


class SeekIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'seek'

    def get_data(self, handler_input):
        return {
            "duration": utils.get_slot_value(handler_input, 'duration', 'PT30S'),  # 30 seconds
            "direction": utils.get_slot_value(handler_input, 'direction', 'forward')
        }

    def get_response(self, data):
        return 'Playing trailer for %s' % data['title']


class PlayEpisodeIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-episode'

    def get_data(self, handler_input):
        params = ['epnum', 'seasnum', 'title', 'tvshow']
        return {
            param: utils.get_slot_value(handler_input, param, '') for param in params
        }

    def get_response(self, data):
        if data['epnum']:
            return f'Playing episode {data["epnum"]} of season {data["seasnum"]} of {data["tvshow"]}'
        return f'Playing the episode {data["title"]} of {data["tvshow"]}'


class PlayMediaIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-media'

    @staticmethod
    def _get_action_response():
        return 'Playing'

    def get_data(self, handler_input):
        params = ['app', 'room', 'title', 'song', 'album', 'artist', 'playlist', 'tvshow', 'movie']
        return {
            param:
                utils.get_slot_value(handler_input, param, '').lower().
                replace('the playlist', '').
                replace('the album', '').
                replace('t. v. show', '').
                replace('t. v. series', '')
            for param in params}

    @staticmethod
    def __build_param(data, param, prompt='', prefix='the'):
        if not prompt:
            prompt = param
        return f' {prefix} {prompt} {data[param]}' if data[param] else ''

    def get_response(self, data):
        return (
            self._get_action_response() +
            f' {data["title"]} ' +
            self.__build_param(data, 'playlist') +
            self.__build_param(data, 'album') +
            self.__build_param(data, 'song') +
            self.__build_param(data, 'tvshow', prompt='tv show') +
            self.__build_param(data, 'movie') +
            self.__build_param(data, 'artist',
                               prompt='by' if data['song'] or data['album'] else 'songs by',
                               prefix='') +
            self.__build_param(data, 'app', prompt='on', prefix='') +
            self.__build_param(data, 'room', prompt='in', prefix='')
        )


class FindMediaIntentHandler(PlayMediaIntentHandler):
    def get_action(self):
        return 'find-media'

    @staticmethod
    def _get_action_response():
        return 'Finding'


class SubtitleOnIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'subtitle-on'

    def get_response(self, data):
        return 'Turning subtitles on'


class SubtitleOffIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'subtitle-off'

    def get_response(self, data):
        return 'Turning subtitles off'


class ChangeAudioIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'change-audio'

    def get_response(self, data):
        return 'Changing audio stream'


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = HELP_TEXT
        return (
            handler_input.response_builder
                .speak(speak_output)
                .card(ui.SimpleCard(CARD_TITLE, speak_output))
                .response
        )


class CancelIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

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
    sb.add_request_handler(PreviousIntentHandler())
    sb.add_request_handler(NextIntentHandler())
    sb.add_request_handler(OpenIntentHandler())
    sb.add_request_handler(RewindIntentHandler())
    sb.add_request_handler(SeekIntentHandler())
    sb.add_request_handler(RestartIntentHandler())
    sb.add_request_handler(MuteIntentHandler())
    sb.add_request_handler(UnMuteIntentHandler())

    # Plex specific
    sb.add_request_handler(FindMediaIntentHandler())
    sb.add_request_handler(ChangeAudioIntentHandler())
    sb.add_request_handler(SubtitleOnIntentHandler())
    sb.add_request_handler(SubtitleOffIntentHandler())

    sb.add_request_handler(PlayTrailerIntentHandler())
    sb.add_request_handler(PlayMediaIntentHandler())
    sb.add_request_handler(PlayEpisodeIntentHandler())

    sb.add_request_handler(HelpIntentHandler())
    sb.add_request_handler(CancelIntentHandler())
    sb.add_request_handler(SessionEndedRequestHandler())

    sb.add_request_handler(
        IntentReflectorHandler())  # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
    sb.add_exception_handler(CatchAllExceptionHandler())

    lambda_handler = sb.lambda_handler()

except Exception as e:
    logger.exception('Unexpected error')
    raise e
