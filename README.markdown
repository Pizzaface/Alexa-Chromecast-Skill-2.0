# Alexa Chromecast Skill

Allows Amazon Alexa to control Google Chromecast

This skill supports controlling a single Chromecast or multiple Chromecasts in different rooms.
Each Alexa device can be set to control a different room. This is done by matching the room name to your Chromecast device's name.
e.g. If your Chromecast is named: "Master Bedroom TV", then set the Alexa room to control to "Master Bedroom"

The following will then pause the chromecast in the Master Bedroom: 
> Alexa, ask chromecast to pause

You can control another room by saying something like:
> Alexa, ask the chromecast to pause in the Media Room

To change the room a partiocular Alexa device controls you can say:
> Alexa, ask the chromecast to set the room

Here are some example voice commands:

> Alexa, tell chromecast to play

> Alexa, tell chromecast to play MKBHD

> Alexa, tell chromecast to play The Big Lebowski trailer
>
> Alexa, tell chromecast to set the volume to 5

> Alexa, tell chromecast to stop

Or:
> Alexa, ask the chromecast in the Media Room to stop
> Alexa, ask the chromecast to play in the Media Room

## How it works

Alexa skills run in the cloud, but this skill needs to be on your local network to control the Chromecast.
This skill implements a hybrid approach: the command is handled by Alexa on AWS, which sends a notification to your local server.

The Lambda component is in `src/lambda`, and the local component is in `src/local`.

![Architecture Overview](docs/diagram.jpg "Architecture Overview")

Both the ChromeCast and the Raspberry Pi (or whatever the local notification handler will run on) **MUST** be on the same network in order for the ChromeCast to be discoverable.
The local AWS SNS Listener defaults to port 30000, this port needs to be able to recieve TCP connections, so you may need to configure your router/firewall devices to allow this.
You can overide this port if required.

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
4. Select "Custom" and "Provision your own", then clike "Create skill". On the template screen just use the "Hello World Skill" template
5. Click on "Interaction Model" in the left menu, then "JSON Editor"
6. Copy and paste the content from `config/interaction_model.json` into the editor, then click "Save Model"
7. Click on "Endpoint" in the left menu. Enter the Lambda function ARN by the aws-setup.sh. Click "Save Endpoints"
8. CLick on "Invocation" in the left menu. Click on "Build Model"
9. Click on the "Test" tab. Enter 
### Install the local application which control the Chromecasts
10. Install local dependencies with `sudo pip install -r ./src/local/requirements.txt`
11. Run `./start.sh` to start the listener, or `./docker-start.sh` to run in docker.
### Finally
12. Ask Alexa to tell Chromecast to play

### Shell example

  `./start.sh`

### Docker

The skill subscriber can be run with docker:

`./docker-start.sh`

### Environment variables

The skill subscriber (local) uses these environment variables:

- **AWS_SNS_TOPIC_ARN** - AWS SNS Topic ARN (can be found in the `.env` file after running `aws-setup.sh`)
- **PORT** - (Optional) Externally accessible port to expose the SNS handler on, defaults to 30000.

- **AWS_ACCESS_KEY_ID** - AWS User Access Key
- **AWS_SECRET_ACCESS_KEY** - AWS Secret Access Key
- **AWS_DEFAULT_REGION** - AWS Lambda and SNS Region (e.g. eu-west-1)

If you have run `aws configure`, you will not need to set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or AWS_DEFAULT_REGION.

## Scripts

### aws-setup.sh

Sets up an AWS environment for the Alexa Skil:

1. Creates an IAM role for Alexa (with permissions for SNS)
2. Creates an SNS topic to communicate over
3. Creates a Lambda function

### build-lambda-bundle.sh

Creates a lambda-bundle.zip, which can be uploaded to an AWS Lambda function.

### aws-update-lambda.sh

Runs build-lambda-bundle and automatically uploads the bundle to AWS Lambda.


## FAQ

### "No Chromecasts found"

When the local service starts it searches for ChromeCasts on the network. If there are no ChromeCasts found, it will exit.

To fix this, you must confirm that the ChromeCast is on and working, make sure you can access it from your phone, and make sure that everything is on the same network.

To debug, a tool to search and list found ChomeCasts is provided at `./search-chromecasts` (make sure to make it executable with `chmod +x ./search-chromecasts`).
