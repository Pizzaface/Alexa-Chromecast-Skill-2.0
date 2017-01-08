#!/usr/bin/env bash

source ./config/variables
source .env

aws iam detach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
aws iam delete-role --role-name $ROLE_NAME
aws sns delete-topic --topic-arn $SNS_TOPIC_ARN
aws lambda delete-function --function-name $LAMBDA_FUNCTION_NAME

rm .env
