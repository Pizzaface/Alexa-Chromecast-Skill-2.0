#!/bin/bash

set -e -o pipefail

if [ -d "lambda-build" ]; then
  rm -rf lambda-build
fi

if [ -f "lambda-build.zip" ]; then
  rm lambda-build.zip
fi

cd $(dirname $0)

source ./config/variables

if [ -f .env ]; then
  source .env
fi

echo "Descartando política de rol AmazonSNSFullAccess del rol $ROLE_NAME"
aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess || true
echo "Descartando política de rol AmazonLambdaBasicExecutionRole del rol $ROLE_NAME"
aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole || true
echo "Descartando política de rol AmazonS3FullAccess del rol $ROLE_NAME"
aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess || true

echo "Eliminando rol $ROLE_NAME"
aws iam delete-role --role-name "$ROLE_NAME" || true

if [ ! -z "$AWS_SNS_TOPIC_ARN" ]; then
  echo "Eliminando topic $AWS_SNS_TOPIC_ARN"
  aws sns delete-topic --topic-arn "$AWS_SNS_TOPIC_ARN" || true
fi

if [ ! -z "$S3_BUCKET_NAME" ]; then
  echo "Eliminando bucket S3 $S3_BUCKET_NAME"
  aws s3 rb s3://$S3_BUCKET_NAME --force
fi

if [ ! -z "$LAMBDA_FUNCTION_NAME" ]; then
  echo "Eliminando dunción lambda $LAMBDA_FUNCTION_NAME"
  aws lambda delete-function --function-name "$LAMBDA_FUNCTION_NAME" || true
fi

rm -f .env
