#!/usr/bin/env bash

source ./config/variables

if [ -z "$(type aws)" ]; then
  echo "Installing AWS CLI tools."
  pip install awscli
  if -z "$(type aws)"; then
    echo "aws is not in path.. please check and re-run."
    exit 1
  else
    echo "Done."
  fi
fi

# Create Role
echo "Creating $ROLE_NAME role."
role_response=$(aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://$(pwd)/config/aws-lambda-role-policy.json)
role_arn=$(echo $role_response | python -c "import sys, json; print(json.load(sys.stdin)['Role']['Arn'])")
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess

# Create SNS Topic
echo "Creating $SNS_TOPIC_NAME topic."
sns_response=$(aws sns create-topic --name $SNS_TOPIC_NAME)
sns_topic_arn=$(echo $sns_response | python -c "import sys, json; print(json.load(sys.stdin)['TopicArn'])")

# Create Lambda function
echo "Creating $LAMBDA_FUNCTION_NAME lambda function."
./build-lambda-bundle.sh
lambda_response=$(aws lambda create-function --function-name $LAMBDA_FUNCTION_NAME --runtime "python2.7" --handler "main.lambda_handler" --role $role_arn --zip-file fileb://lambda-build.zip)
lambda_arn=$(echo $lambda_response | python -c "import sys, json; print(json.load(sys.stdin)['FunctionArn'])")
aws lambda update-function-configuration --function-name $LAMBDA_FUNCTION_NAME --environment "Variables={AWS_SNS_ARN=$sns_topic_arn}"
aws lambda add-permission --function-name $LAMBDA_FUNCTION_NAME --statement-id 1 --action lambda:invokeFunction --principal alexa-appkit.amazon.com

echo "Done!"
echo "Next, go to https://developer.amazon.com/edw/home.html#/skills/list and create an Alexa Skill."
echo "Lambda function ARN: $lambda_arn"
echo "Then run the local handler."
echo "SNS Topic ARN: $sns_topic_arn"

echo "LAMBDA_FUNCTION_ARN=$lambda_arn" >> .env
echo "SNS_TOPIC_ARN=$sns_topic_arn" >> .env
