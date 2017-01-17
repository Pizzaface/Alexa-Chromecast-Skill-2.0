#!/usr/bin/env bash

./build-lambda-bundle.sh

aws lambda update-function-code --function-name AlexaChromecastSkill --zip-file fileb://lambda-build.zip
