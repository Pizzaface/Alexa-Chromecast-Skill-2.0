#!/bin/bash

set -e -o pipefail

cd $(dirname $0)

if [ -z "$(type pip3)" ]; then
  echo "pip3 not found. Installing pip3..."
  curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
  sudo python3 get-pip.py
  rm get-pip.py
  if [ -z "$(type pip3)" ]; then
    echo "pip3 failed to install.. please check and re-run."
    exit 1
  fi
fi

if [ -z "$(type zip)" ]; then
  echo "zip not found. Please install. e.g. sudo apt install zip."
  exit 1
fi

source ./config/aws_variable_names

if [ -z "$(type aws)" ]; then
  echo "aws not found. Installing AWS CLI tools."
  sudo python3 -m pip install 'awscli==1.18.85'
  #curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  #unzip awscliv2.zip
  #sudo ./aws/install
  #rm -rf ./aws
  #rm awscliv2.zip

  if [ -z "$(type aws)" ]; then
    echo "aws failed to install.. please check and re-run."
    exit 1
  else
    echo "Done."
    echo "Running 'aws configure'"
    aws configure
  fi
fi

rm -f .env

AWS_DEFAULT_REGION="$( /usr/bin/awk -F' = ' '$1 == "region" {print $2}' ~/.aws/config )"
# Create Role
echo "Creating $ROLE_NAME role."
role_response=$(aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://config/aws-lambda-role-policy.json)
role_arn=$(echo $role_response | python3 -c "import sys, json; print(json.load(sys.stdin)['Role']['Arn'])")
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole 
aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Create SNS Topic (and store ARN in .env)
echo "Creating $SNS_TOPIC_NAME topic."
sns_response=$(aws sns create-topic --name $SNS_TOPIC_NAME)
sns_topic_arn=$(echo $sns_response | python3 -c "import sys, json; print(json.load(sys.stdin)['TopicArn'])")
echo "export AWS_SNS_TOPIC_ARN=$sns_topic_arn" >> .env

# Create S3 Bucket (and store ARN in .env)
echo "Creating $S3_BUCKET_NAME."
s3_response=$(aws s3api create-bucket --bucket $S3_BUCKET_NAME --region $AWS_DEFAULT_REGION --create-bucket-configuration LocationConstraint=$AWS_DEFAULT_REGION)

# Create Lambda function (and store ARN in .env)
echo "Creating $LAMBDA_FUNCTION_NAME lambda function."
./build-lambda-bundle.sh
lambda_response=$(aws lambda create-function --role $role_arn --function-name $LAMBDA_FUNCTION_NAME --runtime "python3.7" --handler "lambda_function.main.lambda_handler" --role $role_arn --zip-file fileb://lambda-build.zip)
lambda_arn=$(echo $lambda_response | python3 -c "import sys, json; print(json.load(sys.stdin)['FunctionArn'])")
echo "export LAMBDA_FUNCTION_ARN=$lambda_arn" >> .env
aws lambda update-function-configuration --role $role_arn --function-name $LAMBDA_FUNCTION_NAME --environment "Variables={AWS_SNS_ARN=$sns_topic_arn, AWS_S3_BUCKET=$S3_BUCKET_NAME}"
aws lambda add-permission --function-name $LAMBDA_FUNCTION_NAME --statement-id 1 --action lambda:invokeFunction --principal alexa-appkit.amazon.com

echo "Done!"
echo
echo "Next, go to https://developer.amazon.com/edw/home.html#/skills/list and create an Alexa Skill."
echo "Lambda function ARN: $lambda_arn"
echo
echo "Then run the local handler."
echo "SNS Topic ARN: $sns_topic_arn"
