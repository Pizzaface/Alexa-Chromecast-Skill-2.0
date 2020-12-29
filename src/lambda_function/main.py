import os
import logging
import requests
import boto3
import json
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
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
CARD_TITLE = 'Controlar Chromcast con Alexa'

HELP_TEXT = ''.join([
    "Bienvenido al controlador de Chromcast de Alexa. Esta habilidad le permite controlar sus Chromcast en diferentes habitaciones. ",
    "Un Dispositivo Alexa puede ser configurado para controlar un Chromcast en una habitación particular. ",
    "Entonces puedes decir algo como: Alexa, pídele a Chromcast que reproduzca, o: Alexa, pídele a Chromcast que pause. ",
    "O puedes controlar una habitación específica, diciendo algo como: Alexa, cambia a sala de estar"
])

class SNSPublishError(Exception):
    """ If something goes wrong with publishing to SNS """
    pass

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input) or ask_utils.is_intent_name('AMAZON.NavigateHomeIntent')(handler_input)

    def handle(self, handler_input):
        speak_output = 'Bienvenido, ¿qué quieres hacer?'
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .set_card(ui.SimpleCard(CARD_TITLE, speak_output))
                .response
        )

class BaseIntentHandler(AbstractRequestHandler):
    '''
    Base handler for all intents
    '''
    def get_action(self):
        raise NotImplementedError

    def get_intent_name(self):
        return self.__class__.__name__.replace('Handler','')

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
        return 'Vale'

    def handle(self, handler_input):
        room = utils.get_slot_value(handler_input, 'room', False)
        device_id = handler_input.request_envelope.context.system.device.device_id

        if not room:
            room = utils.get_persistent_session_attribute(handler_input, 'DEVICE_'+device_id, False)
            if not room:
                speak_output = 'Tengo que establecer la sala del Chromcast que este dispositivo de Alexa controlará. Por favor, di algo como: ver en la sala de estar.'
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask('Por favor, establezca la sala del Chromcast, diciendo algo como: establecer habitación a sala de estar.')
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
            speak_output = 'Hubo un error al enviar la orden al Chromcast'
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

    def handle(self, handler_input):
        device_id = handler_input.request_envelope.context.system.device.device_id
        room = utils.get_slot_value(handler_input, 'room') #Must have a value enforced by Alexa dialog
        utils.set_persistent_session_attribute(handler_input, 'DEVICE_'+device_id, room)
        handler_input.attributes_manager.save_persistent_attributes()
        speak_output = 'De acuerdo, este dispositivo de Alexa controlará el Chromcast en %s. Para controlar otra habitación puedes decir algo como: Alexa, ver en sala de estar.' % room
        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_card(ui.SimpleCard(CARD_TITLE, speak_output))
                .response
        )

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
            return "Lo siento, sólo se puede ajustar el volumen entre 0 y 10."
        return {"volume": volume}

class NextIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.NextIntent']

    def get_action(self):
        return 'play-next'

class PreviousIntentHandler(BaseIntentHandler):
    def match_other_intent_names(self):
        return ['AMAZON.PreviousIntent']

    def get_action(self):
        return 'play-previous'

class RestartIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'restart'

class PlayTrailerIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-trailer'

    def get_data(self, handler_input):
        return {
            "title": utils.get_slot_value(handler_input, 'movie'),
            "app": 'youtube'
            }

    def get_response(self, data):
        return 'Reproduciendo el tráiler de %s' % data['title']

class PlayOnAppIntentHandler(BaseIntentHandler):
    def get_action(self):
        return 'play-video'

    def get_data(self, handler_input):
        #TODO: Support other apps in the future
        return {
            "title": utils.get_slot_value(handler_input, 'video'),
            "app": 'youtube'
            }

    def get_response(self, data):
        return 'Reproduciendo %s en YouTube' % data['title']

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = HELP_TEXT
        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_card(ui.SimpleCard(CARD_TITLE, speak_output))
                .response
        )

class CancelIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "¡Hasta luego!"

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
        speak_output = "Acabas de activar " + intent_name + "."

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

        speak_output = "Lo siento, tuve problemas para hacer lo que me pediste. Por favor, inténtalo de nuevo."

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

    sb.add_request_handler(SetRoomIntentHandler())
    sb.add_request_handler(PauseIntentHandler())
    sb.add_request_handler(PlayIntentHandler())
    sb.add_request_handler(StopIntentHandler())
    sb.add_request_handler(SetVolumeIntentHandler())
    sb.add_request_handler(PreviousIntentHandler())
    sb.add_request_handler(NextIntentHandler())

    sb.add_request_handler(RestartIntentHandler())
    sb.add_request_handler(PlayTrailerIntentHandler())
    sb.add_request_handler(PlayOnAppIntentHandler())

    sb.add_request_handler(HelpIntentHandler())
    sb.add_request_handler(CancelIntentHandler())
    sb.add_request_handler(SessionEndedRequestHandler())

    sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
    sb.add_exception_handler(CatchAllExceptionHandler())

    lambda_handler = sb.lambda_handler()

except Exception as e:
    logger.exception('Unexpected error')
    raise e
