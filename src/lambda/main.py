#!/usr/bin/env python2.7

import urllib
import urllib2
from bs4 import BeautifulSoup
import json
import boto3
import os

AWS_SNS_ARN = os.getenv('AWS_SNS_ARN')
# AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

def lambda_handler(event, context):

    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Get's the help section
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Sends the request to one of our intents
    if intent_name == "sendVideoIntent":
        return send_video(intent, session)
    elif intent_name == "setVolumeIntent":
        return set_volume(intent, session)
    elif intent_name == "AMAZON.PauseIntent":
        return pause_video(intent, session)
    elif intent_name == "AMAZON.ResumeIntent":
        return resume_video(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    # When the User decides to end the session, this is the function that is
    # called.
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------


def get_welcome_response():
    """ Helps the User Find out what they can say, and how to use
            the program, Sends a Card with that data as well"""
    session_attributes = {}
    card_title = "Chromecast"
    speech_output = "I can control your Chromecast, " \
        "Tell me a video name, or to pause, resume, or turn the volume to numbers 1 through 100"
    reprompt_text = "Please tell me a video name to look up, or say a command."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    should_end_session = True
    return build_response({}, build_speechlet_response(
        None, None, None, should_end_session))


def send_video(intent, session):
    """ Check if the User Specified a Video, if not, return an 'I didn't understand' message"""
    if 'query' in intent['slots']:
        lookupString = intent['slots']['query']['value']
    else:
        speech_output = "I'm sorry, I didn't understand, you can say something like 'I want to watch the Game Grumps on Youtube'"
        card_title = None
        should_end_session = True
        reprompt_text = ""
        return build_response({}, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    """Looks up the first video in a Youtube Search"""
    query = urllib.quote(lookupString)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, "html.parser")
    for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
        vidId = vid['href']
        if "/watch?v=" not in vidId:
            next
        else:
            vidId = vidId.replace("/watch?v=", "")
            break
    """ OPTIONAL: Uses the Youtube API to get the Video Name """
    youtubeAPIURL = "https://www.googleapis.com/youtube/v3/videos?id=" + vidId + \
        "&key=YOUTUBE_API_KEY&fields=items(id,snippet(title),statistics)&part=snippet,statistics"
    response = urllib.urlopen(youtubeAPIURL)
    data = json.loads(response.read())
    title = data['items'][0]['snippet']['title']
    if title == "":
        title = "Video"

    try:
        publish_command_to_sns('play', {'videoId': vidId})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title="ChromeCast - Video Added",
            output=(title + " was added successfully")
        )
        return build_response({}, speech)

def set_volume(intent, session):
    """ Gets the volume from the Query """
    if 'volume' in intent['slots']:
        volume = intent['slots']['volume']['value']

    try:
        publish_command_to_sns('volume', {'level': volume})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        message = "ChromeCast - Volume Set to " + volume
        speech = build_speechlet_response(title=message, output=message)
        return build_response({}, speech)

def pause_video(intent, session):
    try:
        publish_command_to_sns('pause', {})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title="ChromeCast - Video Paused",
            output="I've sent the pause command to your Chromecast"
        )
        return build_response({}, speech)

def resume_video(intent, session):
    try:
        publish_command_to_sns('resume', {})
    except SNSPublishError as error:
        speech = build_speechlet_response(
            title="ChromeCast - Command Failed",
            output=str(error)
        )
        return build_response({}, speech)
    else:
        speech = build_speechlet_response(
            title="ChromeCast - Video Resumed",
            output="I've sent the play command to your Chromecast"
        )
        return build_response({}, speech)

# --------------- Helpers that build all of the responses ----------------


def build_speechlet_response(title, output, reprompt_text="", should_end_session = True):
    if output == None:
        return {
            'shouldEndSession': should_end_session
        }
    elif title == None:
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }
    else:
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'card': {
                'type': 'Simple',
                'title':  title,
                        'content': output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def publish_command_to_sns(command, data):
    message = {
        'command': command,
        'data': data
    }

    client = boto3.client('sns')

    response = client.publish(
        TargetArn=AWS_SNS_ARN,
        Message=json.dumps({'default': json.dumps(message)}),
        MessageStructure='json'
    )

    print(response['ResponseMetadata'])

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        message = 'SNS Publish returned {} response instead of 200.'.format(response['ResponseMetadata']['HTTPStatusCode'])
        raise SNSPublishError(message)

class SNSPublishError(Exception):
    """ If something goes wrong with publishing to SNS """
    pass
