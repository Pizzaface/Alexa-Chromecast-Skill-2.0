#!/bin/bash

set -e -o pipefail

if [ -d "lambda-build" ]; then
  rm -rf lambda-build
fi

if [ -f "lambda-build.zip" ]; then
  rm lambda-build.zip
fi

cd $(dirname $0)

source ./config/aws_variable_names

if [ -f .env ]; then
  source .env
fi

echo "Detaching role policy AmazonSNSFullAccess from role $ROLE_NAME"
aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess || true
echo "Detaching role policy AmazonLambdaBasicExecutionRole from role $ROLE_NAME"
aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true
echo "Detaching role policy AmazonS3FullAccess from role $ROLE_NAME"
aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess || true

echo "Deleting role $ROLE_NAME"
aws iam delete-role --role-name "$ROLE_NAME" || true

if [ ! -z "$AWS_SNS_TOPIC_ARN" ]; then
  echo "Deleting topic $AWS_SNS_TOPIC_ARN"
  aws sns delete-topic --topic-arn "$AWS_SNS_TOPIC_ARN" || true
fi

if [ ! -z "$S3_BUCKET_NAME" ]; then
  echo "Deleting S3 bucket $S3_BUCKET_NAME"
  aws s3 rb s3://$S3_BUCKET_NAME --force
fi

if [ ! -z "$LAMBDA_FUNCTION_NAME" ]; then
  echo "Deleting lambda function $LAMBDA_FUNCTION_NAME"
  aws lambda delete-function --function-name "$LAMBDA_FUNCTION_NAME" || true
fi

rm -f .env
