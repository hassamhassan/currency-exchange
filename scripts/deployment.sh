#!/bin/bash

# S3 bucket name and AWS Profile
S3_BUCKET_NAME=exchange-code-bucket
AWS_PROFILE=exchange-rates-profile

# Grant permissions
chmod +x ./scripts/create_layers.sh

# Create the S3 bucket using CloudFormation
echo "----- Executing S3 bucket creating using CloudFormation-----"
aws cloudformation create-stack \
  --profile ${AWS_PROFILE} \
  --stack-name ExchangeStack \
  --template-body file://./YAML/s3_bucket.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for the S3 bucket creation to complete
echo "-----Please wait for S3 bucket creation-----"
aws cloudformation wait stack-create-complete --stack-name ExchangeStack --profile ${AWS_PROFILE}

# Package Lambda functions and layers
echo "-----Zipping lambda code and layers to s3-----"

# Function to zip a layer
create_lambda_layer() {
  local LAYER_NAME=$1
  local REQUIREMENTS_FILE=$2
  local PROFILE=$3

  # Check if requirements.txt exists
  if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "requirements.txt not found!"
    exit 1
  fi

  # Ensure AWS CLI is configured
  if ! aws sts get-caller-identity --profile "$PROFILE" > /dev/null 2>&1; then
    echo "AWS CLI is not configured for profile '$PROFILE'. Please run 'aws configure --profile $PROFILE' first."
    exit 1
  fi

# Installing the requirments in layer
  pip install -r ${REQUIREMENTS_FILE} -t src/dependency_layers/${LAYER_NAME}/python

# Checking into layers folder and zipping the contents
  cd src/dependency_layers/${LAYER_NAME} || exit
  zip -r ${LAYER_NAME}.zip python

# Moving the contents to main dir
  mv ${LAYER_NAME}.zip ../../../

}

# Packaging files
cd src || exit
zip -r ../get_rates_from_url.zip ./get_rates_from_url.py
zip -r ../get_rates_from_db.zip ./get_rates_from_db.py
cd ../


# Create and package requests layer
create_lambda_layer "requests_layer" "requirements-lib_requests.txt" "$AWS_PROFILE"

# Moving to main folder for contents
cd ../../../

ZIP_FILES=("get_rates_from_url.zip" "get_rates_from_db.zip" "requests_layer.zip")

# Upload each file to S3 and delete if successful
for ZIP_FILE in "${ZIP_FILES[@]}"; do
  # Upload to S3
  echo "Uploading $ZIP_FILE to S3 bucket $S3_BUCKET_NAME..."
  aws s3 cp "$ZIP_FILE" s3://${S3_BUCKET_NAME}/ --profile ${AWS_PROFILE}

  # Check if upload was successful
  if [ $? -eq 0 ]; then
    echo "Upload successful for $ZIP_FILE. Deleting local file."
    rm "$ZIP_FILE"
  else
    echo "Upload failed for $ZIP_FILE. File not deleted."
  fi
done

echo "Dependencies created Successfully and uploaded to S3 with profile ${AWS_PROFILE}."


# Function to deploy or update CloudFormation stack
deploy_or_update_stack() {
  STACK_NAME=$1
  TEMPLATE_BODY=$2
  PARAMETERS=$3
  CAPABILITIES=$4
  PROFILE=$5

  echo "-----Checking if the stack '$STACK_NAME' exists-----"
  STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].StackStatus" --output text --profile $PROFILE 2>/dev/null)

  if [ $? -eq 0 ]; then
    echo "-----Stack exists, attempting to update-----"
    aws cloudformation update-stack --stack-name $STACK_NAME \
        --template-body $TEMPLATE_BODY \
        --parameters $PARAMETERS \
        --capabilities $CAPABILITIES \
        --profile $PROFILE

    echo "-----Waiting for the stack update to complete-----"
    aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --profile $PROFILE
  else
    echo "-----Stack does not exist, creating a new stack-----"
    aws cloudformation create-stack --stack-name $STACK_NAME \
        --template-body $TEMPLATE_BODY \
        --parameters $PARAMETERS \
        --capabilities $CAPABILITIES \
        --profile $PROFILE

    echo "-----Waiting for the stack creation to complete-----"
    aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --profile $PROFILE
  fi
}

# Deploy or update the CloudFormation stack
STACK_NAME="ExchangeStack"
TEMPLATE_BODY="file://./YAML/cloud.yaml"
PARAMETERS="ParameterKey=S3BucketNameZipCode,ParameterValue=${S3_BUCKET_NAME}"
CAPABILITIES="CAPABILITY_NAMED_IAM"
PROFILE=${AWS_PROFILE}

deploy_or_update_stack $STACK_NAME $TEMPLATE_BODY $PARAMETERS $CAPABILITIES $PROFILE

# Retrieve the API URL from CloudFormation outputs
echo "-----Deployment complete. You can access the API using the following URL-----"
# Describe the stack to retrieve outputs
echo "-----Retrieving stack outputs for stack: ${STACK_NAME}-----"
STACK_OUTPUT=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs" \
    --output json \
    --profile ${AWS_PROFILE})

# Extract the API Gateway URL from the stack outputs
echo "-----Extracting API Gateway URL from stack outputs-----"
API_URL=$(echo ${STACK_OUTPUT} | jq -r '.[] | select(.OutputKey=="ApiGatewayUrl") | .OutputValue')

# Print the API URL
echo "The API Gateway URL is: ${API_URL}"
