# Alexa Chromecast Skill 2.0
Allows Amazon Alexa to control Google Chromecast

Now with 100% less PHP!

#Current Features:
###Play Youtube Videos (Based on Sample Utterances)
By saying "Alexa, ask ChromeCast play Jontron Home Improvement", Alexa will send the video URL to your Chromecast Python Script.

###Pause Videos
By saying "Alexa, ask ChromeCast to Pause", Alexa will pause the Chromecast.

###Resume Videos
By saying "Alexa ask ChromeCast to resume", Alexa will resume playback.

###Changing the Volume
By saying "Alexa ask ChromeCast to change the volume to 50", Alexa will change the volume to the specified volume

#Requirements
  - youtube-dl
  - pymysql
  - Youtube API Key

#Installation
  - In the index.py, replace all the connection strings with your information.
  - Zip up all the files EXCEPT raspberry.py.
  - On AWS Lambda, Create A new Skill with Basic Execution and The Alexa Skills Kit Event Source with Python 2.7 as the interpreter.
  - **IMPORTANT: Make sure that index is the event and lambda_handler is the handler**
  - Upload the ZIP to AWS Lambda

  - In raspberry.py, replace:
    - the connection string with the same connection string from index.py.
    - YOUTUBE_API_KEY with your Youtube API Key
    - CHROMECAST_NAME with your default chromecast name.
  - Upload raspberry.py to your Raspberry Pi
