#!/usr/bin/env bash

source ./config/variables
source .env

aws iam detach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
aws iam delete-role --role-name $ROLE_NAME
aws sns delete-topic --topic-arn $AWS_SNS_TOPIC_ARN
aws lambda delete-function --function-name $AWS_LAMBDA_ARN

rm .env
