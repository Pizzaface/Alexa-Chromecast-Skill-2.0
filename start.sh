#!/bin/bash

HELP=0
EXTERNAL_IP=
EXTERNAL_PORT=

while getopts "hi:p:" opt; do
  case $opt in
    h) HELP=1
    ;;
    i) export EXTERNAL_IP="$OPTARG"
    ;;
    p) export EXTERNAL_PORT="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2; exit 1
    ;;
  esac
done

if [ $HELP -eq 1 ]; then
  echo
  echo "Usage:"
  echo "start.sh -- Run with defaults in interactive mode"
  echo "start.sh [params]"
  echo "-h      -- Show help"
  echo "-i IP   -- Specify an external IP address to use"
  echo "-p port -- Specify an external port to use"
  echo
  exit 0
fi

set -e -o pipefail
cd $(dirname $0)

if [ ! -f .env ] || [ ! -d ~/.aws ]; then
  echo "Expected AWS settings not found. Please run the aws-setup script."
  exit 1
fi

if [ ! -f .custom_env ]; then
  cp ./config/custom_variables .custom_env
fi

. .env
. .custom_env

cd src
python3 -m local.main
