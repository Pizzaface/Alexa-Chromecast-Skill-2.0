# Alexa Chromecast Skill

Allows Amazon Alexa to control Google Chromecast

> Alexa, tell chromecast to pause

> Alexa, tell chromecast to play

> Alexa, tell chromecast to set the volume to 5

## Setup and installation

1. Create an [Amazon Web Services](http://aws.amazon.com/) account
2. Install awscli, and run `aws configure` with your credentials
3. Run aws-setup.sh to create a Role, Lambda Function, and SNS Topic.
4. Go to developer.amazon.com and create a Skill mapped to the Lambda function ARN.
5. Run src/local/main.py locally with the AWS_SNS_TOPIC_ARN and CHROMECAST_NAME environment variables.

## Implementation

Alexa skills run in the cloud, but this skill needs to be on your local network to control the Chromecast.
This skill implements a hybrid approach: the command is handled by Alexa on AWS, which sends a notification to your local server.

Alexa -> AWS Lambda -> AWS SNS (Simple Notification Service) -> Local server

The Lambda component is in `src/lambda`, and the local component is in `src/local`.
