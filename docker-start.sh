#!/bin/bash

HELP=0
SERVICE=0
EXTERNAL_IP=
EXTERNAL_PORT=

while getopts "hdi:p:" opt; do
  case $opt in
    h) HELP=1
    ;;
    d) SERVICE=1
    ;;
    i) EXTERNAL_IP="$OPTARG"
    ;;
    p) EXTERNAL_PORT="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1
    ;;
  esac
done

if [ $HELP -eq 1 ]; then
  echo
  echo "Usage:"
  echo "docker_start.sh -- Run with defaults in interactive mode"
  echo "docker_start.sh [params]"
  echo "-h      -- Show help"
  echo "-d      -- Run as a service"
  echo "-i IP   -- Specify an external IP address to use"
  echo "-p port -- Specify an external port to use"
  echo
  exit 0
fi

if [ ! -f .env ] || [ ! -d ~/.aws ]; then
  echo "Expected AWS settings not found. Please run the aws-setup script."
  exit 1
fi
source .env

AWS_ACCESS_KEY_ID="$( /usr/bin/awk -F' = ' '$1 == "aws_access_key_id" {print $2}' ~/.aws/credentials )"
AWS_SECRET_ACCESS_KEY="$( /usr/bin/awk -F' = ' '$1 == "aws_secret_access_key" {print $2}' ~/.aws/credentials )"
AWS_DEFAULT_REGION="$( /usr/bin/awk -F' = ' '$1 == "region" {print $2}' ~/.aws/config )"

CONTAINER_NAME=alexa_chromecast
if [ "$( docker container inspect -f '{{.State.Status}}' $CONTAINER_NAME )" == "running" ]; then
  docker stop $CONTAINER_NAME
fi

docker rm $CONTAINER_NAME 2>/dev/null

docker build -t alexa-skill-chromecast .

if [ $SERVICE -eq 1 ]; then
  docker run -d --network="host" \
   --name alexa_chromecast \
   --restart always \
   -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"\
   -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"\
   -e "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"\
   -e "AWS_SNS_TOPIC_ARN=$AWS_SNS_TOPIC_ARN"\
   -e "EXTERNAL_IP=$EXTERNAL_IP"\
   -e "EXTERNAL_PORT=$EXTERNAL_PORT"\
   -e "MOVIEDB_API_KEY=$MOVIEDB_API_KEY"\
   -e "PLEX_HOST=$PLEX_HOST"\
   -e "PLEX_PORT=$PLEX_PORT"\
   -e "PLEX_TOKEN=$PLEX_TOKEN"\
   alexa-skill-chromecast
else
  docker run --network="host" -it\
   --name alexa_chromecast \
   -e "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"\
   -e "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"\
   -e "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION"\
   -e "AWS_SNS_TOPIC_ARN=$AWS_SNS_TOPIC_ARN"\
   -e "EXTERNAL_IP=$EXTERNAL_IP"\
   -e "EXTERNAL_PORT=$EXTERNAL_PORT"\
   -e "MOVIEDB_API_KEY=$MOVIEDB_API_KEY"\
   -e "PLEX_HOST=$PLEX_HOST"\
   -e "PLEX_PORT=$PLEX_PORT"\
   -e "PLEX_TOKEN=$PLEX_TOKEN"\
   alexa-skill-chromecast
fi

