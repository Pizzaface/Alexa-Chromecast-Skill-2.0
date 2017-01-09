# Alexa Chromecast Skill

Allows Amazon Alexa to control Google Chromecast

> Alexa, tell chromecast to pause

> Alexa, tell chromecast to play

> Alexa, tell chromecast to set the volume to 5

## Dependencies

Installation requires a UNIX environment with:

- BASH
- Python 27
- PIP

## Setup and installation

1. Create an [Amazon Web Services](http://aws.amazon.com/) account
2. Run aws-setup.sh to create a Role, Lambda Function, and SNS Topic. (*It will run `aws configure`, so have an key id and access key ready*)
3. Go to developer.amazon.com and create a Skill mapped to the Lambda function ARN, intentSchemas and sample utterances are in `config/`.
4. Run src/local/main.py with the AWS_SNS_TOPIC_ARN and CHROMECAST_NAME environment variables.
5. Ask Alexa to tell Chromecast to do something.

### Docker

The skill subscriber can be run with docker:

`docker run --network="host" -it -e 'AWS_ACCESS_KEY_ID=...' -e 'AWS_SECRET_ACCESS_KEY=...' -e 'AWS_DEFAULT_REGION=...' -e 'AWS_SNS_TOPIC_ARN=...' lukechannings/alexa-skill-chromecast`

### Environment variables

The skill subscriber (local) uses these environment variables:

- AWS_SNS_TOPIC_ARN - AWS SNS Topic ARN (can be found in the `.env` file after running `aws-setup.sh`)
- CHROMECAST_NAME - Friendly name of the Chromecast to send commands to. (Defaults to 'Living Room')
- PORT - (Optional) Externally accessible port to expose the SNS handler on.

- AWS_ACCESS_KEY_ID - AWS User Access Key
- AWS_SECRET_ACCESS_KEY - AWS Secret Access Key
- AWS_DEFAULT_REGION - AWS Lambda and SNS Region (e.g. eu-west-1)

If you have run `aws configure`, you will not need to set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or AWS_DEFAULT_REGION.

## Implementation

Alexa skills run in the cloud, but this skill needs to be on your local network to control the Chromecast.
This skill implements a hybrid approach: the command is handled by Alexa on AWS, which sends a notification to your local server.

Alexa -> AWS Lambda -> AWS SNS (Simple Notification Service) -> Local server

The Lambda component is in `src/lambda`, and the local component is in `src/local`.
