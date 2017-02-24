#!/usr/bin/env bash -e

source config/variables

./build-lambda-bundle.sh

aws lambda update-function-code --function-name "$LAMBDA_FUNCTION_NAME" --zip-file fileb://lambda-build.zip
