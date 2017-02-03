#!/usr/bin/env bash -e

source ./config/variables

if [ -f .env ]; then
  source .env
fi

echo "Detaching role policy AmazonSNSFullAccess from role $ROLE_NAME"
aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess || true

echo "Deleting role $ROLE_NAME"
aws iam delete-role --role-name "$ROLE_NAME" || true

if [ ! -z "$AWS_SNS_TOPIC_ARN" ]; then
  echo "Deleting topic $AWS_SNS_TOPIC_ARN"
  aws sns delete-topic --topic-arn "$AWS_SNS_TOPIC_ARN" || true
fi

if [ ! -z "$LAMBDA_FUNCTION_NAME" ]; then
  echo "Deleting lambda function $LAMBDA_FUNCTION_NAME"
  aws lambda delete-function --function-name "$LAMBDA_FUNCTION_NAME" || true
fi

rm -f .env
