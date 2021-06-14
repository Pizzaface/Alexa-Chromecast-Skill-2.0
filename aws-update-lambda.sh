#!/bin/bash

set -e -o pipefail

cd $(dirname $0)

source config/aws_variable_names

./build-lambda-bundle.sh

aws lambda update-function-code --function-name "$LAMBDA_FUNCTION_NAME" --zip-file fileb://lambda-build.zip
