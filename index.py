
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
	#When the User decides to end the session, this is the function that is called.
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


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

def sendVideo(intent, session):
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
    for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
        vidId = vid['href']
        if "/watch?v=" not in vidId:
            next
        else:
            vidId = vidId.replace("/watch?v=", "")
            break
    """ OPTIONAL: Uses the Youtube API to get the Video Name """
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

    """ Attempts to send the command to the database, if it can't, returns
    	a 'Please Ensure your Database is Running' Message """
    try:
    	conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME", connect_timeout=10)
    except pymysql.err.OperationalError:
    	speech_output = "The Command Could not be Sent,  Please ensure your database is Running."
	    card_title = "ChromeCast - Command Failed"
	    should_end_session = True
	    reprompt_text = ""
	    return build_response({}, build_speechlet_response(
	        card_title, speech_output, reprompt_text, should_end_session))
	else:
	    cur = conn.cursor()
	    cur.execute("INSERT INTO  `commands` (`command` ,`slot`) VALUES ('play',  '"+vidId +"')")
	    conn.close()

	    return build_response({}, build_speechlet_response(
	        card_title, speech_output, reprompt_text, should_end_session))

def setVolume(intent, session):
	""" Gets the volume from the Query """
    if 'volume' in intent['slots']:
        volume = intent['slots']['volume']['value']

    speech_output =  "Chromecast Volume set to " + volume
    card_title = "ChromeCast - Volume Set to " + volume
    should_end_session = True
    reprompt_text = ""
    #sends the command to the Database
    try:
    	conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME", connect_timeout=10)
    except 
    	speech_output = title + " was added successfully"
	    card_title = "ChromeCast - Command Failed"
	    should_end_session = True
	    reprompt_text = ""
	    return build_response({}, build_speechlet_response(
	        card_title, speech_output, reprompt_text, should_end_session))
	else:
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
    try:
    	conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME", connect_timeout=10)
    except pymysql.err.OperationalError:
    	speech_output = "The Command Could not be Sent,  Please ensure your database is Running."
	    card_title = "ChromeCast - Command Failed"
	    should_end_session = True
	    reprompt_text = ""
	    return build_response({}, build_speechlet_response(
	        card_title, speech_output, reprompt_text, should_end_session))
	else:
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
    try:
    	conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME", connect_timeout=10)
    except pymysql.err.OperationalError:
    	speech_output = "The Command Could not be Sent,  Please ensure your database is Running."
	    card_title = "ChromeCast - Command Failed"
	    should_end_session = True
	    reprompt_text = ""
	    return build_response({}, build_speechlet_response(
	        card_title, speech_output, reprompt_text, should_end_session))
	else:
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