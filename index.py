"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import pymysql
import urllib
import urllib2
from bs4 import BeautifulSoup
import json

def lambda_handler(event, context):

    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

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
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "sendVideoIntent":
        return sendVideo(intent, session)
    elif intent_name == "setVolumeIntent":
        return setVolume(intent, session)
    elif intent_name == "AMAZON.PauseIntent":
        return pauseVideo(intent, session)
    elif intent_name == "AMAZON.ResumeIntent":
        return resumeVideo(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
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

def sendVideo(intent, session):
    if 'query' in intent['slots']:
        lookupString = intent['slots']['query']['value']
    else:
        speech_output = "I'm sorry, I didn't understand, you can say something like 'I want to watch the Game Grumps on Youtube'"
        card_title = None
        should_end_session = True
        reprompt_text = ""
        return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

    #Gets the First Result of a Youtube Search for the string provided
    query = urllib.quote(lookupString)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib2.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, "html.parser")
    for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
        vidId = vid['href']
        if "/watch?v=" not in vidId:
            next
        else:
            vidId = vidId.replace("/watch?v=", "")
            break

    youtubeAPIURL = "https://www.googleapis.com/youtube/v3/videos?id="+vidId+"&key=YOUTUBE_API_KEY&fields=items(id,snippet(title),statistics)&part=snippet,statistics"
    response = urllib.urlopen(youtubeAPIURL)
    data = json.loads(response.read())
    title = data['items'][0]['snippet']['title'];
    if title == "":
        title = "Video"
    
    speech_output = title + " was added successfully"
    card_title = "ChromeCast - Video Added"
    should_end_session = True
    reprompt_text = ""
    #sends the command to the Database
    conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME")
    cur = conn.cursor()
    cur.execute("INSERT INTO  `commands` (`command` ,`slot`) VALUES ('play',  '"+vidId +"')")
    conn.close()

    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def setVolume(intent, session):
    if 'volume' in intent['slots']:
        volume = intent['slots']['volume']['value']

    speech_output =  "Chromecast Volume set to " + volume
    card_title = "ChromeCast - Volume Set to " + volume
    should_end_session = True
    reprompt_text = ""
    #sends the command to the Database
    conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME")
    cur = conn.cursor()
    cur.execute("INSERT INTO  `commands` (`command` ,`slot`) VALUES ('volume',  '"+volume +"')")
    conn.close()

    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def pauseVideo(intent, session):
    speech_output =  "I've sent the pause command to your Chromecast"
    card_title = "ChromeCast - Video Paused"
    should_end_session = True
    reprompt_text = ""
    #sends the command to the Database
    conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME")
    cur = conn.cursor()
    cur.execute("INSERT INTO  `commands` (`command` ,`slot`) VALUES ('pause',  'none')")
    conn.close()

    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def resumeVideo(intent, session):
    speech_output =  "I've sent the play command to your Chromecast"
    card_title = "ChromeCast - Video Resume"
    should_end_session = True
    reprompt_text = ""
    #sends the command to the Database
    conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME")
    cur = conn.cursor()
    cur.execute("INSERT INTO  `commands` (`command` ,`slot`) VALUES ('resume',  'none')")
    conn.close()

    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
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