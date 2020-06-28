#!/bin/bash

source .env

AWS_ACCESS_KEY_ID="$( /usr/bin/awk -F' = ' '$1 == "aws_access_key_id" {print $2}' ~/.aws/credentials )"
AWS_SECRET_ACCESS_KEY="$( /usr/bin/awk -F' = ' '$1 == "aws_secret_access_key" {print $2}' ~/.aws/credentials )"
AWS_DEFAULT_REGION="$( /usr/bin/awk -F' = ' '$1 == "region" {print $2}' ~/.aws/config )"

docker build -t alexa-skill-chromecast .
docker container rm alexa_chromecast

if [ "$1" == "service" ]; then
  docker run -d --network="host" \
   --name alexa_chromecast \
   --restart always \
   -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"\
   -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"\
   -e "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"\
   -e "AWS_SNS_TOPIC_ARN=$AWS_SNS_TOPIC_ARN"\
   alexa-skill-chromecast
else
  docker run --network="host" -it\
   --name alexa_chromecast \
   -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"\
   -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"\
   -e "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"\
   -e "AWS_SNS_TOPIC_ARN=$AWS_SNS_TOPIC_ARN"\
   alexa-skill-chromecast
fi
