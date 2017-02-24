#!/usr/bin/env python2.7

import json
import boto3
import os
from moviedb import get_movie_trailer_youtube_id
import youtube

AWS_SNS_ARN = os.getenv("AWS_SNS_ARN")

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """

    type = event["request"]["type"]

    return {
        "LaunchRequest": on_launch,
        "IntentRequest": on_intent
    }[type](event["request"], event["session"])

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    # Get"s the help section
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    return {
        "PlayYoutubeVideo": send_video,
        "PlayTrailer": send_trailer,
        "PowerOff": power_off,
        "SetVolume": set_volume,
        "AMAZON.PauseIntent": pause_video,
        "AMAZON.ResumeIntent": resume_video,
        "AMAZON.StopIntent": stop,
        "AMAZON.HelpIntent": lambda intent, session: get_welcome_response(),
        "fallback": lambda intent, session: build_response({}, build_speechlet_response(None, "No handler for {}".format(intent_name)))
    }.get(intent_name, "fallback")(intent, session)


# --------------- Functions that control the skill"s behavior ------------


def get_welcome_response():
    """ Helps the User Find out what they can say, and how to use
            the program, Sends a Card with that data as well"""
    session_attributes = {}
    card_title = "Chromecast"
    speech_output = "I can control your Chromecast, " \
        "Tell me a video name, or to pause, resume, or turn the volume to numbers 1 through 10"
    reprompt_text = "Please tell me a video name to look up, or say a command."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    print("handle_session_end_request")
    should_end_session = True
    return build_response({}, build_speechlet_response(
        None, None, None, should_end_session))


def send_video(intent, session):

    youtube_result = youtube.search(intent["slots"]["video"]["value"])
    
    try:
        publish_command_to_sns("play_video", {"videoId": youtube_result["id"]})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title="ChromeCast - Video Added",
            output="Adding {} from YouTube".format(youtube_result["title"])
        )
        return build_response({}, speech)

def send_trailer(intent, session):
    movie = intent["slots"]["movie"]["value"]

    try:
        moviedb_result = get_movie_trailer_youtube_id(movie)
        publish_command_to_sns("play_video", {"videoId": moviedb_result["youtube_id"]})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title="ChromeCast - Video Added",
            output=(moviedb_result["title"] + " was added successfully")
        )
        return build_response({}, speech)

def power_off(intent, session):
    try:
        publish_command_to_sns("power_off", {})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="Communication error",
            output="Communication error"
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title="Ok",
            output="Ok"
        )
        return build_response({}, speech)

def set_volume(intent, session):
    """ Gets the volume from the Query """
    if "volume" in intent["slots"]:
        volume = int(intent["slots"]["volume"]["value"])

    if volume > 10 or volume < 0:
        message = "Sorry, you can only set the volume between 0 and 10."
        return build_response({}, build_speechlet_response(title=message, output=message))

    try:
        publish_command_to_sns("set_volume", {"level": volume})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        message = "Ok"
        speech = build_speechlet_response(title=message, output=message)
        return build_response({}, speech)


def pause_video(intent, session):
    try:
        publish_command_to_sns("pause", {})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title="ChromeCast - Video Paused",
            output="Ok"
        )
        return build_response({}, speech)


def resume_video(intent, session):
    try:
        publish_command_to_sns("resume", {})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title=None,
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title=None,
            output="Ok"
        )
        return build_response({}, speech)


def stop(intent, session):
    try:
        publish_command_to_sns("stop", {})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title=None,
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title=None,
            output="Ok"
        )
        return build_response({}, speech)

# --------------- Helpers that build all of the responses ----------------


def build_speechlet_response(title, output, reprompt_text="", should_end_session=True):
    if output == None:
        return {
            "shouldEndSession": should_end_session
        }
    elif title == None:
        return {
            "outputSpeech": {
                "type": "PlainText",
                "text": output
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": reprompt_text
                }
            },
            "shouldEndSession": should_end_session
        }
    else:
        return {
            "outputSpeech": {
                "type": "PlainText",
                "text": output
            },
            "card": {
                "type": "Simple",
                "title":  title,
                        "content": output
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": reprompt_text
                }
            },
            "shouldEndSession": should_end_session
        }


def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }


def publish_command_to_sns(command, data):
    message = {
        "handler_name": "chromecast",
        "command": command,
        "data": data
    }

    client = boto3.client("sns")

    response = client.publish(
        TargetArn=AWS_SNS_ARN,
        Message=json.dumps({"default": json.dumps(message)}),
        MessageStructure="json"
    )

    print(response["ResponseMetadata"])

    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        message = "SNS Publish returned {} response instead of 200.".format(
            response["ResponseMetadata"]["HTTPStatusCode"])
        raise SNSPublishError(message)


class SNSPublishError(Exception):
    """ If something goes wrong with publishing to SNS """
    pass
