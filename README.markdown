# Alexa Chromecast Skill

Allows Amazon Alexa to control your Google Chromecast

This skill supports controlling a single Chromecast or multiple Chromecasts in different rooms.
Each Alexa device can be set to control a different room. This is done by matching the room name to your Chromecast device's name.
E.g. If your Chromecast is named: "Master Bedroom TV", then set the Alexa room to control to "Master Bedroom"

The following will then pause the Chromecast in the Master Bedroom: 
> Alexa, ask Chromecast to pause

You can control another room by saying something like:
> Alexa, ask the Chromecast to pause in the Media Room

To change the room a particular Alexa device controls you can say:
> Alexa, ask the Chromecast to set the room


###Standard commands
The following media commands are available:
```
 VOICE COMMAND         ACTION
 --------------------------------------------------------------------------------
 pause                 -> Pause a playing item
 play                  -> Play a paused item
 stop                  -> Stop the currently playing item
 set volume to 5       -> Change the volume between 0 and 10
 mute                  -> mute the volume
 unmute                -> unmute the volume
 rewind                -> Rewind back 15 seconds
 rewind 30 seconds     -> Rewind back 30 seconds
 fast forward          -> Fast forward 15 seconds 
 fast forward 1 minute -> Fast forward 1 minute
 restart               -> Restarts the media item from the beginning
 next                  -> Play or show the next item
 previous              -> Play or show the previous item
 open {app}            -> Opena specific app. Plex and YouTube are supported.
 ```

###YouTube app commands
Play items on YouTube.
```
 VOICE COMMAND        ACTION
 --------------------------------------------------------------------------------
 play {title}         -> Searches and queues 5 items matching the title
 play {title} trailer -> Searches and plays any matching trailer for the title
```

###Plex app commands
Find and play items on your Plex server.
* The Find command will display the item that was found.
* The Play command will immediately play the item that was found.
```
 VOICE COMMAND                    ACTION
 ---------------------------------------------------------------------------------
 play                             -> Resumes from pause, or plays the displayed item
 stop                             -> Stops playing and displays the item details
 play/find {title}                -> Play/Find the title
 play/find the tv show {title}    -> Play/Find a tv show matching the title
 play/find the movie {title}      -> Play/Find a movie matching the title
 play/find the song {title}       -> Play/Find a song matching the title
 play/find the album {title}      -> Play/Find an album matching the title
 play/find the playlist {title}   -> Play/Find a playlist matching the title
 play/find songs by {artist}      -> Play/Find songs by the specified artist
 turn on subtitles                -> Turns on subtitles in the configurged language
 turn off subtitles               -> Turns off subtitles
 switch audio                     -> Switches to another audio track if available
                                     (e.g. to the directors commentry)
 play/find the episode {title} of -> Play/Find the specified show episode
                           {show}                     
 play/find season {#} episode {#} -> Play/Find the specified show episode
                        of {show}
```

##Example Commands
> Alexa, ask Chromecast to pause
>
> Alexa, ask Chromecast to resume
>
> Alexa, ask Chromecast to rewind 2 minutes
>
> Alexa, ask Chromecast to play Mythic Quest on Plex
> 
> Alexa, ask Chromecast to play The Matrix trailer

## How it works

Alexa skills run in the cloud, but this skill needs to be on your local network to control the Chromecast.
This skill implements a hybrid approach: the command is handled by Alexa on AWS, which sends a notification to your local server.

The Lambda component is in `src/lambda`, and the local component is in `src/local`.

![Architecture Overview](docs/diagram.jpg "Architecture Overview")

Both the Chromecast and the Raspberry Pi (or whatever the local notification handler will run on) **MUST** be on the same network in order for the Chromecast to be discoverable.

## Dependencies

Installation requires a UNIX environment with:

- BASH
- Python 3.7
- [Pip](https://pip.pypa.io/en/stable/installing/)

## Setup and installation

### Build the AWS Lambda Function
1. Create an [Amazon Web Services](http://aws.amazon.com/) account
2. Run aws-setup.sh to create a Role, Lambda Function, and SNS Topic. (*It will run `aws configure`, so have an key id and access key ready*)
### Setup the Alexa Skill
3. Go to developer.amazon.com and choose "Create Skill"
4. Select "Custom" and "Provision your own", then click "Create skill". On the template screen just use the "Hello World Skill" template
5. Click on "Interaction Model" in the left menu, then "JSON Editor"
6. Copy and paste the content from `config/interaction_model.json` into the editor, then click "Save Model"
7. Click on "Endpoint" in the left menu. Enter the Lambda function ARN by the aws-setup.sh. Click "Save Endpoints"
8. Click on "Invocation" in the left menu. Click on "Build Model"
9. Click on the "Test" tab. Enter 
### Install the local application which control the Chromecasts
10. Install local dependencies with `sudo pip3 install -r ./src/local/requirements.txt`
11. Run `./start.sh` to start the listener, or `./docker-start.sh` to run in an interactive docker session. Or `./docker-start.sh -d` to run as a service.
The service attempts to AWS SNS using UPNP. If UPNP is disabled in your network you can specify a port. `./start.sh -p 30000`
To see other options run `./start.sh -h` or `./docker-start.sh -h`.

When run you should see something like the following:
```
2020-07-12 11:10:40,688 - root - INFO - Starting Alexa Chromecast listener...
2020-07-12 11:10:40,688 - local.ChromecastSkill - INFO - Finding Chromecasts...
2020-07-12 11:10:45,696 - pychromecast - INFO - Querying device status
2020-07-12 11:10:45,727 - pychromecast - INFO - Querying device status
2020-07-12 11:10:45,767 - local.ChromecastSkill - INFO - Found Media Room TV
2020-07-12 11:10:45,768 - local.ChromecastSkill - INFO - Found Living Room TV
2020-07-12 11:10:45,769 - local.ChromecastSkill - INFO - 2 Chromecasts found
2020-07-12 11:10:45,809 - botocore.credentials - INFO - Found credentials in environment variables.
2020-07-12 11:10:46,967 - local.SkillSubscriber - INFO - Listening on http://123.123.123.123:30000
2020-07-12 11:10:46,968 - local.SkillSubscriber - INFO - Subscribing for Alexa commands...
2020-07-12 11:10:47,344 - local.SkillSubscriber - INFO - Received subscription confirmation...
2020-07-12 11:10:47,431 - local.SkillSubscriber - INFO - Subscribed.
```
### Finally
12. Say "Alexa ask Chromecast to play"
The skill will take you through any required room setup.

### Shell example

  `./start.sh`

### Docker

The skill subscriber can be run with docker:

`./docker-start.sh` - for an interactive session
`./docker-start.sh -d` - to run as a service

### Environment variables

The skill subscriber (local) uses these environment variables:

- **AWS_SNS_TOPIC_ARN** - AWS SNS Topic ARN (can be found in the `.env` file after running `aws-setup.sh`)
- **AWS_ACCESS_KEY_ID** - AWS User Access Key
- **AWS_SECRET_ACCESS_KEY** - AWS Secret Access Key
- **AWS_DEFAULT_REGION** - AWS Lambda and SNS Region (e.g. eu-west-1)

If you have run `aws configure`, you will not need to set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or AWS_DEFAULT_REGION.

## Scripts

### aws-setup.sh

Sets up an AWS environment for the Alexa Skill:

1. Creates an IAM role for Alexa (with permissions for SNS)
2. Creates an SNS topic to communicate over
3. Creates an S3 persistent store for persisting the room to Alexa device mapping 
4. Creates a Lambda function

### build-lambda-bundle.sh

Creates a lambda-bundle.zip, which can be uploaded to an AWS Lambda function.

### aws-update-lambda.sh

Runs build-lambda-bundle and automatically uploads the bundle to AWS Lambda.


## FAQ

### No Chromecasts found
When the local service starts it searches for Chromecasts on the network. If there are no ChromeCasts found, it will exit.
To fix this, you must confirm that the Chromecast is on and working, make sure you can access it from your phone, and make sure that everything is on the same network.
To debug, a tool to search and list found ChomeCasts is provided at `./search-chromecasts` (make sure to make it executable with `chmod +x ./search-chromecasts`).

### Local listener fails to subscribe
If the local listener fails to subscribe (no subscribe messages or an error) then the Chromecasts won't receive commands from Alexa
By default the local listener uses UPNP and a dynamic port to establish an external connection, you can override this if required.
1. Check UPNP is enabled/allowed on your network
2. If UPNP is not enabled or working try and manually specify a port, and ensure your firewall/router is configured to allow external access to this port
e.g. to use port 30000 run `./start.sh -p 30000` or `./docker-start.sh -p 30000`
3. Log into the AWS console and check the SNS topic is setup, and check the Cloud Watch logs for your the lambda function for any errors.

### Alexa had an error launching the skill or processing a command
1. Try redeploying the lambda skill. `./aws-update-lambda.sh`
2. If that didn't work go to the AWS Console and check the CloudWatch logs associated with the lambda function

### Alexa accepted the command but it didn't seem to work
1. Check the local listener output, it should show the received command and any error that was encountered
2. To check the docker service logs run something like `docker logs alexa_chromecast --since=30m`, which shows the logs for the last 30 minutes
3. If the command wasn't received then try restarting the service. Consider scheduling a daily restart if it's a common issue.
e.g.
`docker restart alexa_chromecast`
